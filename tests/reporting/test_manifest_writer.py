from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tc_datasynth.core.plan import PlanConfig
from tc_datasynth.reporting import write_stage_manifests


class ManifestWriterTest(unittest.TestCase):
    """阶段 manifest 输出测试。"""

    def test_write_stage_manifests_creates_stage_index_files(self) -> None:
        """应为每个阶段写出独立的 manifest 文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_paths = write_stage_manifests(
                output_dir,
                {
                    "parser": [
                        {
                            "doc_id": "doc1",
                            "parsed_doc_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                            "source_doc_name": "paper-a",
                            "source_file_name": "paper-a.pdf",
                            "artifact_path": "/tmp/doc1.txt",
                            "exists": False,
                        }
                    ],
                    "sampler": [
                        {
                            "doc_id": "doc1",
                            "artifact_path": "/tmp/doc1_chunks.jsonl",
                            "exists": False,
                        }
                    ],
                },
            )

            self.assertEqual(set(manifest_paths.keys()), {"parser", "sampler"})
            self.assertTrue(manifest_paths["parser"].exists())
            payload = json.loads(manifest_paths["parser"].read_text(encoding="utf-8"))
            self.assertEqual(payload["stage"], "parser")
            self.assertEqual(payload["entry_count"], 1)
            self.assertEqual(payload["entries"][0]["doc_id"], "doc1")
            self.assertTrue(Path(payload["entries"][0]["artifact_path"]).is_absolute())
            self.assertEqual(len(payload["doc_id_mapping"]), 1)
            self.assertEqual(
                payload["doc_id_mapping"][0]["parsed_doc_id"],
                "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            )
            self.assertEqual(payload["doc_id_mapping"][0]["source_doc_name"], "paper-a")
            self.assertTrue(
                Path(payload["doc_id_mapping"][0]["artifact_path"]).is_absolute()
            )

    def test_write_stage_manifests_enriches_planner_summary(self) -> None:
        """planner manifest 应包含 targets、summary 及 count/ratio 双写。"""
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_paths = write_stage_manifests(
                output_dir,
                {
                    "planner": [
                        {
                            "doc_id": "doc1",
                            "parsed_doc_id": "p1",
                            "record_count": 4,
                            "eligible_count": 3,
                            "skipped_count": 1,
                            "difficulty_distribution": {"easy": 1, "medium": 1, "hard": 1},
                            "question_type_distribution": {"definition": 2, "reasoning": 1},
                            "artifact_path": "/tmp/plans.jsonl",
                        },
                        {
                            "doc_id": "doc2",
                            "parsed_doc_id": "p2",
                            "record_count": 2,
                            "eligible_count": 2,
                            "skipped_count": 0,
                            "difficulty_distribution": {"medium": 1, "hard": 1},
                            "question_type_distribution": {"factual": 1, "definition": 1},
                            "artifact_path": "/tmp/plans.jsonl",
                        },
                    ]
                },
                plan=PlanConfig(
                    difficulty_profile={"easy": 0.2, "medium": 0.4, "hard": 0.4},
                    question_type_mix={"definition": 0.5, "factual": 0.2, "reasoning": 0.3},
                    min_evidence_len=80,
                ),
            )

            payload = json.loads(manifest_paths["planner"].read_text(encoding="utf-8"))
            self.assertEqual(payload["stage"], "planner")
            self.assertEqual(payload["targets"]["min_evidence_len"], 80)
            self.assertEqual(payload["summary"]["planned_count"], 6)
            self.assertEqual(payload["summary"]["eligible_count"], 5)
            self.assertEqual(payload["summary"]["skipped_count"], 1)
            self.assertEqual(
                payload["summary"]["difficulty_distribution"]["count"],
                {"easy": 1, "medium": 2, "hard": 2},
            )
            self.assertEqual(
                payload["summary"]["question_type_distribution"]["count"],
                {"definition": 3, "reasoning": 1, "factual": 1},
            )
            self.assertAlmostEqual(
                payload["summary"]["difficulty_distribution"]["ratio"]["medium"],
                0.4,
            )
            self.assertIn("count", payload["entries"][0]["difficulty_distribution"])
            self.assertIn("ratio", payload["entries"][0]["difficulty_distribution"])

    def test_write_stage_manifests_enriches_gate_summary(self) -> None:
        """gate manifest 应汇总 accepted/rejected/error_distribution。"""
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            manifest_paths = write_stage_manifests(
                output_dir,
                {
                    "gate": [
                        {
                            "doc_id": "doc1",
                            "accepted_count": 2,
                            "rejected_count": 1,
                            "error_distribution": {"evidence.too_short": 1},
                        },
                        {
                            "doc_id": "doc2",
                            "accepted_count": 1,
                            "rejected_count": 2,
                            "error_distribution": {
                                "evidence.too_short": 1,
                                "label.invalid_difficulty": 1,
                            },
                        },
                    ]
                },
            )

            payload = json.loads(manifest_paths["gate"].read_text(encoding="utf-8"))
            self.assertEqual(payload["stage"], "gate")
            self.assertEqual(payload["summary"]["accepted_count"], 3)
            self.assertEqual(payload["summary"]["rejected_count"], 3)
            self.assertEqual(
                payload["summary"]["error_distribution"],
                {
                    "evidence.too_short": 2,
                    "label.invalid_difficulty": 1,
                },
            )
