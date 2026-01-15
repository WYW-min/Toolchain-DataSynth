from __future__ import annotations

"""
门禁接口定义。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.models import QAPair, ValidationResult
from tc_datasynth.pipeline.mixins.batch import LoopBatchMixin


@dataclass(slots=True)
class ValidatorConfigBase:
    """门禁基础配置。"""

    pass


TValidatorConfig = TypeVar("TValidatorConfig", bound=ValidatorConfigBase)


class QualityGateBase(LoopBatchMixin[QAPair, ValidationResult], ABC, Generic[TValidatorConfig]):
    """门禁接口。"""

    config: TValidatorConfig
    single_method_name: str = "validate"

    def __init__(self, config: Optional[TValidatorConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TValidatorConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def validate(self, qa: QAPair) -> ValidationResult:
        """校验单条 QA。"""
        raise NotImplementedError

    def validate_batch(self, qa_list: Iterable[QAPair]) -> List[ValidationResult]:
        """批量校验 QA，默认循环调用 validate。"""
        return self.batch_run(qa_list)
