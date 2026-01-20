from __future__ import annotations

from tc_datasynth.core.models import DocumentChunk

"""
简单块过滤器。
"""

from tc_datasynth.pipeline.enhance.filter.base import (
    ChunkFilterBase,
    ChunkFilterConfigBase,
)


class SimpleChunkFilter(ChunkFilterBase[ChunkFilterConfigBase]):
    """按指定标记掐头去尾的文本过滤器。"""

    @classmethod
    def default_config(cls) -> ChunkFilterConfigBase:
        return ChunkFilterConfigBase()

    def _apply(self, chunk: DocumentChunk) -> bool:
        pass
        return True  # 简单块过滤器暂不实现具体逻辑
