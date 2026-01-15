"""
适配器实现集合。
"""

from tc_datasynth.pipeline.adapters.implements.mock_pdf import MockPdfAdapter
from tc_datasynth.pipeline.adapters.implements.mock_word import MockWordAdapter

__all__ = ["MockPdfAdapter", "MockWordAdapter"]
