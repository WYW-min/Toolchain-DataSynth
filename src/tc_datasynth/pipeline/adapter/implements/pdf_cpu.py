"""
PDF CPU 适配器：基于文件名生成可预测的文本文件。
"""

import hashlib

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult
from markitdown import MarkItDown


class PdfCpuAdapter(DocumentAdapter[AdapterConfigBase]):
    """W2 使用的 CPU PDF 解析器"""

    def __init__(self):
        self.md_parser = MarkItDown(enable_plugins=False)  # 外置依赖，实现了convert接口

        super().__init__()

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        """返回默认配置。"""
        return AdapterConfigBase()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """解析单个 PDF（mock）并写入，输出写入的中间文本路径。"""
        content = self.md_parser.convert(document.path)
        if not isinstance(content, str):
            content = content.text_content
        text_path = ctx.temp_root / f"{document.doc_id}.md"

        text_path.write_text(content, encoding="utf-8")
        content_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()

        return AdapterResult(
            doc_id=document.doc_id,
            adapter_name="pdf_cpu",
            workdir=ctx.temp_root,
            text_path=text_path,
            table_files=[],
            image_files=[],
            metadata={"md5": content_md5, **document.metadata},
        )
