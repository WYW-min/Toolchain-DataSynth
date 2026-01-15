from __future__ import annotations

"""
Mock 生成器：不调用 LLM，仅构造稳定的假数据。
"""

import random
from dataclasses import dataclass
from typing import Dict, List

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk, QAPair
from tc_datasynth.pipeline.generator.base import GeneratorConfigBase, QAGeneratorBase


@dataclass(slots=True)
class GenerationConfig(GeneratorConfigBase):
    """生成器配置，控制 mock 问答数量与随机种子。"""

    mock_questions_per_doc: int = 3


class MockQAGenerator(QAGeneratorBase[GenerationConfig]):
    """W1 使用的模拟生成器，不调用 LLM，仅构造稳定的假数据。"""

    def __init__(self, config: GenerationConfig | None = None) -> None:
        """初始化生成器并设置随机种子。"""
        super().__init__(config)
        self._rng = random.Random(self.config.seed)

    @classmethod
    def default_config(cls) -> GenerationConfig:
        """返回默认配置。"""
        return GenerationConfig()

    def generate(self, chunks: List[DocumentChunk], ctx: RunContext) -> List[QAPair]:
        """基于 chunk 生成问答对，数量与内容可复现。"""
        qa_pairs: List[QAPair] = []
        per_chunk = max(1, self.config.mock_questions_per_doc // max(1, len(chunks)))
        difficulty_pool = ctx.plan.difficulty_profile
        qtype_pool = ctx.plan.question_type_mix
        min_evidence_len = ctx.plan.min_evidence_len
        for chunk in chunks:
            for idx in range(per_chunk):
                difficulty = self._pick_key(difficulty_pool, fallback="medium")
                qtype = self._pick_key(qtype_pool, fallback="definition")
                question = f"[{qtype}] Q{idx + 1} about {chunk.section or 'document'}?"
                answer = f"[mock answer:{difficulty}] Derived from {chunk.chunk_id}."
                evidence = self._ensure_min_len(chunk.content[:280], min_evidence_len)
                qa_pairs.append(
                    QAPair(
                        question=question,
                        answer=answer,
                        evidence=evidence,
                        source_doc_id=chunk.source_doc_id,
                        chunk_id=chunk.chunk_id,
                        metadata={
                            "generator": "mock",
                            "seed": str(self.config.seed),
                            "difficulty": difficulty,
                            "question_type": qtype,
                        },
                    )
                )
        self._rng.shuffle(qa_pairs)
        return qa_pairs

    def _pick_key(self, pool: Dict[str, float], fallback: str) -> str:
        """按权重随机选择一个 key。"""
        if not pool:
            return fallback
        keys = list(pool.keys())
        weights = list(pool.values())
        return self._rng.choices(keys, weights=weights, k=1)[0]

    def _ensure_min_len(self, text: str, min_len: int) -> str:
        """保证证据文本满足最小长度要求。"""
        if len(text) >= min_len:
            return text
        padding = "." * max(0, min_len - len(text))
        return f"{text}{padding}"
