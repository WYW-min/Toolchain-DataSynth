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
            expected_md5 = hashlib.md5("hello world".encode("utf-8")).hexdigest()

            self.assertEqual(result.doc_id, expected_md5)
            self.assertEqual(result.adapter_name, "pdf_cpu")
            self.assertTrue(result.workdir.exists())
            self.assertEqual(result.workdir, ctx.workdir_for(subdir="parser"))
            self.assertEqual(result.text_path, result.workdir / f"sample__{expected_md5[:8]}.md")
            self.assertTrue(result.text_path.exists())
            self.assertEqual(
                result.text_path.read_text(encoding="utf-8"), "hello world"
            )
            self.assertEqual(result.metadata["src"], "unit")
            self.assertEqual(result.metadata["md5"], expected_md5)
            self.assertEqual(result.metadata["parsed_text_md5"], expected_md5)
            self.assertEqual(result.metadata["source_doc_name"], "sample")
            self.assertEqual(result.metadata["source_file_name"], "sample.pdf")

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
            self.assertEqual(result.workdir, ctx.workdir_for(subdir="parser"))
            self.assertTrue(result.text_path.parent.samefile(result.workdir))
            self.assertTrue(result.text_path.name.startswith(f"{fixture.stem}__"))
            self.assertEqual(result.table_files, [])
            self.assertEqual(result.image_files, [])
            self.assertEqual(result.doc_id, result.metadata["md5"])
            self.assertEqual(len(result.metadata.get("md5", "")), 32)
