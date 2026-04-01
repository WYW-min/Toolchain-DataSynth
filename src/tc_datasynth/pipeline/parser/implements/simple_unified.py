from __future__ import annotations

"""
最小实现：调用适配器并读取文本文件生成 IR。
"""

from dataclasses import dataclass

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation, SourceDocument
from tc_datasynth.pipeline.parser.base import (
    AdapterRegistry,
    ParserBase,
    ParserConfigBase,
)
from tc_datasynth.pipeline.parser.implements.unified_support import parse_document_to_ir


@dataclass(slots=True)
class SimpleParserConfig(ParserConfigBase):
    """Simple 解析器配置。"""

    pass


class SimpleUnifiedParser(ParserBase[SimpleParserConfig]):
    """最小统一解析器实现。"""

    component_name = "simple_unified"

    def __init__(
        self,
        registry: AdapterRegistry,
        config: SimpleParserConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.registry = registry

    @classmethod
    def default_config(cls) -> SimpleParserConfig:
        """返回默认配置。"""
        return SimpleParserConfig()

    def parse(
        self, document: SourceDocument, ctx: RunContext
    ) -> IntermediateRepresentation:
        """解析文档，读取适配器产出的文本文件生成 IR。"""
        return parse_document_to_ir(
            self.registry,
            document,
            ctx,
            encoding=self.config.encoding,
        )
