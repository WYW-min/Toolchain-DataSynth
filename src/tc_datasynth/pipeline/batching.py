from __future__ import annotations

"""
批处理逻辑：批次切分、解析与生成阶段的执行。
"""

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import (
    DocumentChunk,
    IntermediateRepresentation,
    QAPair,
    SourceDocument,
)
from tc_datasynth.pipeline.components import PipelineComponents
from tc_datasynth.pipeline.progress import ProgressTracker

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
        return parsed

    def generate_from_parsed(
        self,
        parsed_items: List[Tuple[SourceDocument, IntermediateRepresentation]],
        final_records: List[QAPair],
        failed_records: List[dict],
        progress: Optional[ProgressTracker] = None,
    ) -> int:
        """基于解析结果执行采样、生成与校验。"""
        if not parsed_items:
            return 0
        self.logger.debug(f"生成批次: {len(parsed_items)}")
        chunk_batches: List[List[DocumentChunk]] = []
        for document, ir in parsed_items:
            self.logger.debug(f"采样文档: {document.path}")
            chunk_batches.append(self.components.sampler.sample(ir, self.ctx))
        qa_batches = self.components.generator.generate_batch(chunk_batches, self.ctx)
        if len(qa_batches) != len(parsed_items):
            self.logger.warning(
                f"生成批次返回数量不一致: expected={len(parsed_items)}, actual={len(qa_batches)}"
            )
        paired_batches = list(zip(parsed_items, qa_batches))
        for (document, _), qa_pairs in paired_batches:
            self.logger.debug(f"生成完成: {document.path}")
            for qa in qa_pairs:
                validation = self.components.validator.validate(qa)
                if validation.is_valid:
                    final_records.append(qa)
                else:
                    failed_records.append(
                        {"qa": qa.to_jsonable(), "errors": validation.errors}
                    )
            if progress:
                progress.update_generate(1)
        return len(paired_batches)
