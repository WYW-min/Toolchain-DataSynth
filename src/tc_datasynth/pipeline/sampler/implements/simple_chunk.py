from __future__ import annotations

"""
最小切片实现：按字符长度切分，并用省略标识提示上下文被截断。
"""

from dataclasses import dataclass
from typing import List

from tc_datasynth.core.models import DocumentChunk, IntermediateRepresentation
from tc_datasynth.pipeline.sampler.base import SamplerBase, SamplerConfigBase


ELLIPSIS = "..."


@dataclass(slots=True)
class SamplingConfig(SamplerConfigBase):
    """切分配置，预留后续策略参数。"""

    chunk_size: int = 400


class SimpleChunkSampler(SamplerBase[SamplingConfig]):
    """基于字符长度切分文档片段。"""

    component_name = "simple_chunk"

    @classmethod
    def default_config(cls) -> SamplingConfig:
        """返回默认配置。"""
        return SamplingConfig()

    def _content_budget(self, has_prefix_gap: bool, has_suffix_gap: bool) -> int:
        """计算当前 chunk 可承载的原始文本长度。"""
        budget = self.config.chunk_size
        if has_prefix_gap:
            budget -= len(ELLIPSIS)
        if has_suffix_gap:
            budget -= len(ELLIPSIS)
        return budget

    def _make_chunk(
        self,
        ir: IntermediateRepresentation,
        index: int,
        raw_content: str,
        start: int,
        end: int,
        has_prefix_gap: bool,
        has_suffix_gap: bool,
    ) -> DocumentChunk:
        """构造带截断标识的 chunk。"""
        content = raw_content
        if has_prefix_gap:
            content = f"{ELLIPSIS}{content}"
        if has_suffix_gap:
            content = f"{content}{ELLIPSIS}"
        metadata = {
            **self._build_source_metadata(ir),
            "strategy": "char_truncate",
            "char_start": start,
            "char_end": end,
            "truncated_prefix": has_prefix_gap,
            "truncated_suffix": has_suffix_gap,
        }
        return DocumentChunk(
            chunk_id=f"{ir.doc_id}__chunk-{index}",
            content=content,
            source_doc_id=ir.doc_id,
            section=None,
            metadata=metadata,
        )

    def _do_sample(self, ir: IntermediateRepresentation) -> List[DocumentChunk]:
        """按字符长度切分；非首尾片段使用 `...` 标识上下文被截断。"""
        text = ir.text or ""
        if self.config.strip_whitespace:
            text = text.strip()
        if not text:
            return []
        if self.config.chunk_size <= len(ELLIPSIS) * 2:
            raise ValueError("chunk_size 过小，无法容纳截断标识与正文")
        if len(text) <= self.config.chunk_size:
            return [
                self._make_chunk(
                    ir=ir,
                    index=1,
                    raw_content=text,
                    start=0,
                    end=len(text),
                    has_prefix_gap=False,
                    has_suffix_gap=False,
                )
            ]

        chunks: List[DocumentChunk] = []
        cursor = 0
        chunk_index = 1
        total_len = len(text)

        while cursor < total_len:
            has_prefix_gap = cursor > 0
            budget_without_suffix = self._content_budget(
                has_prefix_gap=has_prefix_gap,
                has_suffix_gap=False,
            )
            if cursor + budget_without_suffix >= total_len:
                has_suffix_gap = False
                raw_len = total_len - cursor
            else:
                has_suffix_gap = True
                raw_len = self._content_budget(
                    has_prefix_gap=has_prefix_gap,
                    has_suffix_gap=True,
                )
            if raw_len <= 0:
                raise ValueError("chunk_size 过小，无法生成有效 chunk")

            next_cursor = min(cursor + raw_len, total_len)
            raw_content = text[cursor:next_cursor]
            chunks.append(
                self._make_chunk(
                    ir=ir,
                    index=chunk_index,
                    raw_content=raw_content,
                    start=cursor,
                    end=next_cursor,
                    has_prefix_gap=has_prefix_gap,
                    has_suffix_gap=has_suffix_gap,
                )
            )
            cursor = next_cursor
            chunk_index += 1

        return chunks
