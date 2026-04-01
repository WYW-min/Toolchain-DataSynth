"""
适配器实现集合。
"""

from tc_datasynth.pipeline.adapter.implements.mock_pdf import MockPdfAdapter
from tc_datasynth.pipeline.adapter.implements.mock_word import MockWordAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_cpu import PdfCpuAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_gpu import (
    MineruParseOptions,
    PdfGpuAdapter,
    PdfGpuAdapterConfig,
)

__all__ = [
    "MockPdfAdapter",
    "MockWordAdapter",
    "PdfCpuAdapter",
    "MineruParseOptions",
    "PdfGpuAdapter",
    "PdfGpuAdapterConfig",
]
