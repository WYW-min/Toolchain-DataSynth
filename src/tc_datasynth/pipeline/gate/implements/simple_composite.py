from __future__ import annotations

"""
最小门控实现：组合多个原子校验器。
"""

from dataclasses import dataclass
from typing import Iterable, List

from tc_datasynth.core.models import GateDecision, QAPair
from tc_datasynth.pipeline.gate.base import GateConfigBase, QualityGateBase
from tc_datasynth.pipeline.validator import ValidatorBase


@dataclass(slots=True)
class SimpleCompositeGateConfig(GateConfigBase):
    """组合门控配置。"""

    stop_on_first_error: bool = True


class SimpleCompositeGate(QualityGateBase[SimpleCompositeGateConfig]):
    """组合多个原子校验器，并给出最终拦截结果。"""

    component_name = "simple_composite"

    def __init__(
        self,
        validators: Iterable[ValidatorBase],
        config: SimpleCompositeGateConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.validators = list(validators)

    @classmethod
    def default_config(cls) -> SimpleCompositeGateConfig:
        """返回默认配置。"""
        return SimpleCompositeGateConfig()

    def evaluate(self, qa: QAPair) -> GateDecision:
        """聚合校验结果，默认首错即停。"""
        errors: List[str] = []
        for validator in self.validators:
            result = validator.validate(qa)
            if not result.is_valid:
                errors.extend(result.errors)
                if self.config.stop_on_first_error:
                    break
        action = "pass" if not errors else "reject"
        return GateDecision(qa=qa, errors=errors, action=action, stage="gate")
