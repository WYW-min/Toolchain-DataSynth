from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tc_datasynth.core.models import QAPair
from tc_datasynth.reporting import write_run_report


class ReportWriterTest(unittest.TestCase):
    """report.json 输出测试。"""

    def test_write_run_report_contains_summary_distribution_and_quality(self) -> None:
        """报告应包含三类核心信息与产物引用。"""
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            final_path = output_dir / "FinalQA.jsonl"
            failed_path = output_dir / "FailedCases.jsonl"
            manifests_dir = output_dir / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            final_path.write_text("", encoding="utf-8")
            failed_path.write_text("", encoding="utf-8")
            (manifests_dir / "parser.json").write_text(
                json.dumps(
                    {
                        "stage": "parser",
                        "entry_count": 1,
                        "entries": [],
                        "doc_id_mapping": [
                            {
                                "doc_id": "paper-a",
                                "parsed_doc_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                                "source_doc_name": "paper-a",
                                "source_file_name": "paper-a.pdf",
                                "artifact_path": "/tmp/paper-a__aaaaaaaa.md",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (manifests_dir / "planner.json").write_text(
                json.dumps(
                    {
                        "stage": "planner",
                        "entry_count": 1,
                        "targets": {
                            "difficulty_profile": {"easy": 0.5, "hard": 0.5},
                            "question_type_mix": {"definition": 0.5, "reasoning": 0.5},
                            "min_evidence_len": 80,
                        },
                        "summary": {
                            "planned_count": 3,
                            "eligible_count": 2,
                            "skipped_count": 1,
                            "difficulty_distribution": {
                                "count": {"easy": 1, "hard": 1},
                                "ratio": {"easy": 0.5, "hard": 0.5},
                            },
                            "question_type_distribution": {
                                "count": {"definition": 1, "reasoning": 1},
                                "ratio": {"definition": 0.5, "reasoning": 0.5},
                            },
                        },
                        "entries": [
                            {
                                "artifact_path": "/tmp/planner/plans.jsonl",
                            }
                        ],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (manifests_dir / "gate.json").write_text(
                json.dumps(
                    {
                        "stage": "gate",
                        "entry_count": 1,
                        "summary": {
                            "accepted_count": 2,
                            "rejected_count": 1,
                            "error_distribution": {"schema.missing_question": 1},
                        },
                        "entries": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            final_records = [
                QAPair(
                    question="What is A?",
                    answer="A is alpha.",
                    evidences=["alpha"],
                    source_doc_id="doc1",
                    chunk_id="c1",
                    metadata={"difficulty": "easy", "question_type": "definition"},
                ),
                QAPair(
                    question="Why is B important?",
                    answer="Because it stabilizes the system.",
                    evidences=["beta", "gamma"],
                    source_doc_id="doc2",
                    chunk_id="c2",
                    metadata={
                        "generator": "simple_qa",
                        "other": {
                            "prompt_meta": {
                                "difficulty": "hard",
                                "question_type": "reasoning",
                            },
                        },
                    },
                ),
            ]
            failed_records = [
                {
                    "qa": {"question": "", "answer": "A"},
                    "errors": ["schema.missing_question"],
                    "stage": "gate",
                    "action": "reject",
                }
            ]

            report_path = write_run_report(
                output_dir=output_dir,
                run_id="run-1",
                doc_count=3,
                final_records=final_records,
                failed_records=failed_records,
                final_path=final_path,
                failed_path=failed_path,
                manifest_paths={
                    "parser": manifests_dir / "parser.json",
                    "planner": manifests_dir / "planner.json",
                    "gate": manifests_dir / "gate.json",
                },
                intermediate_path=Path("/tmp/run-1"),
            )

            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["run_id"], "run-1")
            self.assertEqual(report["summary"]["documents_processed"], 3)
            self.assertEqual(report["summary"]["qa_count"], 2)
            self.assertEqual(report["summary"]["failed_count"], 1)
            self.assertAlmostEqual(report["summary"]["pass_rate"], 0.6667)
            self.assertEqual(report["final_distribution"]["difficulty"]["easy"], 1)
            self.assertEqual(report["final_distribution"]["difficulty"]["hard"], 1)
            self.assertEqual(report["final_distribution"]["question_type"]["definition"], 1)
            self.assertEqual(report["final_distribution"]["question_type"]["reasoning"], 1)
            self.assertEqual(report["planner"]["targets"]["min_evidence_len"], 80)
            self.assertEqual(report["planner"]["summary"]["planned_count"], 3)
            self.assertEqual(report["planner"]["summary"]["eligible_count"], 2)
            self.assertEqual(report["gate"]["accepted_count"], 2)
            self.assertEqual(report["gate"]["rejected_count"], 1)
            self.assertEqual(
                report["gate"]["error_distribution"]["schema.missing_question"],
                1,
            )
            self.assertEqual(report["quality"]["avg_evidence_count"], 1.5)
            self.assertEqual(report["artifacts"]["dataset"], str(final_path.resolve()))
            self.assertEqual(
                report["artifacts"]["failed_cases"], str(failed_path.resolve())
            )
            self.assertEqual(
                report["artifacts"]["intermediate_path"],
                str(Path("/tmp/run-1").resolve()),
            )
            self.assertEqual(
                report["artifacts"]["manifests"]["parser"],
                str((output_dir / "manifests" / "parser.json").resolve()),
            )
            self.assertEqual(
                report["artifacts"]["manifests"]["planner"],
                str((output_dir / "manifests" / "planner.json").resolve()),
            )
            self.assertEqual(
                report["artifacts"]["manifests"]["gate"],
                str((output_dir / "manifests" / "gate.json").resolve()),
            )
            self.assertEqual(
                report["failure_backlog"]["error_distribution"]["schema.missing_question"],
                1,
            )
            self.assertEqual(
                report["doc_map"]["aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"],
                "paper-a.pdf",
            )
            self.assertEqual(list(report.keys())[-1], "doc_map")
