from __future__ import annotations

"""
冒烟测试：验证 mock 流程端到端可跑通。
"""

import tempfile
import unittest
import json
from pathlib import Path

from tc_datasynth.core import RuntimeConfig
from tc_datasynth.core.spec import SpecConfig
from tc_datasynth.service import DataSynthService


class MockPipelineSmokeTest(unittest.TestCase):
    """mock 流程冒烟测试。"""

    def test_mock_pipeline_smoke(self) -> None:
        """最小输入下确保产物与统计生成。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            input_dir = base_dir / "in"
            output_dir = base_dir / "out"
            temp_root = base_dir / "temp"
            input_dir.mkdir(parents=True, exist_ok=True)
            (input_dir / "sample.pdf").write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                mode="mock",
                doc_limit=1,
                log_level="INFO",
                temp_root_base=temp_root,
                spec=SpecConfig(min_evidence_len=1),
            )
            config.ensure_output_dir()

            service = DataSynthService(config=config)
            artifacts = service.run_sync(doc_limit=1)

            self.assertTrue(artifacts.final_qa_path.exists())
            self.assertTrue(artifacts.report_path.exists())
            self.assertGreater(artifacts.qa_count, 0)

            content = artifacts.final_qa_path.read_text(encoding="utf-8").strip()
            self.assertTrue(content)
            report = json.loads(artifacts.report_path.read_text(encoding="utf-8"))
            self.assertIn("summary", report)
            self.assertIn("final_distribution", report)
            self.assertIn("gate", report)
            self.assertIn("quality", report)
            self.assertIn("failure_backlog", report)
            manifests_dir = artifacts.output_dir / "manifests"
            self.assertTrue(manifests_dir.exists())
            self.assertTrue((manifests_dir / "parser.json").exists())
            self.assertTrue((manifests_dir / "sampler.json").exists())
            self.assertTrue((manifests_dir / "gate.json").exists())

    def test_mock_pipeline_respects_qa_limit(self) -> None:
        """limit=2 时最终 QA 数量应被截断到 2。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            input_dir = base_dir / "in"
            output_dir = base_dir / "out"
            temp_root = base_dir / "temp"
            input_dir.mkdir(parents=True, exist_ok=True)
            for idx in range(3):
                (input_dir / f"sample-{idx + 1}.pdf").write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                mode="mock",
                doc_limit=3,
                limit=2,
                log_level="INFO",
                temp_root_base=temp_root,
                components={"generator": {"name": "mock", "questions_per_doc": 3}},
            )
            config.ensure_output_dir()

            service = DataSynthService(config=config)
            artifacts = service.run_sync(doc_limit=3)

            self.assertEqual(artifacts.qa_count, 2)
            records = [
                json.loads(line)
                for line in artifacts.final_qa_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(records), 2)
