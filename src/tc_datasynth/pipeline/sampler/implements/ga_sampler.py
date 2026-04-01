from __future__ import annotations

"""
贪心追加切片：优先按段落，再按句子，最后字符兜底。
"""

import re
from dataclasses import dataclass, field
from typing import List

from tc_datasynth.core.models import DocumentChunk, IntermediateRepresentation
from tc_datasynth.pipeline.sampler.base import SamplerBase, SamplerConfigBase


@dataclass(slots=True)
class GreedyAdditionSamplingConfig(SamplerConfigBase):
    """贪心切分配置。"""

    paragraph_separators: List[str] = field(default_factory=lambda: ["\n\n"])
    separators: List[str] = field(
        default_factory=lambda: ["。", "！", "？", ".", "!", "?", ";", "；"]
    )
    min_sentence_len: int = 10
    anchor_length: int = 0
    char_fallback_backoff: int = 80


class GreedyAdditionSampler(SamplerBase[GreedyAdditionSamplingConfig]):
    """基于多级边界贪心追加生成文档片段。"""

    component_name = "greedy_addition"

    @classmethod
    def default_config(cls) -> GreedyAdditionSamplingConfig:
        return GreedyAdditionSamplingConfig()

    @staticmethod
    def _build_pattern(separators: List[str]) -> re.Pattern:
        """构建分隔符正则，长分隔符优先匹配。"""
        sorted_seps = sorted(separators, key=len, reverse=True)
        escaped = [re.escape(sep) for sep in sorted_seps]
        return re.compile(f"({'|'.join(escaped)})")

    def _split_units(self, text: str, separators: List[str]) -> List[str]:
        """按分隔符拆分文本单元，保留分隔符。"""
        if not separators:
            return [text] if text else []
        pattern = self._build_pattern(separators)
        parts = pattern.split(text)

        units: List[str] = []
        buffer = ""
        separators_set = set(separators)

        for part in parts:
            if not part:
                continue
            buffer += part
            if part in separators_set:
                if buffer.strip():
                    units.append(buffer)
                buffer = ""

        if buffer:
            if buffer.strip():
                units.append(buffer)
        return units

    def _split_paragraphs(self, text: str) -> List[str]:
        """优先按换行/空行切分段落。"""
        return self._split_units(text, self.config.paragraph_separators)

    def _split_sentences(self, text: str) -> List[str]:
        """段内再按句末边界切分。"""
        return self._split_units(text, self.config.separators)

    def _merge_short_sentences(self, sentences: List[str]) -> List[str]:
        """将短句合并到后续句子。"""
        if self.config.min_sentence_len <= 0:
            return sentences
        merged: List[str] = []
        pending = ""
        for sentence in sentences:
            if len(sentence) < self.config.min_sentence_len:
                pending += sentence
                continue
            if pending:
                sentence = pending + sentence
                pending = ""
            merged.append(sentence)
        if pending:
            if merged:
                merged[-1] += pending
            else:
                merged.append(pending)
        return merged

    def _create_chunk(
        self,
        doc_id: str,
        index: int,
        content: str,
        strategy: str,
        split_level: str,
        unit_count: int | None,
        source_metadata: dict | None = None,
    ) -> DocumentChunk:
        """创建文档片段。"""
        if self.config.strip_whitespace:
            content = content.strip()
        metadata: dict = {
            **(source_metadata or {}),
            "strategy": strategy,
            "split_level": split_level,
        }
        if unit_count is not None:
            metadata["unit_count"] = unit_count
        return DocumentChunk(
            chunk_id=f"{doc_id}__chunk-{index}",
            content=content,
            source_doc_id=doc_id,
            section=None,
            metadata=metadata,
        )

    def _append_chunk(
        self,
        chunks: List[DocumentChunk],
        ir: IntermediateRepresentation,
        content: str,
        strategy: str,
        split_level: str,
        unit_count: int | None,
        source_metadata: dict,
    ) -> None:
        """追加一个 chunk。"""
        chunks.append(
            self._create_chunk(
                doc_id=ir.doc_id,
                index=len(chunks),
                content=content,
                strategy=strategy,
                split_level=split_level,
                unit_count=unit_count,
                source_metadata=source_metadata,
            )
        )

    def _pack_units(
        self,
        ir: IntermediateRepresentation,
        chunks: List[DocumentChunk],
        units: List[str],
        source_metadata: dict,
        split_level: str,
    ) -> None:
        """将同一层级的文本单元贪心打包成 chunk。"""
        current_units: List[str] = []
        current_len = 0

        for unit in units:
            unit_len = len(unit)
            if unit_len > self.config.chunk_size:
                if current_units:
                    self._append_chunk(
                        chunks,
                        ir,
                        "".join(current_units),
                        strategy="greedy_addition",
                        split_level=split_level,
                        unit_count=len(current_units),
                        source_metadata=source_metadata,
                    )
                    current_units = []
                    current_len = 0
                self._pack_oversize_unit(ir, chunks, unit, source_metadata)
                continue
            if current_len + unit_len <= self.config.chunk_size or not current_units:
                current_units.append(unit)
                current_len += unit_len
            else:
                self._append_chunk(
                    chunks,
                    ir,
                    "".join(current_units),
                    strategy="greedy_addition",
                    split_level=split_level,
                    unit_count=len(current_units),
                    source_metadata=source_metadata,
                )
                current_units = [unit]
                current_len = unit_len

        if current_units:
            self._append_chunk(
                chunks,
                ir,
                "".join(current_units),
                strategy="greedy_addition",
                split_level=split_level,
                unit_count=len(current_units),
                source_metadata=source_metadata,
            )

    def _pack_oversize_unit(
        self,
        ir: IntermediateRepresentation,
        chunks: List[DocumentChunk],
        unit: str,
        source_metadata: dict,
    ) -> None:
        """对超长单元做层级回退：句子优先，单句超长时保留整句。"""
        sentences = self._split_sentences(unit)
        if not sentences or len(sentences) == 1 and sentences[0] == unit:
            self._append_chunk(
                chunks,
                ir,
                unit,
                strategy="greedy_addition",
                split_level="sentence",
                unit_count=1,
                source_metadata=source_metadata,
            )
            return

        merged_sentences = self._merge_short_sentences(sentences)
        self._pack_sentence_units(
            ir=ir,
            chunks=chunks,
            sentences=merged_sentences,
            source_metadata=source_metadata,
        )

    def _pack_sentence_units(
        self,
        ir: IntermediateRepresentation,
        chunks: List[DocumentChunk],
        sentences: List[str],
        source_metadata: dict,
    ) -> None:
        """按句子锚点长度进行误差反馈打包。"""
        if not sentences:
            return
        anchor = self.config.anchor_length or self.config.chunk_size
        anchor = max(1, anchor)
        total_error = 0
        cursor = 0
        total = len(sentences)

        while cursor < total:
            current_units = [sentences[cursor]]
            current_len = len(sentences[cursor])
            cursor += 1

            while cursor < total and current_len < anchor:
                next_sentence = sentences[cursor]
                next_len = len(next_sentence)
                next_total = current_len + next_len

                if next_total <= anchor:
                    current_units.append(next_sentence)
                    current_len = next_total
                    cursor += 1
                    continue

                drop_error = total_error + (current_len - anchor)
                keep_error = total_error + (next_total - anchor)
                if abs(keep_error) <= abs(drop_error):
                    current_units.append(next_sentence)
                    current_len = next_total
                    cursor += 1
                    total_error = keep_error
                else:
                    total_error = drop_error
                break
            else:
                total_error += current_len - anchor

            self._append_chunk(
                chunks,
                ir,
                "".join(current_units),
                strategy="greedy_addition",
                split_level="sentence",
                unit_count=len(current_units),
                source_metadata=source_metadata,
            )

    def _pack_char_fallback(
        self,
        ir: IntermediateRepresentation,
        chunks: List[DocumentChunk],
        text: str,
        source_metadata: dict,
    ) -> None:
        """当没有稳定边界可用时，退回软边界优先的字符切分。"""
        cursor = 0
        total = len(text)
        while cursor < total:
            hard_end = min(cursor + self.config.chunk_size, total)
            next_cursor = self._find_soft_break(text, cursor, hard_end)
            self._append_chunk(
                chunks,
                ir,
                text[cursor:next_cursor],
                strategy="greedy_char_fallback",
                split_level="char",
                unit_count=None,
                source_metadata=source_metadata,
            )
            cursor = next_cursor

    def _find_soft_break(self, text: str, start: int, hard_end: int) -> int:
        """在字符兜底时尽量靠近软边界截断，避免生硬断词。"""
        if hard_end >= len(text):
            return hard_end
        lower_bound = max(start + 1, hard_end - max(0, self.config.char_fallback_backoff))
        for candidates in ({"\n"}, {" ", "\t"}, {"。", "！", "？", ".", "!", "?", ";", "；", ",", "，"}):
            for idx in range(hard_end - 1, lower_bound - 1, -1):
                if text[idx] in candidates:
                    return idx + 1
        return hard_end

    def _do_sample(self, ir: IntermediateRepresentation) -> List[DocumentChunk]:
        """核心切分逻辑：段落优先、句子次之、字符兜底。"""
        text = ir.text or ""
        if self.config.strip_whitespace:
            text = text.strip()
        if not text:
            return []

        source_metadata = self._build_source_metadata(ir)
        paragraphs = self._split_paragraphs(text)
        chunks: List[DocumentChunk] = []
        self._pack_units(
            ir=ir,
            chunks=chunks,
            units=paragraphs or [text],
            source_metadata=source_metadata,
            split_level="paragraph",
        )
        return chunks
