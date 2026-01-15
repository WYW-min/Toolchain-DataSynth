from __future__ import annotations

"""
冒烟测试：验证 mock 流程端到端可跑通。
"""

import tempfile
import unittest
from pathlib import Path

from tc_datasynth.core import RuntimeConfig
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
                max_docs=1,
                log_level="INFO",
                temp_root_base=temp_root,
            )
            config.ensure_output_dir()

            service = DataSynthService(config=config)
            artifacts = service.run_sync(limit=1)

            self.assertTrue(artifacts.final_qa_path.exists())
            self.assertTrue(artifacts.report_path.exists())
            self.assertGreater(artifacts.qa_count, 0)

            content = artifacts.final_qa_path.read_text(encoding="utf-8").strip()
            self.assertTrue(content)
