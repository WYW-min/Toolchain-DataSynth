from __future__ import annotations

"""
适配器基类：将原始文档转换为中间产物，供统一解析器消费。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.core.registrable import RegistrableComponent
from tc_datasynth.pipeline.adapter.types import AdapterResult


@dataclass(slots=True)
class AdapterConfigBase:
    """适配器基础配置。"""

    output_subdir: str = "parser"


TAdapterConfig = TypeVar("TAdapterConfig", bound=AdapterConfigBase)


class DocumentAdapter(RegistrableComponent, ABC, Generic[TAdapterConfig]):
    """解析/适配接口，负责从输入文档生成 AdapterResult。"""

    config: TAdapterConfig

    def __init__(self, config: Optional[TAdapterConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TAdapterConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """将单个文档解析为中间结果。"""
        raise NotImplementedError
