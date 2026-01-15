from __future__ import annotations

"""
最小门禁实现：Schema 校验与组合器。
"""

from dataclasses import dataclass
from typing import Iterable, List

from tc_datasynth.core.models import QAPair, ValidationResult
from tc_datasynth.pipeline.validator.base import QualityGateBase, ValidatorConfigBase


@dataclass(slots=True)
class SimpleValidatorConfig(ValidatorConfigBase):
    """Simple 门禁配置。"""

    pass


class SimpleSchemaGate(QualityGateBase[SimpleValidatorConfig]):
    """检查必填字段是否存在且非空。"""

    REQUIRED_FIELDS = ("question", "answer", "evidence", "source_doc_id", "chunk_id")

    def __init__(self, config: SimpleValidatorConfig | None = None) -> None:
        """初始化门禁配置。"""
        super().__init__(config)

    @classmethod
    def default_config(cls) -> SimpleValidatorConfig:
        """返回默认配置。"""
        return SimpleValidatorConfig()

    def validate(self, qa: QAPair) -> ValidationResult:
        """校验单条 QA 的字段完整性。"""
        errors: List[str] = []
        for field_name in self.REQUIRED_FIELDS:
            if not getattr(qa, field_name):
                errors.append(f"missing_field:{field_name}")
        return ValidationResult(qa=qa, errors=errors)


@dataclass(slots=True)
class SimpleCompositeConfig(ValidatorConfigBase):
    """组合门禁配置。"""

    pass


class SimpleCompositeGate(QualityGateBase[SimpleCompositeConfig]):
    """组合多个门禁，按顺序执行，遇到错误即返回。"""

    def __init__(self, gates: Iterable[QualityGateBase], config: SimpleCompositeConfig | None = None) -> None:
        """注入门禁列表。"""
        super().__init__(config)
        self.gates = list(gates)

    @classmethod
    def default_config(cls) -> SimpleCompositeConfig:
        """返回默认配置。"""
        return SimpleCompositeConfig()

    def validate(self, qa: QAPair) -> ValidationResult:
        """依次执行门禁校验。"""
        for gate in self.gates:
            result = gate.validate(qa)
            if not result.is_valid:
                return result
        return ValidationResult(qa=qa, errors=[])
