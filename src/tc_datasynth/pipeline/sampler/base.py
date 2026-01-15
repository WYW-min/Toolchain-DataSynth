from __future__ import annotations

"""
切片采样器接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.models import DocumentChunk, IntermediateRepresentation
from tc_datasynth.pipeline.mixins.batch import LoopBatchMixin


@dataclass(slots=True)
class SamplerConfigBase:
    """采样器基础配置。"""

    pass


TSamplerConfig = TypeVar("TSamplerConfig", bound=SamplerConfigBase)


class SamplerBase(LoopBatchMixin[IntermediateRepresentation, List[DocumentChunk]], ABC, Generic[TSamplerConfig]):
    """切片采样器接口。"""

    config: TSamplerConfig
    single_method_name: str = "sample"

    def __init__(self, config: Optional[TSamplerConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TSamplerConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def sample(self, ir: IntermediateRepresentation) -> List[DocumentChunk]:
        """将 IR 切分为 chunk 列表。"""
        raise NotImplementedError

    def sample_batch(self, ir_list: Iterable[IntermediateRepresentation]) -> List[List[DocumentChunk]]:
        """批量切分 IR，默认循环调用 sample。"""
        return self.batch_run(ir_list)
