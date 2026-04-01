from __future__ import annotations

"""
最小原子校验器实现：Schema 校验。
"""

from dataclasses import dataclass
from typing import List

from tc_datasynth.core.models import QAPair, ValidationResult
from tc_datasynth.pipeline.validator.base import ValidatorBase, ValidatorConfigBase


@dataclass(slots=True)
class SimpleValidatorConfig(ValidatorConfigBase):
    """Simple 校验器配置。"""

    pass


class SimpleSchemaValidator(ValidatorBase[SimpleValidatorConfig]):
    """检查必填字段是否存在且非空。"""

    component_name = "simple_schema"

    REQUIRED_FIELDS = ("question", "answer", "evidences", "source_doc_id", "chunk_id")

    def __init__(self, config: SimpleValidatorConfig | None = None) -> None:
        """初始化校验器配置。"""
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
                errors.append(f"schema.missing_{field_name}")
        return ValidationResult(qa=qa, errors=errors)
