from __future__ import annotations

"""
Word Mock 适配器：占位实现，生成简单文本文件。
"""

from pathlib import Path

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapters.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapters.types import AdapterResult


class MockWordAdapter(DocumentAdapter[AdapterConfigBase]):
    """W1 占位：基于文件名拼接文本，模拟 Word 解析结果。"""

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        """返回默认配置。"""
        return AdapterConfigBase()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """解析单个 Word（mock），输出中间文本路径。"""
        basename = Path(document.path).name
        workdir = ctx.workdir_for(document.doc_id, subdir=self.config.output_subdir)
        text_path = workdir / f"{document.path.stem}.txt"
        content = f"[mock word] {basename}"
        text_path.write_text(content, encoding="utf-8")
        return AdapterResult(
            doc_id=document.path.stem,
            adapter_name="mock_word",
            workdir=workdir,
            text_path=text_path,
            table_files=[],
            image_files=[],
            metadata={"mock_type": "word", **document.metadata},
        )
