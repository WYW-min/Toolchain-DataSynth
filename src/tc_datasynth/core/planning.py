from __future__ import annotations

"""
Spec -> Plan 编译接口与 W1 的占位实现。
"""

from abc import ABC, abstractmethod
from typing import Dict

from tc_datasynth.core.plan import PlanConfig
from tc_datasynth.core.spec import SpecConfig


def _normalize_ratios(values: Dict[str, float], defaults: Dict[str, float]) -> Dict[str, float]:
    """归一化比例，异常时回退默认值。"""
    cleaned = {k: float(v) for k, v in values.items() if v is not None and v >= 0}
    total = sum(cleaned.values())
    if total <= 0:
        cleaned = defaults
        total = sum(cleaned.values())
    return {k: v / total for k, v in cleaned.items()}


class PlanCompiler(ABC):
    """Plan 编译器接口。"""

    @abstractmethod
    def compile(self, spec: SpecConfig) -> PlanConfig:
        """将 Spec 编译为可执行的 Plan。"""
        raise NotImplementedError


class MockPlanCompiler(PlanCompiler):
    """W1 占位实现：仅做比例归一化。"""

    def compile(self, spec: SpecConfig) -> PlanConfig:
        """编译 Spec，输出最简 Plan。"""
        difficulty = _normalize_ratios(
            spec.difficulty_profile, {"easy": 0.3, "medium": 0.5, "hard": 0.2}
        )
        qtypes = _normalize_ratios(
            spec.question_type_mix, {"definition": 0.4, "factual": 0.3, "reasoning": 0.3}
        )
        return PlanConfig(
            difficulty_profile=difficulty,
            question_type_mix=qtypes,
            min_evidence_len=spec.min_evidence_len,
        )
