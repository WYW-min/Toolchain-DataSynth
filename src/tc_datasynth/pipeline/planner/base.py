from __future__ import annotations

"""
题目规划器接口与注册表。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk
from tc_datasynth.core.registrable import RegistrableComponent
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


class PlannerRegistry:
    """规划器注册表，基于名称路由。"""

    def __init__(self, mapping: Optional[Dict[str, type["PlannerBase[Any]"]]] = None) -> None:
        self.mapping: Dict[str, type[PlannerBase[Any]]] = mapping or {}

    def register(self, name: str, planner_cls: type["PlannerBase[Any]"]) -> None:
        """按名称注册规划器。"""
        self.mapping[name.lower()] = planner_cls

    def resolve(self, name: str) -> type["PlannerBase[Any]"]:
        """根据名称返回对应规划器。"""
        key = name.lower()
        if key in self.mapping:
            return self.mapping[key]
        raise ValueError(f"未找到规划器: {name}")


@dataclass(slots=True)
class PlannerConfigBase:
    """规划器基础配置。"""

    seed: int = 0


TPlannerConfig = TypeVar("TPlannerConfig", bound=PlannerConfigBase)


class PlannerBase(
    RegistrableComponent,
    LoopBatchMixin[Iterable[DocumentChunk], List[Dict[str, Any]]],
    ABC,
    Generic[TPlannerConfig],
):
    """规划器接口：为每个 chunk 生成一条 planning meta。"""

    config: TPlannerConfig
    single_method_name: str = "plan"

    def __init__(self, config: Optional[TPlannerConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TPlannerConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def plan(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
    ) -> List[Dict[str, Any]]:
        """为给定 chunk 列表生成与之对齐的规划元数据。"""
        raise NotImplementedError

    def plan_batch(
        self,
        batch_chunks: Iterable[Iterable[DocumentChunk]],
        ctx: RunContext,
    ) -> List[List[Dict[str, Any]]]:
        """批量规划，默认循环调用 plan。"""
        return self.batch_run(batch_chunks, ctx)
