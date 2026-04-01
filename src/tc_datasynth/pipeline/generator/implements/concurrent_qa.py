from __future__ import annotations

"""
并发 QA 生成器：基于结构化 QA 辅助模块，增加异步并发、重试与 attempt 聚合。
"""

import asyncio
from dataclasses import dataclass
import json
from threading import Thread
from typing import Any, Dict, Iterable, Iterator, List, Tuple

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.llm.structured_chain import StructuredChain
from tc_datasynth.core.models import DocumentChunk, QAPair, build_qa_id
from tc_datasynth.pipeline.enhance.mixin import PreflightCheckMixin, PreflightCheckResult
from tc_datasynth.pipeline.generator.base import QAGeneratorBase
from tc_datasynth.pipeline.generator.implements.simple_qa import SimpleQaConfig
from tc_datasynth.pipeline.generator.implements.structured_qa_support import (
    StructuredQaSupport,
)


@dataclass(slots=True)
class ConcurrentQaConfig(SimpleQaConfig):
    """并发生成器配置。"""

    batch_size: int = 4
    max_retries: int = 2
    retry_backoff_ms: int = 500


class ConcurrentQaGenerator(
    QAGeneratorBase[ConcurrentQaConfig],
    PreflightCheckMixin,
):
    """支持异步并发调用与幂等重试的 QA 生成器。"""

    component_name = "concurrent_qa"

    def __init__(self, config: ConcurrentQaConfig | None = None) -> None:
        super().__init__(config=config)
        self.support = StructuredQaSupport()

    @property
    def _chain(self) -> StructuredChain | None:
        """兼容测试中的链路注入。"""
        return self.support._chain

    @_chain.setter
    def _chain(self, value: StructuredChain | None) -> None:
        self.support._chain = value

    @classmethod
    def default_config(cls) -> ConcurrentQaConfig:
        return ConcurrentQaConfig()

    def preflight_check(self) -> PreflightCheckResult:
        """执行轻量生成器预检。"""
        return self.support.run_preflight_check(
            llm_config_path=self.config.llm_config_path,
            llm_model=self.config.llm_model,
            prompt_id=self.config.prompt_id,
            component_name=self.get_component_name(),
        )

    def generate(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
        metas: List[Dict[str, Any]] | None = None,
    ) -> List[QAPair]:
        """同步主接口，内部封装事件循环执行异步并发逻辑。"""
        return self._run_coroutine_sync(self.agenerate(chunks, ctx, metas=metas))

    async def agenerate(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
        metas: List[Dict[str, Any]] | None = None,
    ) -> List[QAPair]:
        """异步并发生成，支持调用级重试与 attempt 落盘。"""
        chunk_list = list(chunks)
        meta_list = self.support.normalize_metas(metas, len(chunk_list))
        per_chunk = max(1, int(self.config.questions_per_chunk))
        qa_limit = ctx.extras.get("generator_qa_limit")
        remaining = (
            int(qa_limit) if isinstance(qa_limit, int) and qa_limit > 0 else None
        )

        jobs: List[Tuple[DocumentChunk, Dict[str, Any], int]] = []
        for chunk, meta in zip(chunk_list, meta_list, strict=True):
            for qa_index in range(1, per_chunk + 1):
                jobs.append((chunk, meta, qa_index))
                if remaining is not None and len(jobs) >= remaining:
                    break
            if remaining is not None and len(jobs) >= remaining:
                break

        chain = self.support.get_chain(
            ctx=ctx,
            prompt_id=self.config.prompt_id,
            llm_model=self.config.llm_model,
            llm_output_structure=self.config.llm_output_structure,
        )
        qa_pairs: List[QAPair] = []
        attempt_rows: List[Dict[str, Any]] = []
        for window in self._chunk_jobs(jobs, max(1, int(self.config.batch_size))):
            tasks = [
                self._run_job(chunk, meta, qa_index, ctx, chain)
                for chunk, meta, qa_index in window
            ]
            results = await asyncio.gather(*tasks)
            for qa, attempts in results:
                qa_pairs.append(qa)
                attempt_rows.extend(attempts)
                self.notify_progress(ctx)
        self._write_attempt_rows(ctx, attempt_rows)
        return qa_pairs

    async def _run_job(
        self,
        chunk: DocumentChunk,
        meta: Dict[str, Any],
        qa_index: int,
        ctx: RunContext,
        chain: Any,
    ) -> Tuple[QAPair, List[Dict[str, Any]]]:
        """执行单个 QA 任务槽位，带重试。"""
        qa_id = build_qa_id(ctx.run_id, chunk.source_doc_id, chunk.chunk_id, qa_index)
        payload = self.support.build_payload(
            chain=chain,
            chunk=chunk,
            meta=meta,
        )
        attempts: List[Dict[str, Any]] = []
        last_result: Dict[str, Any] = {}
        last_error: str | None = None

        for attempt in range(1, self.config.max_retries + 2):
            try:
                result = await chain.arun(payload)
                last_result = result or {}
                failure_reason = self._get_retryable_failure(last_result)
                if failure_reason is None:
                    attempts.append(
                        self._make_attempt_row(
                            qa_id=qa_id,
                            chunk=chunk,
                            qa_index=qa_index,
                            attempt=attempt,
                            status="success",
                            error=None,
                        )
                    )
                    return (
                        self.support.build_qa(
                            chunk=chunk,
                            result=last_result,
                            ctx=ctx,
                            meta=meta,
                            qa_index=qa_index,
                            generator_name="concurrent_qa",
                            llm_model=self.config.llm_model,
                            prompt_id=self.config.prompt_id,
                        ),
                        attempts,
                    )
                last_error = failure_reason
                attempts.append(
                    self._make_attempt_row(
                        qa_id=qa_id,
                        chunk=chunk,
                        qa_index=qa_index,
                        attempt=attempt,
                        status="invalid_output",
                        error=failure_reason,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                last_error = f"{type(exc).__name__}: {exc}"
                attempts.append(
                    self._make_attempt_row(
                        qa_id=qa_id,
                        chunk=chunk,
                        qa_index=qa_index,
                        attempt=attempt,
                        status="exception",
                        error=last_error,
                    )
                )

            if attempt <= self.config.max_retries:
                await asyncio.sleep(max(0, self.config.retry_backoff_ms) / 1000)

        fallback_result = dict(last_result)
        fallback_error = last_error or "retry_exhausted"
        fallback_result["error"] = fallback_error
        attempts.append(
            self._make_attempt_row(
                qa_id=qa_id,
                chunk=chunk,
                qa_index=qa_index,
                attempt=self.config.max_retries + 2,
                status="fallback",
                error=fallback_error,
            )
        )
        return (
            self.support.build_qa(
                chunk=chunk,
                result=fallback_result,
                ctx=ctx,
                meta=meta,
                qa_index=qa_index,
                generator_name="concurrent_qa",
                llm_model=self.config.llm_model,
                prompt_id=self.config.prompt_id,
            ),
            attempts,
        )

    @staticmethod
    def _chunk_jobs(
        jobs: List[Tuple[DocumentChunk, Dict[str, Any], int]],
        batch_size: int,
    ) -> Iterator[List[Tuple[DocumentChunk, Dict[str, Any], int]]]:
        """按批大小切分任务窗口。"""
        for start in range(0, len(jobs), batch_size):
            yield jobs[start : start + batch_size]

    @staticmethod
    def _get_retryable_failure(result: Dict[str, Any]) -> str | None:
        """判断当前结构化结果是否需要重试。"""
        if not result:
            return "empty_result"
        if result.get("error"):
            return str(result["error"])
        parsed = result.get("parse")
        if not isinstance(parsed, dict):
            return "missing_parse"
        if not str(parsed.get("question") or "").strip():
            return "missing_question"
        if not str(parsed.get("answer") or "").strip():
            return "missing_answer"
        return None

    @staticmethod
    def _make_attempt_row(
        *,
        qa_id: str,
        chunk: DocumentChunk,
        qa_index: int,
        attempt: int,
        status: str,
        error: str | None,
    ) -> Dict[str, Any]:
        """构造一次调用尝试的记录。"""
        return {
            "qa_id": qa_id,
            "source_doc_id": chunk.source_doc_id,
            "chunk_id": chunk.chunk_id,
            "qa_index": qa_index,
            "attempt": attempt,
            "status": status,
            "error": error,
        }

    def _write_attempt_rows(
        self,
        ctx: RunContext,
        rows: List[Dict[str, Any]],
    ) -> None:
        """将本轮 attempt 记录追加写入中间产物。"""
        if not rows:
            return
        output_dir = ctx.workdir_for(subdir="generator")
        output_path = output_dir / "attempts.jsonl"
        with output_path.open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        ctx.extras["generator_attempts_path"] = str(output_path)
        ctx.extras["generator_attempts_count"] = int(
            ctx.extras.get("generator_attempts_count", 0)
        ) + len(rows)

    @staticmethod
    def _run_coroutine_sync(coro: Any) -> Any:
        """同步环境中运行协程；若当前线程已有事件循环，则切到新线程。"""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)

        result: Dict[str, Any] = {}
        error: Dict[str, BaseException] = {}

        def _target() -> None:
            try:
                result["value"] = asyncio.run(coro)
            except BaseException as exc:  # noqa: BLE001
                error["value"] = exc

        thread = Thread(target=_target, daemon=True)
        thread.start()
        thread.join()
        if "value" in error:
            raise error["value"]
        return result.get("value")
