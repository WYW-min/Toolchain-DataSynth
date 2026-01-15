from __future__ import annotations

"""
最小切片实现：按章节生成 chunk。
"""

from dataclasses import dataclass
from typing import List

from tc_datasynth.core.models import DocumentChunk, IntermediateRepresentation
from tc_datasynth.pipeline.sampler.base import SamplerBase, SamplerConfigBase


@dataclass(slots=True)
class SamplingConfig(SamplerConfigBase):
    """切分配置，预留后续策略参数。"""

    chunk_size: int = 400


class SimpleChunkSampler(SamplerBase[SamplingConfig]):
    """基于 IR 生成可供生成器消费的文档片段。"""

    def __init__(self, config: SamplingConfig | None = None) -> None:
        """初始化采样器，可传入切分配置。"""
        super().__init__(config)

    @classmethod
    def default_config(cls) -> SamplingConfig:
        """返回默认配置。"""
        return SamplingConfig()

    def sample(self, ir: IntermediateRepresentation) -> List[DocumentChunk]:
        """根据章节创建 chunk，mock 阶段一节一片。"""
        chunks: List[DocumentChunk] = []
        for idx, section in enumerate(ir.sections or ["full_document"]):
            chunk_id = f"{ir.doc_id}-chunk-{idx+1}"
            content = f"{section}\n{ir.text}"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    content=content,
                    source_doc_id=ir.doc_id,
                    section=section,
                    metadata={"strategy": "section_mock"},
                )
            )
        if not chunks:
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{ir.doc_id}-chunk-1",
                    content=ir.text,
                    source_doc_id=ir.doc_id,
                    section=None,
                    metadata={"strategy": "fallback_single_chunk"},
                )
            )
        return chunks
