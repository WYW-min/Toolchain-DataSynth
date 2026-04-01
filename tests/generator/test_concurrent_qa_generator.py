from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import tc_datasynth.core.llm.llm_factory as llm_factory_module
from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk
from tc_datasynth.pipeline.enhance.mixin import PreflightStage
from tc_datasynth.pipeline.generator.implements.concurrent_qa import (
    ConcurrentQaConfig,
    ConcurrentQaGenerator,
)


class _RetryOnceAsyncChain:
    """第一次返回无效结果，第二次返回成功结果。"""

    required_inputs = {"text", "meta"}

    def __init__(self) -> None:
        self.calls = 0

    async def arun(self, _: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        await asyncio.sleep(0)
        if self.calls == 1:
            return {
                "parse": {"question": "", "answer": "", "evidences": []},
                "error": None,
                "raw_text": "{}",
            }
        return {
            "parse": {
                "question": "Q?",
                "answer": "A.",
                "evidences": ["E1"],
                "proposition_thought": "P",
                "solution_thought": "S",
            },
            "error": None,
            "raw_text": "{}",
        }


class _AlwaysSuccessAsyncChain:
    """始终成功的异步假链路，可记录并发情况。"""

    required_inputs = {"text", "meta"}

    def __init__(self, delay: float = 0.0) -> None:
        self.delay = delay
        self.calls = 0
        self.in_flight = 0
        self.max_in_flight = 0

    async def arun(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            if self.delay > 0:
                await asyncio.sleep(self.delay)
            return {
                "parse": {
                    "question": f"Q:{payload.get('text', '')[:8]}?",
                    "answer": "A.",
                    "evidences": ["E1"],
                },
                "error": None,
                "raw_text": "{}",
            }
        finally:
            self.in_flight -= 1


class _AlwaysInvalidAsyncChain:
    """始终返回无效结构化结果。"""

    required_inputs = {"text", "meta"}

    def __init__(self) -> None:
        self.calls = 0

    async def arun(self, _: Dict[str, Any]) -> Dict[str, Any]:
        self.calls += 1
        await asyncio.sleep(0)
        return {
            "parse": {"question": "", "answer": "", "evidences": []},
            "error": None,
            "raw_text": "{}",
        }


class _RetryByTextAsyncChain:
    """指定文本首轮失败，其余情况成功。"""

    required_inputs = {"text", "meta"}

    def __init__(self, retry_texts: set[str]) -> None:
        self.retry_texts = retry_texts
        self.calls_by_text: Counter[str] = Counter()

    async def arun(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = str(payload.get("text") or "")
        self.calls_by_text[text] += 1
        await asyncio.sleep(0)
        if text in self.retry_texts and self.calls_by_text[text] == 1:
            return {
                "parse": {"question": "", "answer": "", "evidences": []},
                "error": None,
                "raw_text": "{}",
            }
        return {
            "parse": {
                "question": f"Q:{text[:8]}?",
                "answer": "A.",
                "evidences": ["E1"],
            },
            "error": None,
            "raw_text": "{}",
        }


class ConcurrentQaGeneratorTest(unittest.TestCase):
    """并发生成器测试。"""

    def setUp(self) -> None:
        llm_factory_module.llm_manager = None
        llm_factory_module.LlmFactory._instance = None

    def tearDown(self) -> None:
        llm_factory_module.llm_manager = None
        llm_factory_module.LlmFactory._instance = None

    def test_generate_retries_and_writes_attempts(self) -> None:
        """失败后应重试，并将 attempt 轨迹落盘。"""
        chunk = DocumentChunk(
            chunk_id="doc1__chunk-0",
            content="sample content",
            source_doc_id="doc1",
            section="intro",
            metadata={"line_start": 1, "line_end": 3},
        )
        config = ConcurrentQaConfig(
            prompt_id="simple_qa",
            batch_size=2,
            max_retries=1,
            retry_backoff_ms=0,
        )
        generator = ConcurrentQaGenerator(config=config)
        generator._chain = _RetryOnceAsyncChain()  # type: ignore[assignment]

        ctx = _make_context()
        metas = [
            {
                "system_meta": {"planner": "simple", "plan_index": 7},
                "prompt_meta": {"difficulty": "easy", "question_type": "definition"},
            }
        ]

        qas = generator.generate([chunk], ctx, metas=metas)

        self.assertEqual(len(qas), 1)
        self.assertEqual(qas[0].qa_info.question, "Q?")
        self.assertEqual(qas[0].qa_info.labels["difficulty"], "easy")
        self.assertEqual(qas[0].provenance.plan_index, 7)
        self.assertEqual(qas[0].qa_id, f"{ctx.run_id}__doc-doc1__chunk-0__qa-1")

        attempts_path = Path(str(ctx.extras["generator_attempts_path"]))
        self.assertTrue(attempts_path.exists())
        rows = [
            json.loads(line)
            for line in attempts_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["status"], "invalid_output")
        self.assertEqual(rows[1]["status"], "success")
        self.assertTrue(all(row["qa_id"] == qas[0].qa_id for row in rows))

    def test_generate_respects_batch_window_size(self) -> None:
        """窗口式执行时，同时在飞的任务数不应超过 batch_size。"""
        chunks = [
            DocumentChunk(
                chunk_id=f"doc1__chunk-{index}",
                content=f"sample content {index}",
                source_doc_id="doc1",
                metadata={"line_start": index + 1, "line_end": index + 1},
            )
            for index in range(5)
        ]
        chain = _AlwaysSuccessAsyncChain(delay=0.01)
        generator = ConcurrentQaGenerator(
            config=ConcurrentQaConfig(
                prompt_id="simple_qa",
                batch_size=2,
                max_retries=0,
                retry_backoff_ms=0,
            )
        )
        generator._chain = chain  # type: ignore[assignment]
        ctx = _make_context()

        qas = generator.generate(chunks, ctx, metas=_make_metas(len(chunks)))

        self.assertEqual(len(qas), 5)
        self.assertEqual(chain.calls, 5)
        self.assertLessEqual(chain.max_in_flight, 2)
        self.assertEqual(chain.max_in_flight, 2)

    def test_generate_retry_exhaustion_returns_fallback_qa(self) -> None:
        """重试耗尽后仍应聚合为一条 fallback QA，并完整记录 attempts。"""
        chunk = DocumentChunk(
            chunk_id="doc1__chunk-0",
            content="fallback source content",
            source_doc_id="doc1",
            metadata={"line_start": 2, "line_end": 4},
        )
        generator = ConcurrentQaGenerator(
            config=ConcurrentQaConfig(
                prompt_id="simple_qa",
                batch_size=1,
                max_retries=1,
                retry_backoff_ms=0,
            )
        )
        generator._chain = _AlwaysInvalidAsyncChain()  # type: ignore[assignment]
        ctx = _make_context()

        qas = generator.generate([chunk], ctx, metas=_make_metas(1))

        self.assertEqual(len(qas), 1)
        self.assertEqual(qas[0].qa_info.question, "请基于文本回答问题。")
        self.assertEqual(qas[0].qa_info.answer, "参考原文内容作答。")
        self.assertEqual(
            qas[0].provenance.extra,
            {"error": "missing_question"},
        )

        rows = _read_attempt_rows(ctx)
        self.assertEqual([row["status"] for row in rows], ["invalid_output", "invalid_output", "fallback"])
        self.assertEqual([row["attempt"] for row in rows], [1, 2, 3])
        self.assertTrue(all(row["qa_id"] == qas[0].qa_id for row in rows))

    def test_preflight_check_validates_current_model_only(self) -> None:
        """并发生成器预检应复用单模型检查逻辑。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            env_path = base / "llm.env"
            env_path.write_text(
                "TEST_BASE_URL=https://unit.example.com\nTEST_API_KEY=test-key\n",
                encoding="utf-8",
            )
            llm_config_path = base / "llm.toml"
            llm_config_path.write_text(
                """
[settings]
env_path = "llm.env"

[models.demo_model]
model = "dummy"
model_provider = "openai"
base_url_env = "TEST_BASE_URL"
api_key_env = "TEST_API_KEY"
""".strip(),
                encoding="utf-8",
            )

            class _FakeModel:
                def stream(self, _: str):
                    yield "1"

            generator = ConcurrentQaGenerator(
                config=ConcurrentQaConfig(
                    prompt_id="simple_qa",
                    llm_model="demo-model",
                    llm_config_path=llm_config_path,
                )
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=_FakeModel()
            ) as mock_init:
                result = generator.preflight_check()

            self.assertTrue(result.ok)
            self.assertEqual(result.stage, PreflightStage.PING)
            self.assertEqual(result.component_name, "concurrent_qa")
            self.assertEqual(result.details["llm_model"], "demo-model")
            self.assertEqual(mock_init.call_count, 1)

    def test_generate_respects_qa_limit_on_job_expansion(self) -> None:
        """qa_limit 应在任务展开阶段生效，而不是生成后再裁剪。"""
        chunks = [
            DocumentChunk(
                chunk_id=f"doc1__chunk-{index}",
                content=f"content-{index}",
                source_doc_id="doc1",
                metadata={"line_start": index + 1, "line_end": index + 1},
            )
            for index in range(2)
        ]
        chain = _AlwaysSuccessAsyncChain()
        generator = ConcurrentQaGenerator(
            config=ConcurrentQaConfig(
                prompt_id="simple_qa",
                questions_per_chunk=2,
                batch_size=2,
                max_retries=0,
                retry_backoff_ms=0,
            )
        )
        generator._chain = chain  # type: ignore[assignment]
        ctx = _make_context()
        ctx.extras["generator_qa_limit"] = 2

        qas = generator.generate(chunks, ctx, metas=_make_metas(len(chunks)))

        self.assertEqual(len(qas), 2)
        self.assertEqual(chain.calls, 2)
        self.assertEqual(
            [qa.qa_id for qa in qas],
            [
                f"{ctx.run_id}__doc-doc1__chunk-0__qa-1",
                f"{ctx.run_id}__doc-doc1__chunk-0__qa-2",
            ],
        )
        rows = _read_attempt_rows(ctx)
        self.assertEqual(len(rows), 2)

    def test_generate_builds_stable_qa_ids_for_multi_chunk_slots(self) -> None:
        """多 chunk、多 QA 槽位时应按稳定顺序生成 qa_id。"""
        chunks = [
            DocumentChunk(
                chunk_id=f"doc1__chunk-{index}",
                content=f"slot content {index}",
                source_doc_id="doc1",
                metadata={"line_start": index + 10, "line_end": index + 10},
            )
            for index in range(2)
        ]
        generator = ConcurrentQaGenerator(
            config=ConcurrentQaConfig(
                prompt_id="simple_qa",
                questions_per_chunk=2,
                batch_size=2,
                max_retries=0,
                retry_backoff_ms=0,
            )
        )
        generator._chain = _AlwaysSuccessAsyncChain()  # type: ignore[assignment]
        ctx = _make_context()

        qas = generator.generate(chunks, ctx, metas=_make_metas(len(chunks)))

        self.assertEqual(
            [qa.qa_id for qa in qas],
            [
                f"{ctx.run_id}__doc-doc1__chunk-0__qa-1",
                f"{ctx.run_id}__doc-doc1__chunk-0__qa-2",
                f"{ctx.run_id}__doc-doc1__chunk-1__qa-1",
                f"{ctx.run_id}__doc-doc1__chunk-1__qa-2",
            ],
        )

    def test_generate_aggregates_attempt_rows_across_jobs(self) -> None:
        """attempts.jsonl 应汇总全部 job 的重试轨迹，而不是只保留最终成功结果。"""
        chunks = [
            DocumentChunk(
                chunk_id="doc1__chunk-0",
                content="retry-me",
                source_doc_id="doc1",
                metadata={"line_start": 1, "line_end": 2},
            ),
            DocumentChunk(
                chunk_id="doc1__chunk-1",
                content="success-me",
                source_doc_id="doc1",
                metadata={"line_start": 3, "line_end": 4},
            ),
        ]
        generator = ConcurrentQaGenerator(
            config=ConcurrentQaConfig(
                prompt_id="simple_qa",
                batch_size=2,
                max_retries=1,
                retry_backoff_ms=0,
            )
        )
        generator._chain = _RetryByTextAsyncChain({"retry-me"})  # type: ignore[assignment]
        ctx = _make_context()

        qas = generator.generate(chunks, ctx, metas=_make_metas(len(chunks)))

        self.assertEqual(len(qas), 2)
        rows = _read_attempt_rows(ctx)
        self.assertEqual(len(rows), 3)
        counts = Counter(row["qa_id"] for row in rows)
        self.assertEqual(sorted(counts.values()), [1, 2])
        self.assertEqual(sum(1 for row in rows if row["status"] == "success"), 2)


def _make_context() -> RunContext:
    """构造最小 RunContext。"""
    base_dir = Path(tempfile.mkdtemp())
    input_dir = base_dir / "in"
    output_dir = base_dir / "out"
    temp_root = base_dir / "temp"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = RuntimeConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        mode="mock",
        doc_limit=1,
        log_level="INFO",
        temp_root_base=temp_root,
    )
    config.ensure_output_dir()
    return RunContext.from_config(config=config)


def _make_metas(total: int) -> list[dict[str, Any]]:
    """构造统一的 planner metas。"""
    return [
        {
            "system_meta": {"planner": "simple", "plan_index": index + 1},
            "prompt_meta": {
                "difficulty": "easy",
                "question_type": "definition",
            },
        }
        for index in range(total)
    ]


def _read_attempt_rows(ctx: RunContext) -> list[dict[str, Any]]:
    """读取 generator attempts 中间产物。"""
    attempts_path = Path(str(ctx.extras["generator_attempts_path"]))
    return [
        json.loads(line)
        for line in attempts_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
