from __future__ import annotations

"""
过滤器基类定义：文本级与块级过滤。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.models import DocumentChunk
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


@dataclass(slots=True)
class TextFilterConfigBase:
    """文本过滤器基础配置。"""

    pass


@dataclass(slots=True)
class ChunkFilterConfigBase:
    """块级过滤器基础配置。"""

    pass


TTextFilterConfig = TypeVar("TTextFilterConfig", bound=TextFilterConfigBase)
TChunkFilterConfig = TypeVar("TChunkFilterConfig", bound=ChunkFilterConfigBase)
TFilterConfig = TypeVar("TFilterConfig")
TFilterIn = TypeVar("TFilterIn")
TFilterOut = TypeVar("TFilterOut")


class FilterBase(
    LoopBatchMixin[TFilterIn, TFilterOut],
    ABC,
    Generic[TFilterConfig, TFilterIn, TFilterOut],
):
    """通用过滤器基类。"""

    config: TFilterConfig
    single_method_name: str = "_apply"

    def __init__(self, config: Optional[TFilterConfig] = None) -> None:
        """初始化过滤器，可传入配置。"""
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TFilterConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def _apply(self, item: TFilterIn) -> TFilterOut:
        """应用过滤逻辑。"""
        raise NotImplementedError

    @abstractmethod
    def filter(
        self, items: Iterable[TFilterIn] | TFilterIn
    ) -> Iterable[TFilterOut] | TFilterOut:
        """过滤输入项集合。"""
        raise NotImplementedError

    def apply_batch(self, items: Iterable[TFilterIn]) -> List[TFilterOut]:
        """批量执行过滤逻辑。"""
        return self.batch_run(items)


class TextFilterBase(FilterBase[TTextFilterConfig, str, str], ABC):
    """文本级过滤器基类。"""

    def filter(self, text: str) -> str:

        return self._apply(text)


class ChunkFilterBase(FilterBase[TChunkFilterConfig, DocumentChunk, bool], ABC):
    """块级过滤器基类。"""

    def filter(self, chunks: Iterable[DocumentChunk]) -> Iterable[DocumentChunk]:
        """判断是否保留该块。"""
        return [chunk for chunk in chunks if self._apply(chunk)]
