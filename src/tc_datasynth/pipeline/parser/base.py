from __future__ import annotations

"""
统一解析器接口与适配器注册表。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation, SourceDocument
from tc_datasynth.core.registrable import RegistrableComponent
from tc_datasynth.pipeline.adapter import DocumentAdapter
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


class AdapterRegistry:
    """适配器注册表，基于扩展名路由。"""

    def __init__(self, mapping: Optional[Dict[str, DocumentAdapter]] = None) -> None:
        self.mapping: Dict[str, DocumentAdapter] = mapping or {}

    def register(self, ext: str, adapter: DocumentAdapter) -> None:
        """按扩展名注册适配器。"""
        self.mapping[ext.lower()] = adapter

    def resolve(self, document: SourceDocument) -> DocumentAdapter:
        """根据文件后缀返回对应适配器。"""
        ext = document.path.suffix.lower()
        if ext in self.mapping:
            return self.mapping[ext]
        raise ValueError(f"未找到适配器: {ext}")


class ParserRegistry:
    """解析器注册表，基于名称路由。"""

    def __init__(self, mapping: Optional[Dict[str, type["ParserBase[Any]"]]] = None) -> None:
        self.mapping: Dict[str, type[ParserBase[Any]]] = mapping or {}

    def register(self, name: str, parser_cls: type["ParserBase[Any]"]) -> None:
        """按名称注册解析器。"""
        self.mapping[name.lower()] = parser_cls

    def resolve(self, name: str) -> type["ParserBase[Any]"]:
        """根据名称返回对应解析器。"""
        key = name.lower()
        if key in self.mapping:
            return self.mapping[key]
        raise ValueError(f"未找到解析器: {name}")


@dataclass(slots=True)
class ParserConfigBase:
    """解析器基础配置。"""

    encoding: str = "utf-8"


TParserConfig = TypeVar("TParserConfig", bound=ParserConfigBase)


class ParserBase(
    RegistrableComponent,
    LoopBatchMixin[SourceDocument, IntermediateRepresentation],
    ABC,
    Generic[TParserConfig],
):
    """统一解析器接口。"""

    config: TParserConfig
    single_method_name: str = "parse"

    def __init__(self, config: Optional[TParserConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TParserConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def parse(
        self, document: SourceDocument, ctx: RunContext
    ) -> IntermediateRepresentation:
        """解析文档，输出 IR。"""
        raise NotImplementedError

    def parse_batch(
        self, documents: Iterable[SourceDocument], ctx: RunContext
    ) -> List[IntermediateRepresentation]:
        """批量解析文档，默认循环调用 parse。"""
        return self.batch_run(documents, ctx)
