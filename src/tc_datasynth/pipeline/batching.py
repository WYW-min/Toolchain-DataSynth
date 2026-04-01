from __future__ import annotations

"""
批处理逻辑：批次切分、解析与生成阶段的执行。
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import (
    DocumentChunk,
    IntermediateRepresentation,
    QAPair,
    SourceDocument,
)
from tc_datasynth.pipeline.components import PipelineComponents
from tc_datasynth.pipeline.progress import ProgressTracker
from tc_datasynth.reporting import register_stage_manifest_entry

TItem = TypeVar("TItem")


def normalize_batch_size(batch_size: Optional[int]) -> Optional[int]:
    """规范化批处理大小，None/0/负数表示全量。"""
    if batch_size is None:
        return None
    if batch_size <= 0:
        return None
    return batch_size


def format_batch_size(batch_size: Optional[int]) -> str:
    """用于日志输出的批处理数量描述。"""
    return "all" if batch_size is None else str(batch_size)


def batch_items(items: List[TItem], batch_size: Optional[int]) -> Iterable[List[TItem]]:
    """按批大小切分列表，batch_size=None 表示全量。"""
    if batch_size is None or batch_size <= 0:
        yield items
        return
    batch: List[TItem] = []
    for item in items:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


@dataclass(slots=True)
class BatchExecutor:
    """批处理执行器，封装解析与生成阶段逻辑。"""

    components: PipelineComponents
    ctx: RunContext
    logger: Any

    def parse_documents(
        self,
        documents: List[SourceDocument],
        progress: Optional[ProgressTracker] = None,
    ) -> List[Tuple[SourceDocument, IntermediateRepresentation]]:
        """解析一批文档并返回 IR 列表。"""
        if not documents:
            return []
        self.logger.debug(f"解析批次: {len(documents)}")
        irs = self.components.parser.parse_batch(documents, self.ctx)
        if len(irs) != len(documents):
            self.logger.warning(
                f"解析批次返回数量不一致: expected={len(documents)}, actual={len(irs)}"
            )
        parsed = list(zip(documents, irs))
        for document, _ in parsed:
            self.logger.debug(f"解析完成: {document.path}")
            if progress:
                progress.update_parse(1)
        for document, ir in parsed:
            text_path = ir.metadata.get("text_path")
            register_stage_manifest_entry(
                self.ctx,
                "parser",
                {
                    "doc_id": document.doc_id,
                    "parsed_doc_id": ir.doc_id,
                    "source_doc_name": ir.metadata.get("source_doc_name"),
                    "source_file_name": ir.metadata.get("source_file_name"),
                    "artifact_path": text_path,
                    "attempts_path": ir.metadata.get("attempts_path"),
                    "attempt_count": ir.metadata.get("attempt_count"),
                    "parse_task_id": ir.metadata.get("parse_task_id"),
                    "exists": bool(text_path) and Path(str(text_path)).exists(),
                    "schema": "IntermediateRepresentation",
                    "retention": "temporary",
                    "adapter": ir.metadata.get("adapter"),
                },
            )
        return parsed

    def generate_from_parsed(
        self,
        parsed_items: List[Tuple[SourceDocument, IntermediateRepresentation]],
        final_records: List[QAPair],
        failed_records: List[dict],
        progress: Optional[ProgressTracker] = None,
        qa_limit: Optional[int] = None,
    ) -> Tuple[int, bool]:
        """基于解析结果执行采样、生成与校验。"""
        if not parsed_items:
            return 0, False
        self.logger.debug(f"生成批次: {len(parsed_items)}")
        processed_docs = 0
        for document, ir in parsed_items:
            current_qa_total = len(final_records) + len(failed_records)
            if qa_limit is not None and current_qa_total >= qa_limit:
                return processed_docs, True
            self.logger.debug(f"采样文档: {document.path}")
            sampler_line_count = int(self.ctx.extras.get("sampler_line_count", 0))
            chunks = list(self.components.sampler.sample(ir, self.ctx))
            sampler_output = self.ctx.extras.get("sampler_output_path")
            sampler_human_readable_dir = self.ctx.extras.get("sampler_human_readable_dir")
            register_stage_manifest_entry(
                self.ctx,
                "sampler",
                {
                    "doc_id": document.doc_id,
                    "parsed_doc_id": ir.doc_id,
                    "artifact_path": sampler_output,
                    "human_readable_dir": sampler_human_readable_dir,
                    "exists": bool(sampler_output) and Path(str(sampler_output)).exists(),
                    "record_count": len(chunks),
                    "line_start": sampler_line_count + 1 if chunks else None,
                    "line_end": sampler_line_count + len(chunks) if chunks else None,
                    "schema": "DocumentChunk",
                    "retention": "temporary",
                },
            )
            self.ctx.extras["sampler_line_count"] = sampler_line_count + len(chunks)
            metas = self.components.planner.plan(chunks, self.ctx)
            planner_line_count = int(self.ctx.extras.get("planner_line_count", 0))
            planner_output = _write_planner_records(
                self.ctx,
                ir,
                chunks,
                metas,
            )
            eligible_pairs = [
                (chunk, meta)
                for chunk, meta in zip(chunks, metas, strict=True)
                if bool(meta.get("system_meta", {}).get("should_generate", True))
            ]
            planned_chunks = [chunk for chunk, _ in eligible_pairs]
            planned_metas = [meta for _, meta in eligible_pairs]
            register_stage_manifest_entry(
                self.ctx,
                "planner",
                {
                    "doc_id": document.doc_id,
                    "parsed_doc_id": ir.doc_id,
                    "artifact_path": planner_output,
                    "exists": bool(planner_output) and Path(str(planner_output)).exists(),
                    "record_count": len(metas),
                    "eligible_count": len(planned_metas),
                    "skipped_count": len(metas) - len(planned_metas),
                    "line_start": planner_line_count + 1 if metas else None,
                    "line_end": planner_line_count + len(metas) if metas else None,
                    "difficulty_distribution": _count_meta_field(metas, "difficulty"),
                    "question_type_distribution": _count_meta_field(
                        metas, "question_type"
                    ),
                    "retention": "result",
                },
            )
            self.ctx.extras["planner_line_count"] = planner_line_count + len(metas)
            remaining_limit = None
            if qa_limit is not None:
                remaining_limit = qa_limit - (len(final_records) + len(failed_records))
                if remaining_limit <= 0:
                    return processed_docs, True
                chunk_budget = _estimate_chunk_budget(
                    self.components.generator,
                    remaining_limit,
                )
                if chunk_budget is not None:
                    planned_chunks = planned_chunks[:chunk_budget]
                    planned_metas = planned_metas[:chunk_budget]
                self.ctx.extras["generator_qa_limit"] = remaining_limit
            else:
                self.ctx.extras.pop("generator_qa_limit", None)

            if progress:
                planned_task_count = _estimate_generation_task_count(
                    self.components.generator,
                    planned_chunks,
                    remaining_limit,
                )
                progress.add_generate_total(planned_task_count)
                self.ctx.extras["generator_progress_callback"] = progress.update_generate
            else:
                self.ctx.extras.pop("generator_progress_callback", None)

            attempts_before = int(self.ctx.extras.get("generator_attempts_count", 0))
            try:
                qa_pairs = self.components.generator.generate(
                    planned_chunks,
                    self.ctx,
                    metas=planned_metas,
                )
            finally:
                self.ctx.extras.pop("generator_qa_limit", None)
                self.ctx.extras.pop("generator_progress_callback", None)
            self.logger.debug(f"生成完成: {document.path}")
            attempts_after = int(self.ctx.extras.get("generator_attempts_count", 0))
            register_stage_manifest_entry(
                self.ctx,
                "generator",
                {
                    "doc_id": document.doc_id,
                    "parsed_doc_id": ir.doc_id,
                    "qa_count": len(qa_pairs),
                    "artifact_path": self.ctx.extras.get("generator_attempts_path"),
                    "attempt_count": max(0, attempts_after - attempts_before),
                    "backend": str(
                        self.ctx.config.components.get("generator", {}).get(
                            "name", "mock"
                        )
                    ),
                    "retention": "result",
                },
            )
            accepted = 0
            rejected = 0
            error_counts: Dict[str, int] = {}
            limit_reached = False
            for qa in qa_pairs:
                validation = self.components.gate.evaluate(qa)
                if validation.is_valid:
                    if qa_limit is not None and (len(final_records) + len(failed_records)) >= qa_limit:
                        limit_reached = True
                        break
                    final_records.append(qa)
                    accepted += 1
                    if qa_limit is not None and (len(final_records) + len(failed_records)) >= qa_limit:
                        limit_reached = True
                        break
                else:
                    if qa_limit is not None and (len(final_records) + len(failed_records)) >= qa_limit:
                        limit_reached = True
                        break
                    rejected += 1
                    for error in validation.errors:
                        error_counts[error] = error_counts.get(error, 0) + 1
                    failed_records.append(
                        {
                            "qa_id": qa.qa_id,
                            "action": validation.action,
                            "stage": validation.stage,
                            "errors": validation.errors,
                            "qa": qa.model_dump(mode="json", exclude_none=True),
                        }
                    )
                    if qa_limit is not None and (len(final_records) + len(failed_records)) >= qa_limit:
                        limit_reached = True
                        break
            register_stage_manifest_entry(
                self.ctx,
                "gate",
                {
                    "doc_id": document.doc_id,
                    "parsed_doc_id": ir.doc_id,
                    "accepted_count": accepted,
                    "rejected_count": rejected,
                    "error_distribution": error_counts,
                    "retention": "result",
                },
            )
            processed_docs += 1
            if limit_reached:
                return processed_docs, True
        return processed_docs, False


def _estimate_chunk_budget(generator: Any, remaining_limit: int) -> int | None:
    """根据生成器配置估算本轮最多需要消费多少 chunk。"""
    if remaining_limit <= 0:
        return 0
    questions_per_chunk = getattr(generator.config, "questions_per_chunk", None)
    if isinstance(questions_per_chunk, int) and questions_per_chunk > 0:
        return max(1, math.ceil(remaining_limit / questions_per_chunk))
    return remaining_limit


def _estimate_generation_task_count(
    generator: Any,
    chunks: List[DocumentChunk],
    remaining_limit: int | None,
) -> int:
    """估算本轮生成任务数，用于动态进度展示。"""
    if not chunks:
        return 0
    if remaining_limit is not None and remaining_limit <= 0:
        return 0

    questions_per_chunk = getattr(generator.config, "questions_per_chunk", None)
    if isinstance(questions_per_chunk, int) and questions_per_chunk > 0:
        count = len(chunks) * questions_per_chunk
    else:
        questions_per_doc = getattr(generator.config, "questions_per_doc", None)
        if isinstance(questions_per_doc, int) and questions_per_doc > 0:
            per_chunk = max(1, questions_per_doc // max(1, len(chunks)))
            count = len(chunks) * per_chunk
        else:
            count = len(chunks)
    if remaining_limit is not None:
        return min(count, remaining_limit)
    return count


def _count_meta_field(metas: List[Dict[str, Any]], field_name: str) -> Dict[str, int]:
    """统计规划 meta 中某个字段的分布。"""
    counts: Dict[str, int] = {}
    for meta in metas:
        prompt_meta = meta.get("prompt_meta", {})
        value = prompt_meta.get(field_name) if isinstance(prompt_meta, dict) else None
        if not value:
            continue
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    return counts


def _write_planner_records(
    ctx: RunContext,
    ir: IntermediateRepresentation,
    chunks: List[DocumentChunk],
    metas: List[Dict[str, Any]],
) -> Path:
    """将 planner 中间体追加落盘到运行级 JSONL。"""
    output_dir = ctx.workdir_for(subdir="planner")
    output_path = output_dir / "plans.jsonl"
    with output_path.open("a", encoding="utf-8") as f:
        for chunk, meta in zip(chunks, metas, strict=True):
            payload = {
                "chunk_id": chunk.chunk_id,
                "source_doc_id": chunk.source_doc_id,
                "parsed_doc_id": ir.doc_id,
                "section": chunk.section,
                "content_length": len(chunk.content or ""),
                "system_meta": meta.get("system_meta", {}),
                "prompt_meta": meta.get("prompt_meta", {}),
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    ctx.extras["planner_output_path"] = str(output_path)
    return output_path
