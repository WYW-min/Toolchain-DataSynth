from __future__ import annotations

"""
Word Mock 适配器：占位实现，生成简单文本文件。
"""

from pathlib import Path
import hashlib

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult


class MockWordAdapter(DocumentAdapter[AdapterConfigBase]):
    """W1 占位：基于文件名拼接文本，模拟 Word 解析结果。"""

    component_name = "mock_word"

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        """返回默认配置。"""
        return AdapterConfigBase()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """解析单个 Word（mock），输出中间文本路径。"""
        basename = Path(document.path).name
        workdir = ctx.workdir_for(subdir=self.config.output_subdir)
        content = f"[mock word] {basename}"
        content_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
        text_path = workdir / f"{document.path.stem}__{content_md5[:8]}.txt"
        text_path.write_text(content, encoding="utf-8")
        return AdapterResult(
            doc_id=content_md5,
            adapter_name="mock_word",
            workdir=workdir,
            text_path=text_path,
            table_files=[],
            image_files=[],
            metadata={
                "mock_type": "word",
                "parsed_text_md5": content_md5,
                "source_doc_name": document.path.stem,
                "source_file_name": basename,
                "source_path": str(document.path),
                **document.metadata,
            },
        )
