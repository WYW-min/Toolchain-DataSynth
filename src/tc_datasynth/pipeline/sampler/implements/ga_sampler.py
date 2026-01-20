from __future__ import annotations

"""
贪心追加切片：按句子从左到右生成 chunk。
"""

import re
from dataclasses import dataclass, field
from typing import List

from tc_datasynth.core.models import DocumentChunk, IntermediateRepresentation
from tc_datasynth.pipeline.sampler.base import SamplerBase, SamplerConfigBase


@dataclass(slots=True)
class GreedyAdditionSamplingConfig(SamplerConfigBase):
    """贪心切分配置。"""

    separators: List[str] = field(
        default_factory=lambda: ["。", "！", "？", ".", "!", "?", "\n\n"]
    )
    min_sentence_len: int = 10


class GreedyAdditionSampler(SamplerBase[GreedyAdditionSamplingConfig]):
    """基于句子贪心追加生成文档片段。"""

    @classmethod
    def default_config(cls) -> GreedyAdditionSamplingConfig:
        return GreedyAdditionSamplingConfig()

    def _build_pattern(self) -> re.Pattern:
        """构建分隔符正则，长分隔符优先匹配。"""
        sorted_seps = sorted(self.config.separators, key=len, reverse=True)
        escaped = [re.escape(sep) for sep in sorted_seps]
        return re.compile(f"({'|'.join(escaped)})")

    def _split_sentences(self, text: str) -> List[str]:
        """按分隔符拆分句子，保留分隔符。"""
        pattern = self._build_pattern()
        parts = pattern.split(text)

        sentences: List[str] = []
        buffer = ""
        separators_set = set(self.config.separators)

        for part in parts:
            if not part:
                continue
            buffer += part
            if part in separators_set:
                sentence = buffer.strip() if self.config.strip_whitespace else buffer
                if sentence:
                    sentences.append(sentence)
                buffer = ""

        if buffer:
            sentence = buffer.strip() if self.config.strip_whitespace else buffer
            if sentence:
                sentences.append(sentence)
        return sentences

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
        sentence_count: int | None = None,
        strategy: str = "greedy_addition",
    ) -> DocumentChunk:
        """创建文档片段。"""
        if self.config.strip_whitespace:
            content = content.strip()
        metadata: dict = {"strategy": strategy}
        if sentence_count is not None:
            metadata["sentence_count"] = sentence_count
        return DocumentChunk(
            chunk_id=f"{doc_id}-chunk-{index}",
            content=content,
            source_doc_id=doc_id,
            section=None,
            metadata=metadata,
        )

    def _do_sample(self, ir: IntermediateRepresentation) -> List[DocumentChunk]:
        """核心切分逻辑：按句子贪心追加生成 chunk。"""
        text = ir.text or ""
        sentences = self._split_sentences(text)

        if not sentences:
            content = text.strip() if self.config.strip_whitespace else text
            if not content:
                return []
            return [
                self._create_chunk(ir.doc_id, 0, content, strategy="greedy_fallback")
            ]

        sentences = self._merge_short_sentences(sentences)
        chunks: List[DocumentChunk] = []
        current_sentences: List[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if (
                current_len + sentence_len <= self.config.chunk_size
                or not current_sentences
            ):
                current_sentences.append(sentence)
                current_len += sentence_len
            else:
                chunks.append(
                    self._create_chunk(
                        ir.doc_id,
                        len(chunks),
                        "".join(current_sentences),
                        sentence_count=len(current_sentences),
                    )
                )
                current_sentences = [sentence]
                current_len = sentence_len

        if current_sentences:
            chunks.append(
                self._create_chunk(
                    ir.doc_id,
                    len(chunks),
                    "".join(current_sentences),
                    sentence_count=len(current_sentences),
                )
            )
        return chunks
