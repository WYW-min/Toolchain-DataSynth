"""
PDF CPU 适配器：基于文件名生成可预测的文本文件。
"""

import hashlib
from pathlib import Path

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult
from markitdown import MarkItDown


class PdfGpuAdapter(DocumentAdapter[AdapterConfigBase]):
    """W2 使用的 GPU PDF 解析器"""

    def __init__(self):
        self.md_parser = MarkItDown(enable_plugins=False)  # 外置依赖，实现了convert接口

        super().__init__()

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        """返回默认配置。"""
        return AdapterConfigBase()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """解析单个 PDF（mock）并写入，输出写入的中间文本路径。"""
        ...
        return AdapterResult(
            doc_id=document.path.stem,
            adapter_name="pdf_gpu",
            workdir=None,
            text_path=None,
            table_files=[],
            image_files=[],
            metadata={"md5": None, **document.metadata},
        )
