from __future__ import annotations

"""
报告输出：生成运行统计并落盘。
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List

from tc_datasynth.core.models import QAPair


def write_run_report(
    output_dir: Path,
    run_id: str,
    doc_count: int,
    final_records: List[QAPair],
    failed_records: List[dict],
) -> Path:
    """生成当前运行的 JSON 报告并返回路径。"""
    report = {
        "run_id": run_id,
        "documents_processed": doc_count,
        "qa_count": len(final_records),
        "failed_count": len(failed_records),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    report_path = output_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report_path
