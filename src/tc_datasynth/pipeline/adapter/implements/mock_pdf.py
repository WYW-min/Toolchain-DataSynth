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

    component_name = "mock_pdf"

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        """返回默认配置。"""
        return AdapterConfigBase()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """解析单个 PDF（mock），输出中间文本路径。"""
        basename = Path(document.path).name
        workdir = ctx.workdir_for(subdir=self.config.output_subdir)
        digest = hashlib.sha1(basename.encode("utf-8")).hexdigest()[:8]
        content = f"[mock pdf] {basename} (digest={digest})"
        content_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
        text_path = workdir / f"{document.path.stem}__{content_md5[:8]}.txt"
        text_path.write_text(content, encoding="utf-8")
        return AdapterResult(
            doc_id=content_md5,
            adapter_name="mock_pdf",
            workdir=workdir,
            text_path=text_path,
            table_files=[],
            image_files=[],
            metadata={
                "mock_digest": digest,
                "parsed_text_md5": content_md5,
                "source_doc_name": document.path.stem,
                "source_file_name": basename,
                "source_path": str(document.path),
                **document.metadata,
            },
        )
