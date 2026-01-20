from __future__ import annotations

"""
PDF Mock 适配器：基于文件名生成可预测的文本文件（W1 占位）。
"""

import hashlib
from pathlib import Path

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult


class MockPdfAdapter(DocumentAdapter[AdapterConfigBase]):
    """W1 使用的 PDF 模拟解析器，不读取真实内容。"""

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        """返回默认配置。"""
        return AdapterConfigBase()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """解析单个 PDF（mock），输出中间文本路径。"""
        basename = Path(document.path).name
        digest = hashlib.sha1(basename.encode("utf-8")).hexdigest()[:8]
        workdir = ctx.workdir_for(subdir=self.config.output_subdir)
        text_path = workdir / f"{document.doc_id}.txt"
        content = f"[mock pdf] {basename} (digest={digest})"
        text_path.write_text(content, encoding="utf-8")
        return AdapterResult(
            doc_id=document.doc_id,
            adapter_name="mock_pdf",
            workdir=workdir,
            text_path=text_path,
            table_files=[],
            image_files=[],
            metadata={"mock_digest": digest, **document.metadata},
        )
