"""
PdfCpuAdapter 单元/集成测试。
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from pprint import pprint

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument

try:
    from tc_datasynth.pipeline.adapter.implements.pdf_cpu import PdfCpuAdapter
except Exception:
    PdfCpuAdapter = None
    MARKITDOWN_AVAILABLE = False
else:
    MARKITDOWN_AVAILABLE = True


class PdfCpuAdapterTest(unittest.TestCase):
    """PDF CPU 适配器单元测试。"""

    @unittest.skipUnless(MARKITDOWN_AVAILABLE, "markitdown 未安装")
    def test_parse_outputs_text_and_metadata(self) -> None:
        """验证输出文件、路径与元数据。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf_path = base / "sample.pdf"
            pdf_path.write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            doc = SourceDocument(
                doc_id=pdf_path.stem, path=pdf_path, metadata={"src": "unit"}
            )

            adapter = PdfCpuAdapter()

            class DummyMdParser:
                def convert(self, p: Path | str) -> str:
                    return "hello world"

            adapter.md_parser = DummyMdParser()

            result = adapter.parse(doc, ctx)

            self.assertEqual(result.doc_id, "sample")
            self.assertEqual(result.adapter_name, "pdf_cpu")
            self.assertTrue(result.workdir.exists())
            self.assertEqual(result.text_path, result.workdir / "sample.md")
            self.assertTrue(result.text_path.exists())
            self.assertEqual(
                result.text_path.read_text(encoding="utf-8"), "hello world"
            )
            self.assertEqual(result.metadata["src"], "unit")
            self.assertEqual(
                result.metadata["md5"],
                hashlib.md5("hello world".encode("utf-8")).hexdigest(),
            )

    @unittest.skipUnless(MARKITDOWN_AVAILABLE, "markitdown 未安装")
    def test_parse_real_pdf_integration(self) -> None:
        """使用真实 PDF 验证解析链路与落盘产物。"""
        fixture = Path("tests/fixtures/advs.202415937.pdf")
        if not fixture.exists():
            self.skipTest("缺少测试 PDF: tests/fixtures/advs.202415937.pdf")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            doc = SourceDocument(doc_id=fixture.stem, path=fixture, metadata={})

            adapter = PdfCpuAdapter()
            result = adapter.parse(doc, ctx)
            pprint(f"解析结果如下：\n{result}")

            self.assertTrue(result.workdir.exists())
            self.assertTrue(result.text_path.exists())
            self.assertGreater(result.text_path.stat().st_size, 0)
            self.assertEqual(result.adapter_name, "pdf_cpu")
            self.assertEqual(result.doc_id, fixture.stem)
            self.assertEqual(result.table_files, [])
            self.assertEqual(result.image_files, [])
            self.assertEqual(len(result.metadata.get("md5", "")), 32)
