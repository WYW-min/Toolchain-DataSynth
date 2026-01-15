from __future__ import annotations

"""
最小实现：调用适配器并读取文本文件生成 IR。
"""

from dataclasses import dataclass

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation, SourceDocument
from tc_datasynth.pipeline.adapters import AdapterResult
from tc_datasynth.pipeline.parser.base import AdapterRegistry, ParserBase, ParserConfigBase


@dataclass(slots=True)
class SimpleParserConfig(ParserConfigBase):
    """Simple 解析器配置。"""

    pass


class SimpleUnifiedParser(ParserBase[SimpleParserConfig]):
    """最小统一解析器实现。"""

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

    def parse(self, document: SourceDocument, ctx: RunContext) -> IntermediateRepresentation:
        """解析文档，读取适配器产出的文本文件生成 IR。"""
        adapter = self.registry.resolve(document)
        result: AdapterResult = adapter.parse(document, ctx)
        text = result.text_path.read_text(encoding=self.config.encoding)
        return IntermediateRepresentation(
            doc_id=result.doc_id,
            text=text,
            sections=[result.doc_id],
            metadata={
                "adapter": result.adapter_name,
                "text_path": str(result.text_path),
                "workdir": str(result.workdir),
                **result.metadata,
            },
        )
