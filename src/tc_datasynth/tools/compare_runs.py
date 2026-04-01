from __future__ import annotations

"""
对比两个 run 目录/报告，汇总关键指标与 generator attempts 信息。
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def resolve_report_path(path_text: str) -> Path:
    """接受 run 目录或 report.json 路径，统一解析成 report.json。"""
    path = Path(path_text).expanduser().resolve(strict=False)
    if path.is_dir():
        return path / "report.json"
    return path


def load_json(path: Path) -> Dict[str, Any]:
    """读取 JSON 文件。"""
    return json.loads(path.read_text(encoding="utf-8"))


def load_generator_manifest(report: Dict[str, Any]) -> Dict[str, Any]:
    """根据 report 中的 manifest 路径加载 generator manifest。"""
    manifest_path = (
        report.get("artifacts", {})
        .get("manifests", {})
        .get("generator")
    )
    if not manifest_path:
        return {}
    path = Path(str(manifest_path)).expanduser().resolve(strict=False)
    if not path.exists():
        return {}
    return load_json(path)


def summarize_run(report: Dict[str, Any]) -> Dict[str, Any]:
    """从 report/generator manifest 中提取关键对比指标。"""
    summary = dict(report.get("summary", {}))
    generator_manifest = load_generator_manifest(report)
    generator_entries = generator_manifest.get("entries", [])
    attempt_count = 0
    backend = None
    if isinstance(generator_entries, list):
        for entry in generator_entries:
            if not isinstance(entry, dict):
                continue
            attempt_count += int(entry.get("attempt_count") or 0)
            if backend is None and entry.get("backend"):
                backend = str(entry.get("backend"))
    qa_count = int(summary.get("qa_count") or 0)
    return {
        "run_id": report.get("run_id"),
        "generator": backend,
        "documents_processed": int(summary.get("documents_processed") or 0),
        "qa_count": qa_count,
        "failed_count": int(summary.get("failed_count") or 0),
        "pass_rate": float(summary.get("pass_rate") or 0.0),
        "runtime_seconds": float(summary.get("runtime_seconds") or 0.0),
        "attempt_count": attempt_count,
        "avg_attempts_per_qa": round(attempt_count / qa_count, 4) if qa_count > 0 else 0.0,
        "difficulty_distribution": (
            report.get("final_distribution", {}).get("difficulty", {})
        ),
        "question_type_distribution": (
            report.get("final_distribution", {}).get("question_type", {})
        ),
    }


def render_value(value: Any) -> str:
    """渲染单元格内容。"""
    if isinstance(value, dict):
        if not value:
            return "{}"
        return ", ".join(f"{key}={value[key]}" for key in sorted(value))
    return str(value)


def format_comparison_table(
    left_label: str,
    left_summary: Dict[str, Any],
    right_label: str,
    right_summary: Dict[str, Any],
) -> str:
    """输出人类可读的对比表。"""
    metrics = [
        "run_id",
        "generator",
        "documents_processed",
        "qa_count",
        "failed_count",
        "pass_rate",
        "runtime_seconds",
        "attempt_count",
        "avg_attempts_per_qa",
        "difficulty_distribution",
        "question_type_distribution",
    ]
    rows = [
        (
            metric,
            render_value(left_summary.get(metric)),
            render_value(right_summary.get(metric)),
        )
        for metric in metrics
    ]
    metric_width = max(len("metric"), *(len(row[0]) for row in rows))
    left_width = max(len(left_label), *(len(row[1]) for row in rows))
    right_width = max(len(right_label), *(len(row[2]) for row in rows))
    lines = [
        f"{'metric':<{metric_width}} | {left_label:<{left_width}} | {right_label:<{right_width}}",
        f"{'-' * metric_width}-+-{'-' * left_width}-+-{'-' * right_width}",
    ]
    for metric, left_value, right_value in rows:
        lines.append(
            f"{metric:<{metric_width}} | {left_value:<{left_width}} | {right_value:<{right_width}}"
        )
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    """构造命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        description="Compare two TC-DataSynth runs by report/manifests."
    )
    parser.add_argument("--left", required=True, help="Left run directory or report.json")
    parser.add_argument("--right", required=True, help="Right run directory or report.json")
    parser.add_argument("--left-label", default="left", help="Display label for left run")
    parser.add_argument("--right-label", default="right", help="Display label for right run")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print structured JSON instead of human-readable table",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """命令行入口。"""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    left_report = load_json(resolve_report_path(args.left))
    right_report = load_json(resolve_report_path(args.right))
    left_summary = summarize_run(left_report)
    right_summary = summarize_run(right_report)

    if args.json:
        payload = {
            args.left_label: left_summary,
            args.right_label: right_summary,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            format_comparison_table(
                args.left_label,
                left_summary,
                args.right_label,
                right_summary,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
