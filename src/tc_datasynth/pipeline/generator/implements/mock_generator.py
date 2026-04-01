from __future__ import annotations

"""
Mock 生成器：不调用 LLM，仅构造稳定的假数据。
"""

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk, QAPair, build_qa_id
from tc_datasynth.pipeline.generator.base import GeneratorConfigBase, QAGeneratorBase


@dataclass(slots=True)
class GenerationConfig(GeneratorConfigBase):
    """生成器配置，控制 mock 问答数量与随机种子。"""

    questions_per_doc: int = 3


class MockQAGenerator(QAGeneratorBase[GenerationConfig]):
    """W1 使用的模拟生成器，不调用 LLM，仅构造稳定的假数据。"""

    component_name = "mock"

    def __init__(self, config: GenerationConfig | None = None) -> None:
        """初始化生成器并设置随机种子。"""
        super().__init__(config)
        self._rng = random.Random(self.config.seed)

    @classmethod
    def default_config(cls) -> GenerationConfig:
        """返回默认配置。"""
        return GenerationConfig()

    def generate(
        self,
        chunks: List[DocumentChunk],
        ctx: RunContext,
        metas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[QAPair]:
        """基于 chunk 生成问答对，数量与内容可复现。"""
        qa_pairs: List[QAPair] = []
        per_chunk = max(1, self.config.questions_per_doc // max(1, len(chunks)))
        difficulty_pool = ctx.plan.difficulty_profile
        qtype_pool = ctx.plan.question_type_mix
        min_evidence_len = ctx.plan.min_evidence_len
        qa_limit = ctx.extras.get("generator_qa_limit")
        remaining = int(qa_limit) if isinstance(qa_limit, int) and qa_limit > 0 else None
        metas = metas or [{} for _ in chunks]
        for chunk, meta in zip(chunks, metas):
            system_meta = meta.get("system_meta", {}) if isinstance(meta, dict) else {}
            prompt_meta = meta.get("prompt_meta", {}) if isinstance(meta, dict) else {}
            for idx in range(per_chunk):
                difficulty = str(prompt_meta.get("difficulty") or "").strip() or self._pick_key(
                    difficulty_pool, fallback="medium"
                )
                qtype = str(prompt_meta.get("question_type") or "").strip() or self._pick_key(
                    qtype_pool, fallback="definition"
                )
                question = f"[{qtype}] Q{idx + 1} about {chunk.section or 'document'}?"
                answer = f"[mock answer:{difficulty}] Derived from {chunk.chunk_id}."
                evidence = self._ensure_min_len(chunk.content[:280], min_evidence_len)
                qa_pairs.append(
                    QAPair(
                        qa_id=build_qa_id(
                            ctx.run_id,
                            chunk.source_doc_id,
                            chunk.chunk_id,
                            idx + 1,
                        ),
                        provenance={
                            "run_id": ctx.run_id,
                            "source_doc_id": chunk.source_doc_id,
                            "chunk_id": chunk.chunk_id,
                            "qa_index": idx + 1,
                            "line_start": chunk.metadata.get("line_start"),
                            "line_end": chunk.metadata.get("line_end"),
                            "generator": "mock",
                            "planner": str(system_meta.get("planner") or "") or None,
                            "plan_index": system_meta.get("plan_index"),
                        },
                        qa_info={
                            "question": question,
                            "answer": answer,
                            "evidences": [evidence],
                            "labels": {
                                "difficulty": difficulty,
                                "question_type": qtype,
                            },
                        },
                    )
                )
                self.notify_progress(ctx)
                if remaining is not None and len(qa_pairs) >= remaining:
                    self._rng.shuffle(qa_pairs)
                    return qa_pairs[:remaining]
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
