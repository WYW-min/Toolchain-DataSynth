from __future__ import annotations

"""
阶段 manifest 输出：记录各阶段可复查的索引信息。
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from tc_datasynth.core.plan import PlanConfig
from tc_datasynth.core.context import RunContext


def register_stage_manifest_entry(
    ctx: RunContext,
    stage: str,
    entry: Dict[str, Any],
) -> None:
    """登记一条阶段 manifest 记录。"""
    manifests = ctx.extras.setdefault("stage_manifests", {})
    stage_entries = manifests.setdefault(stage, [])
    stage_entries.append(entry)


def write_stage_manifests(
    output_dir: Path,
    stage_manifests: Dict[str, List[Dict[str, Any]]],
    plan: PlanConfig | None = None,
) -> Dict[str, Path]:
    """将各阶段 manifest 落盘到 `manifests/`。"""
    manifests_dir = output_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)

    written: Dict[str, Path] = {}
    for stage, entries in stage_manifests.items():
        normalized_entries = [_normalize_entry(entry) for entry in entries]
        payload = {
            "stage": stage,
            "entry_count": len(normalized_entries),
            "entries": normalized_entries,
        }
        if stage == "parser":
            payload["doc_id_mapping"] = _build_parser_doc_id_mapping(normalized_entries)
        if stage == "planner":
            payload = _build_planner_manifest_payload(normalized_entries, plan)
        if stage == "gate":
            payload = _build_gate_manifest_payload(normalized_entries)
        path = manifests_dir / f"{stage}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        written[stage] = path
    return written


def _build_parser_doc_id_mapping(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """构建 parser 阶段的可读文档名到解析后 doc_id 的映射摘要。"""
    mappings: List[Dict[str, Any]] = []
    for entry in entries:
        mappings.append(
            {
                "doc_id": entry.get("doc_id"),
                "parsed_doc_id": entry.get("parsed_doc_id"),
                "source_doc_name": entry.get("source_doc_name"),
                "source_file_name": entry.get("source_file_name"),
                "artifact_path": entry.get("artifact_path"),
            }
        )
    return mappings


def _normalize_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """将 manifest 里的路径字段统一转换为绝对路径字符串。"""
    normalized = dict(entry)
    for key in ("artifact_path", "source_path", "human_readable_dir", "attempts_path"):
        value = normalized.get(key)
        if value:
            normalized[key] = str(Path(str(value)).expanduser().resolve(strict=False))
    return normalized


def _build_planner_manifest_payload(
    entries: List[Dict[str, Any]],
    plan: PlanConfig | None,
) -> Dict[str, Any]:
    """构建 planner 阶段的增强 manifest。"""
    normalized_entries = [_normalize_planner_entry(entry) for entry in entries]
    summary = _build_planner_summary(entries)
    payload: Dict[str, Any] = {
        "stage": "planner",
        "entry_count": len(normalized_entries),
        "entries": normalized_entries,
        "summary": summary,
    }
    if plan is not None:
        payload["targets"] = {
            "difficulty_profile": dict(plan.difficulty_profile),
            "question_type_mix": dict(plan.question_type_mix),
            "min_evidence_len": plan.min_evidence_len,
        }
    return payload


def _normalize_planner_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """为 planner entry 增加 count/ratio 双写分布。"""
    normalized = _normalize_entry(entry)
    eligible_count = int(normalized.get("eligible_count") or normalized.get("record_count") or 0)
    normalized["difficulty_distribution"] = _distribution_payload(
        normalized.get("difficulty_distribution", {}),
        eligible_count,
    )
    normalized["question_type_distribution"] = _distribution_payload(
        normalized.get("question_type_distribution", {}),
        eligible_count,
    )
    return normalized


def _build_planner_summary(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """汇总 planner 阶段总体分布。"""
    planned_count = sum(int(entry.get("record_count") or 0) for entry in entries)
    eligible_count = sum(
        int(entry.get("eligible_count") or entry.get("record_count") or 0)
        for entry in entries
    )
    skipped_count = sum(int(entry.get("skipped_count") or 0) for entry in entries)
    difficulty_counts = _aggregate_distribution(entries, "difficulty_distribution")
    question_type_counts = _aggregate_distribution(entries, "question_type_distribution")
    return {
        "planned_count": planned_count,
        "eligible_count": eligible_count,
        "skipped_count": skipped_count,
        "difficulty_distribution": _distribution_payload(
            difficulty_counts,
            eligible_count,
        ),
        "question_type_distribution": _distribution_payload(
            question_type_counts,
            eligible_count,
        ),
    }


def _aggregate_distribution(
    entries: List[Dict[str, Any]],
    key: str,
) -> Dict[str, int]:
    """聚合 entry 中的分布计数。"""
    counts: Dict[str, int] = {}
    for entry in entries:
        raw = entry.get(key, {})
        if not isinstance(raw, dict):
            continue
        for label, value in raw.items():
            if value is None:
                continue
            counts[str(label)] = counts.get(str(label), 0) + int(value)
    return counts


def _distribution_payload(
    counts: Dict[str, Any],
    total: int,
) -> Dict[str, Dict[str, float] | Dict[str, int]]:
    """将分布转换为 count/ratio 双写结构。"""
    clean_counts: Dict[str, int] = {}
    for key, value in counts.items():
        if value is None:
            continue
        clean_counts[str(key)] = int(value)
    if total <= 0:
        ratios = {key: 0.0 for key in clean_counts}
    else:
        ratios = {
            key: round(value / total, 6)
            for key, value in clean_counts.items()
        }
    return {
        "count": clean_counts,
        "ratio": ratios,
    }


def _build_gate_manifest_payload(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """构建 gate 阶段的增强 manifest。"""
    accepted_count = sum(int(entry.get("accepted_count") or 0) for entry in entries)
    rejected_count = sum(int(entry.get("rejected_count") or 0) for entry in entries)
    error_counts = _aggregate_distribution(entries, "error_distribution")
    return {
        "stage": "gate",
        "entry_count": len(entries),
        "entries": entries,
        "summary": {
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "error_distribution": error_counts,
        },
    }
