"""
适配器集合：负责把各类原始输入转为统一中间产物。
"""

from tc_datasynth.pipeline.adapters.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapters.implements import MockPdfAdapter, MockWordAdapter
from tc_datasynth.pipeline.adapters.types import AdapterResult

__all__ = [
    "AdapterConfigBase",
    "DocumentAdapter",
    "AdapterResult",
    "MockPdfAdapter",
    "MockWordAdapter",
]
