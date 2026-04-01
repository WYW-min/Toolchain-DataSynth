from __future__ import annotations

"""
报告输出：生成运行统计并落盘。
"""

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

from tc_datasynth.core.models import QAPair


def write_run_report(
    output_dir: Path,
    run_id: str,
    doc_count: int,
    final_records: List[QAPair],
    failed_records: List[dict],
    final_path: Path,
    failed_path: Path,
    manifest_paths: Dict[str, Path] | None = None,
    intermediate_path: Path | None = None,
    runtime_seconds: float = 0.0,
) -> Path:
    """生成当前运行的 JSON 报告并返回路径。"""
    difficulty_distribution = _count_label_field(final_records, "difficulty")
    question_type_distribution = _count_label_field(final_records, "question_type")
    summary = {
        "documents_processed": doc_count,
        "qa_count": len(final_records),
        "failed_count": len(failed_records),
        "pass_rate": _compute_pass_rate(len(final_records), len(failed_records)),
        "runtime_seconds": round(runtime_seconds, 4),
    }
    quality = {
        "avg_evidence_count": _average(
            len(record.evidences) for record in final_records
        ),
        "avg_question_length": _average(
            len(record.question.strip()) for record in final_records
        ),
        "avg_answer_length": _average(
            len(record.answer.strip()) for record in final_records
        ),
    }
    failure = {
        "count": len(failed_records),
        "is_placeholder_empty": len(failed_records) == 0,
        "error_distribution": _count_failed_errors(failed_records),
    }
    report = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "summary": summary,
        "final_distribution": {
            "difficulty": difficulty_distribution,
            "question_type": question_type_distribution,
        },
        "planner": _load_planner_summary(manifest_paths or {}),
        "gate": _load_gate_summary(manifest_paths or {}),
        "quality": quality,
        "artifacts": {
            "dataset": str(final_path.resolve()),
            "failed_cases": str(failed_path.resolve()),
            "intermediate_path": (
                str(intermediate_path.resolve())
                if intermediate_path is not None
                else None
            ),
            "manifests": {
                stage: str(path.resolve())
                for stage, path in (manifest_paths or {}).items()
            },
        },
        "failure_backlog": failure,
        "doc_map": _load_doc_map(manifest_paths or {}),
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report_path


def _compute_pass_rate(final_count: int, failed_count: int) -> float:
    """计算通过率。"""
    total = final_count + failed_count
    if total <= 0:
        return 0.0
    return round(final_count / total, 4)


def _average(values: Any) -> float:
    """计算平均值，保留两位小数。"""
    items = list(values)
    if not items:
        return 0.0
    return round(sum(items) / len(items), 2)


def _count_label_field(records: List[QAPair], field_name: str) -> Dict[str, int]:
    """统计指定标签字段分布。"""
    counter: Counter[str] = Counter()
    for record in records:
        value = _extract_label_field(record, field_name)
        if value:
            counter[str(value)] += 1
    return dict(counter)


def _extract_label_field(record: QAPair, field_name: str) -> Any:
    """从 QA 信息中提取标签字段，兼容旧 metadata 访问。"""
    labels = record.qa_info.labels
    if field_name in labels:
        return labels[field_name]
    return record.metadata.get(field_name)


def _count_failed_errors(failed_records: List[dict]) -> Dict[str, int]:
    """统计失败错误码分布。"""
    counter: Counter[str] = Counter()
    for record in failed_records:
        for error in record.get("errors", []):
            counter[str(error)] += 1
    return dict(counter)


def _load_doc_map(manifest_paths: Dict[str, Path]) -> Dict[str, str]:
    """从 parser manifest 读取精简的 md5 => 文件名映射摘要。"""
    parser_manifest_path = manifest_paths.get("parser")
    if not parser_manifest_path or not parser_manifest_path.exists():
        return {}
    payload = json.loads(parser_manifest_path.read_text(encoding="utf-8"))
    mappings = payload.get("doc_id_mapping", [])
    summary: Dict[str, str] = {}
    for item in mappings:
        parsed_doc_id = item.get("parsed_doc_id")
        source_file_name = item.get("source_file_name") or item.get("source_doc_name")
        if parsed_doc_id and source_file_name:
            summary[str(parsed_doc_id)] = str(source_file_name)
    return summary


def _load_planner_summary(manifest_paths: Dict[str, Path]) -> Dict[str, Any]:
    """从 planner manifest 读取规划摘要。"""
    planner_manifest_path = manifest_paths.get("planner")
    if not planner_manifest_path or not planner_manifest_path.exists():
        return {}
    payload = json.loads(planner_manifest_path.read_text(encoding="utf-8"))
    result: Dict[str, Any] = {}
    targets = payload.get("targets")
    summary = payload.get("summary")
    if isinstance(targets, dict):
        result["targets"] = targets
    if isinstance(summary, dict):
        result["summary"] = summary
    return result


def _load_gate_summary(manifest_paths: Dict[str, Path]) -> Dict[str, Any]:
    """从 gate manifest 读取门禁摘要。"""
    gate_manifest_path = manifest_paths.get("gate")
    if not gate_manifest_path or not gate_manifest_path.exists():
        return {}
    payload = json.loads(gate_manifest_path.read_text(encoding="utf-8"))
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return summary
    return {}
