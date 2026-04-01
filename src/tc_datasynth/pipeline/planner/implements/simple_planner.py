from __future__ import annotations

"""
最小规划器实现：将全局比例翻译为 chunk 级 planning meta。
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk
from tc_datasynth.pipeline.planner.base import PlannerBase, PlannerConfigBase


@dataclass(slots=True)
class SimplePlannerConfig(PlannerConfigBase):
    """简单规划器配置。"""

    difficulty_order: tuple[str, ...] = ("easy", "medium", "hard")
    skip_below_evidence_ratio: float = 0.5
    reasoning_cues: tuple[str, ...] = (
        "because",
        "therefore",
        "thus",
        "suggest",
        "indicate",
        "result",
        "due to",
        "compared",
        "whereas",
        "in contrast",
        "因为",
        "因此",
        "所以",
        "表明",
        "导致",
        "相比",
    )
    definition_cues: tuple[str, ...] = (
        "is defined as",
        "refers to",
        "defined as",
        "means",
        "abstract",
        "keyword",
        "keywords",
        "定义为",
        "是指",
        "摘要",
        "关键词",
    )


class SimplePlanner(PlannerBase[SimplePlannerConfig]):
    """按全局比例稳定分配难度与题型。"""

    component_name = "simple"

    def __init__(self, config: SimplePlannerConfig | None = None) -> None:
        super().__init__(config)
        self._planned_total = 0
        self._difficulty_counts: Counter[str] = Counter()
        self._question_type_counts: Counter[str] = Counter()

    @classmethod
    def default_config(cls) -> SimplePlannerConfig:
        """返回默认配置。"""
        return SimplePlannerConfig()

    def plan(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
    ) -> List[Dict[str, Any]]:
        """为 chunk 列表分配 difficulty/question_type。"""
        chunk_list = list(chunks)
        if not chunk_list:
            return []

        metas: List[Dict[str, Any]] = [self._build_base_meta(chunk, ctx) for chunk in chunk_list]
        eligible_indices = [
            idx
            for idx, meta in enumerate(metas)
            if bool(meta.get("system_meta", {}).get("should_generate", True))
        ]
        if not eligible_indices:
            start_index = self._planned_total
            for offset, meta in enumerate(metas):
                meta["system_meta"]["planner"] = self.get_component_name()
                meta["system_meta"]["plan_index"] = start_index + offset + 1
            self._planned_total += len(chunk_list)
            return metas

        difficulty_labels = self._allocate_labels(
            len(eligible_indices),
            ctx.plan.difficulty_profile,
            self._difficulty_counts,
            fallback="medium",
        )
        question_type_labels = self._allocate_labels(
            len(eligible_indices),
            ctx.plan.question_type_mix,
            self._question_type_counts,
            fallback="definition",
        )

        eligible_chunks = [chunk_list[idx] for idx in eligible_indices]
        eligible_metas = [metas[idx] for idx in eligible_indices]
        self._assign_difficulty(eligible_chunks, eligible_metas, difficulty_labels)

        start_index = self._planned_total
        for offset, meta in enumerate(metas):
            meta["system_meta"]["planner"] = self.get_component_name()
            meta["system_meta"]["plan_index"] = start_index + offset + 1

        for meta, question_type in zip(
            eligible_metas, question_type_labels, strict=True
        ):
            meta["prompt_meta"]["question_type"] = question_type

        self._planned_total += len(chunk_list)
        return metas

    def _build_base_meta(
        self,
        chunk: DocumentChunk,
        ctx: RunContext,
    ) -> Dict[str, Any]:
        """构造规划前的轻量元信息，不改目标分布。"""
        text = chunk.content or ""
        text_len = len(text)
        min_evidence_len = max(1, int(ctx.plan.min_evidence_len))
        skip_threshold = max(1, int(min_evidence_len * self.config.skip_below_evidence_ratio))
        lower_text = text.lower()
        reasoning_signal = any(cue in lower_text for cue in self.config.reasoning_cues)
        definition_signal = any(cue in lower_text for cue in self.config.definition_cues)

        if text_len < skip_threshold:
            length_bucket = "short"
        elif text_len < min_evidence_len:
            length_bucket = "medium"
        else:
            length_bucket = "long"

        should_generate = text_len >= skip_threshold
        return {
            "system_meta": {
                "planner": self.get_component_name(),
                "should_generate": should_generate,
                "skip_reason": None if should_generate else "below_min_evidence_window",
                "length_bucket": length_bucket,
                "evidence_ready": text_len >= min_evidence_len,
            },
            "prompt_meta": {
                "reasoning_signal": reasoning_signal,
                "definition_signal": definition_signal,
            },
        }

    def _assign_difficulty(
        self,
        chunks: List[DocumentChunk],
        metas: List[Dict[str, Any]],
        difficulty_labels: List[str],
    ) -> None:
        """将更高难度尽量分配给更长的 chunk。"""
        ranked_indices = sorted(
            range(len(chunks)),
            key=lambda idx: len(chunks[idx].content or ""),
            reverse=True,
        )
        ranked_difficulties = sorted(
            difficulty_labels,
            key=self._difficulty_rank,
            reverse=True,
        )
        for idx, difficulty in zip(ranked_indices, ranked_difficulties, strict=True):
            metas[idx]["prompt_meta"]["difficulty"] = difficulty

    def _difficulty_rank(self, name: str) -> int:
        """返回难度排序值，未知标签按中等处理。"""
        if name in self.config.difficulty_order:
            return self.config.difficulty_order.index(name)
        return len(self.config.difficulty_order) // 2

    @staticmethod
    def _allocate_labels(
        total: int,
        ratios: Dict[str, float],
        counts: Counter[str],
        fallback: str,
    ) -> List[str]:
        """基于 deficit round-robin 分配标签，保证前缀分布稳定。"""
        if total <= 0:
            return []
        labels = list(ratios.keys())
        if not labels:
            labels = [fallback]
            ratios = {fallback: 1.0}

        working = Counter({label: counts.get(label, 0) for label in labels})
        assigned_total = sum(working.values())
        results: List[str] = []
        for _ in range(total):
            next_total = assigned_total + 1
            best_label = max(
                labels,
                key=lambda label: ratios.get(label, 0.0) * next_total - working[label],
            )
            results.append(best_label)
            working[best_label] += 1
            assigned_total = next_total

        counts.clear()
        counts.update(working)
        return results
