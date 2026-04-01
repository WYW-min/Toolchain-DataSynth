from __future__ import annotations

"""
标签合法性校验器。
"""

from dataclasses import dataclass, field
from typing import List, Sequence

from tc_datasynth.core.models import QAPair, ValidationResult
from tc_datasynth.pipeline.validator.base import ValidatorBase, ValidatorConfigBase


@dataclass(slots=True)
class LabelValidatorConfig(ValidatorConfigBase):
    """标签校验配置。"""

    allowed_difficulties: Sequence[str] = field(
        default_factory=lambda: ("easy", "medium", "hard")
    )
    allowed_question_types: Sequence[str] = field(
        default_factory=lambda: ("definition", "factual", "reasoning")
    )
    reasoning_min_evidence_len: int = 80


class LabelValidator(ValidatorBase[LabelValidatorConfig]):
    """检查 difficulty/question_type 标签是否在允许集合内。"""

    component_name = "label"

    @classmethod
    def default_config(cls) -> LabelValidatorConfig:
        return LabelValidatorConfig()

    def validate(self, qa: QAPair) -> ValidationResult:
        errors: List[str] = []
        labels = qa.qa_info.labels
        difficulty = labels.get("difficulty")
        question_type = labels.get("question_type")
        if difficulty not in self.config.allowed_difficulties:
            errors.append("label.invalid_difficulty")
        if question_type not in self.config.allowed_question_types:
            errors.append("label.invalid_question_type")
        if question_type == "reasoning":
            longest_evidence = max((len(item.strip()) for item in qa.evidences), default=0)
            if longest_evidence < self.config.reasoning_min_evidence_len:
                errors.append("label.reasoning_insufficient_context")
        return ValidationResult(qa=qa, errors=errors)
