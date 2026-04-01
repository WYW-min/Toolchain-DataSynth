from __future__ import annotations

"""
证据质量校验器。
"""

from dataclasses import dataclass
from typing import List

from tc_datasynth.core.models import QAPair, ValidationResult
from tc_datasynth.pipeline.validator.base import ValidatorBase, ValidatorConfigBase


@dataclass(slots=True)
class EvidenceValidatorConfig(ValidatorConfigBase):
    """证据校验配置。"""

    min_evidence_len: int = 80


class EvidenceValidator(ValidatorBase[EvidenceValidatorConfig]):
    """检查 evidence 是否存在且长度达到基本阈值。"""

    component_name = "evidence"

    @classmethod
    def default_config(cls) -> EvidenceValidatorConfig:
        return EvidenceValidatorConfig()

    def validate(self, qa: QAPair) -> ValidationResult:
        errors: List[str] = []
        evidences = [item.strip() for item in qa.evidences if item and item.strip()]
        if not evidences:
            errors.append("evidence.empty")
        else:
            longest = max(len(item) for item in evidences)
            if longest < self.config.min_evidence_len:
                errors.append("evidence.too_short")
        return ValidationResult(qa=qa, errors=errors)
