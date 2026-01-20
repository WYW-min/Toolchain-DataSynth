"""
适配器集合：负责把各类原始输入转为统一中间产物。
"""

from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.implements import MockPdfAdapter, MockWordAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult

__all__ = [
    "AdapterConfigBase",
    "DocumentAdapter",
    "AdapterResult",
    "MockPdfAdapter",
    "MockWordAdapter",
]
