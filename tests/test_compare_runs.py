from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tc_datasynth.tools.compare_runs import (
    format_comparison_table,
    main,
    resolve_report_path,
    summarize_run,
)


class CompareRunsToolTest(unittest.TestCase):
    """run 对比工具测试。"""

    def test_resolve_report_path_accepts_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_dir = Path(tmp_dir) / "20260330-120000"
            run_dir.mkdir(parents=True, exist_ok=True)
            self.assertEqual(resolve_report_path(str(run_dir)), run_dir / "report.json")

    def test_summarize_run_reads_generator_attempt_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            manifests_dir = base_dir / "manifests"
            manifests_dir.mkdir(parents=True, exist_ok=True)
            generator_manifest = manifests_dir / "generator.json"
            generator_manifest.write_text(
                json.dumps(
                    {
                        "stage": "generator",
                        "entries": [
                            {"backend": "concurrent_qa", "attempt_count": 3},
                            {"backend": "concurrent_qa", "attempt_count": 2},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = {
                "run_id": "run-a",
                "summary": {
                    "documents_processed": 2,
                    "qa_count": 4,
                    "failed_count": 1,
                    "pass_rate": 0.8,
                    "runtime_seconds": 12.5,
                },
                "final_distribution": {
                    "difficulty": {"easy": 1, "medium": 3},
                    "question_type": {"definition": 2, "reasoning": 2},
                },
                "artifacts": {
                    "manifests": {
                        "generator": str(generator_manifest),
                    }
                },
            }

            summary = summarize_run(report)

            self.assertEqual(summary["generator"], "concurrent_qa")
            self.assertEqual(summary["attempt_count"], 5)
            self.assertEqual(summary["avg_attempts_per_qa"], 1.25)
            self.assertEqual(summary["runtime_seconds"], 12.5)

    def test_format_and_main_output_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            left_dir = _write_run(base_dir / "left", "run-left", "simple_qa", 0, 2)
            right_dir = _write_run(
                base_dir / "right",
                "run-right",
                "concurrent_qa",
                3,
                2,
            )

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = main(
                    [
                        "--left",
                        str(left_dir),
                        "--right",
                        str(right_dir),
                        "--left-label",
                        "simple",
                        "--right-label",
                        "concurrent",
                    ]
                )

            text = output.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("metric", text)
            self.assertIn("attempt_count", text)
            self.assertIn("runtime_seconds", text)
            self.assertIn("simple_qa", text)
            self.assertIn("concurrent_qa", text)


def _write_run(
    run_dir: Path,
    run_id: str,
    backend: str,
    attempt_count: int,
    qa_count: int,
) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir = run_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    generator_manifest = manifests_dir / "generator.json"
    generator_manifest.write_text(
        json.dumps(
            {
                "stage": "generator",
                "entries": [
                    {"backend": backend, "attempt_count": attempt_count},
                ],
            }
        ),
        encoding="utf-8",
    )
    report = {
        "run_id": run_id,
        "summary": {
            "documents_processed": 1,
            "qa_count": qa_count,
            "failed_count": 0,
            "pass_rate": 1.0,
            "runtime_seconds": 1.234,
        },
        "final_distribution": {
            "difficulty": {"easy": qa_count},
            "question_type": {"definition": qa_count},
        },
        "artifacts": {
            "manifests": {
                "generator": str(generator_manifest),
            }
        },
    }
    (run_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False),
        encoding="utf-8",
    )
    return run_dir
