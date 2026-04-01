from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import requests

from tc_datasynth.core import RuntimeConfig
from tc_datasynth.service import DataSynthService


def _mineru_service_available() -> bool:
    try:
        response = requests.get("http://127.0.0.1:8000/health", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


class RealPdfGpuParserSmokeTest(unittest.TestCase):
    """真实 MinerU HTTP 服务解析链路冒烟测试。"""

    @unittest.skipUnless(_mineru_service_available(), "MinerU HTTP 服务不可用")
    def test_real_pdf_gpu_parser_pipeline_smoke(self) -> None:
        """real 模式下应使用 pdf_gpu 解析器跑通主流程。"""
        fixture = Path("tests/fixtures/advs.202415937.pdf")
        if not fixture.exists():
            self.skipTest("缺少测试 PDF: tests/fixtures/advs.202415937.pdf")

        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            input_dir = base_dir / "in"
            output_dir = base_dir / "out"
            temp_root = base_dir / "temp"
            input_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fixture, input_dir / fixture.name)

            config = RuntimeConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                mode="real",
                doc_limit=1,
                log_level="INFO",
                temp_root_base=temp_root,
                components={
                    "adapter": {
                        "pdf": {
                            "name": "pdf_gpu",
                            "server_url": "http://127.0.0.1:8000",
                        }
                    },
                    "generator": {"name": "mock"},
                },
            )
            config.ensure_output_dir()

            service = DataSynthService(config=config)
            artifacts = service.run_sync(doc_limit=1)

            self.assertTrue(artifacts.final_qa_path.exists())
            self.assertGreater(artifacts.qa_count, 0)

            parser_manifest = artifacts.output_dir / "manifests" / "parser.json"
            self.assertTrue(parser_manifest.exists())
            payload = json.loads(parser_manifest.read_text(encoding="utf-8"))
            entry = payload["entries"][0]

            self.assertEqual(entry["adapter"], "pdf_gpu")
            self.assertTrue(entry["exists"])
            self.assertEqual(len(entry["parsed_doc_id"]), 32)
            self.assertIn("/parser/", entry["artifact_path"])
            self.assertGreaterEqual(int(entry["attempt_count"]), 1)
            self.assertIn("/parser/attempts.jsonl", entry["attempts_path"])
            self.assertEqual(len(payload["doc_id_mapping"]), 1)
            self.assertEqual(
                payload["doc_id_mapping"][0]["parsed_doc_id"],
                entry["parsed_doc_id"],
            )
