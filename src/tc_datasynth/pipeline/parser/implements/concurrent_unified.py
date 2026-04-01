from __future__ import annotations

"""
并发统一解析器：保留单文档解析逻辑，在 batch 维度做线程池调度。
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable, List

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation, SourceDocument
from tc_datasynth.pipeline.parser.base import (
    AdapterRegistry,
    ParserBase,
    ParserConfigBase,
)
from tc_datasynth.pipeline.parser.implements.unified_support import parse_document_to_ir


@dataclass(slots=True)
class ConcurrentParserConfig(ParserConfigBase):
    """并发统一解析器配置。"""

    max_workers: int = 2


class ConcurrentUnifiedParser(ParserBase[ConcurrentParserConfig]):
    """基于线程池的并发统一解析器。"""

    component_name = "concurrent_unified"

    def __init__(
        self,
        registry: AdapterRegistry,
        config: ConcurrentParserConfig | None = None,
    ) -> None:
        super().__init__(config)
        self.registry = registry

    @classmethod
    def default_config(cls) -> ConcurrentParserConfig:
        """返回默认配置。"""
        return ConcurrentParserConfig()

    def parse(
        self, document: SourceDocument, ctx: RunContext
    ) -> IntermediateRepresentation:
        """单文档解析逻辑与 simple_unified 保持一致。"""
        return parse_document_to_ir(
            self.registry,
            document,
            ctx,
            encoding=self.config.encoding,
        )

    def parse_batch(
        self, documents: Iterable[SourceDocument], ctx: RunContext
    ) -> List[IntermediateRepresentation]:
        """批量解析时以线程池并发执行，并保持输出顺序。"""
        items = list(documents)
        if not items:
            return []
        if self.config.max_workers <= 1 or len(items) <= 1:
            return [self.parse(item, ctx) for item in items]

        max_workers = min(self.config.max_workers, len(items))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(lambda item: self.parse(item, ctx), items))
