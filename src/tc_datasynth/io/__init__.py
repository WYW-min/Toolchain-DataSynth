"""IO 辅助工具（落盘等）。"""

from tc_datasynth.io.reader import ReaderBase, ReaderConfigBase, SimpleDocumentReader, SimpleReaderConfig
from tc_datasynth.io.writer import SimpleQAWriter, SimpleWriterConfig, WriterBase, WriterConfigBase

__all__ = [
    "ReaderBase",
    "ReaderConfigBase",
    "SimpleReaderConfig",
    "SimpleDocumentReader",
    "WriterBase",
    "WriterConfigBase",
    "SimpleWriterConfig",
    "SimpleQAWriter",
]
