from __future__ import annotations

import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tc_datasynth.core import RuntimeConfig
from tc_datasynth.core.spec import SpecConfig
from tc_datasynth.service import DataSynthService


class PlannerPipelineSmokeTest(unittest.TestCase):
    """planner 接入主流程的冒烟测试。"""

    def test_planner_distribution_flows_into_mock_generator(self) -> None:
        """mock 主流程应按 planner 分配输出目标分布。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            input_dir = base_dir / "in"
            output_dir = base_dir / "out"
            temp_root = base_dir / "temp"
            input_dir.mkdir(parents=True, exist_ok=True)
            for idx in range(10):
                (input_dir / f"sample-{idx + 1}.pdf").write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                mode="mock",
                doc_limit=10,
                log_level="INFO",
                temp_root_base=temp_root,
                components={"generator": {"name": "mock", "questions_per_doc": 1}},
                spec=SpecConfig(
                    difficulty_profile={"easy": 0.2, "medium": 0.3, "hard": 0.5},
                    question_type_mix={"definition": 0.5, "factual": 0.3, "reasoning": 0.2},
                    min_evidence_len=1,
                ),
            )
            config.ensure_output_dir()

            service = DataSynthService(config=config)
            artifacts = service.run_sync(doc_limit=10)

            self.assertTrue(artifacts.final_qa_path.exists())
            records = [
                json.loads(line)
                for line in artifacts.final_qa_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(records), 10)
            self.assertEqual(
                Counter(
                    record["qa_info"]["labels"]["difficulty"] for record in records
                ),
                Counter({"easy": 2, "medium": 3, "hard": 5}),
            )
            self.assertEqual(
                Counter(
                    record["qa_info"]["labels"]["question_type"] for record in records
                ),
                Counter({"definition": 5, "factual": 3, "reasoning": 2}),
            )
            self.assertTrue(
                all(record["provenance"]["planner"] == "simple" for record in records)
            )
            self.assertTrue(all("qa_id" in record for record in records))
            planner_manifest = artifacts.output_dir / "manifests" / "planner.json"
            self.assertTrue(planner_manifest.exists())
            planner_payload = json.loads(planner_manifest.read_text(encoding="utf-8"))
            self.assertIn("targets", planner_payload)
            self.assertIn("summary", planner_payload)
            self.assertEqual(planner_payload["summary"]["eligible_count"], 10)
            plans_path = temp_root / artifacts.run_id / "planner" / "plans.jsonl"
            self.assertTrue(plans_path.exists())
            plan_rows = [
                json.loads(line)
                for line in plans_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(plan_rows), 10)
            self.assertIn("chunk_id", plan_rows[0])
            self.assertIn("system_meta", plan_rows[0])
            self.assertIn("prompt_meta", plan_rows[0])
