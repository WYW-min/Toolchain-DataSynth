from __future__ import annotations

"""
QA 生成器接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Iterable, List, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk, QAPair
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


@dataclass(slots=True)
class GeneratorConfigBase:
    """生成器基础配置。"""

    seed: int = 0


TGeneratorConfig = TypeVar("TGeneratorConfig", bound=GeneratorConfigBase)


class QAGeneratorBase(
    LoopBatchMixin[List[DocumentChunk], List[QAPair]], ABC, Generic[TGeneratorConfig]
):
    """QA 生成器接口。"""

    config: TGeneratorConfig
    single_method_name: str = "generate"

    def __init__(self, config: TGeneratorConfig | None = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TGeneratorConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self, chunks: Iterable[DocumentChunk], ctx: RunContext
    ) -> List[QAPair]:
        """基于 chunk 生成 QA 列表。"""
        raise NotImplementedError

    def generate_batch(
        self, batch_chunks: Iterable[Iterable[DocumentChunk]], ctx: RunContext
    ) -> List[List[QAPair]]:
        """批量生成 QA，默认循环调用 generate。"""
        return self.batch_run(batch_chunks, ctx)
