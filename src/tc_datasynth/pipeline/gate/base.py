from __future__ import annotations

"""
门控器接口定义。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.models import GateDecision, QAPair
from tc_datasynth.core.registrable import RegistrableComponent
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


@dataclass(slots=True)
class GateConfigBase:
    """门控器基础配置。"""

    pass


TGateConfig = TypeVar("TGateConfig", bound=GateConfigBase)


class QualityGateBase(
    RegistrableComponent,
    LoopBatchMixin[QAPair, GateDecision],
    ABC,
    Generic[TGateConfig],
):
    """门控器接口，负责组合校验结果并做通过/拦截决策。"""

    config: TGateConfig
    single_method_name: str = "evaluate"

    def __init__(self, config: Optional[TGateConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TGateConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, qa: QAPair) -> GateDecision:
        """评估单条 QA，并给出最终门控结果。"""
        raise NotImplementedError

    def evaluate_batch(self, qa_list: Iterable[QAPair]) -> List[GateDecision]:
        """批量评估 QA，默认循环调用 evaluate。"""
        return self.batch_run(qa_list)
