from __future__ import annotations

"""
Plan：执行计划（怎么做）。
"""

from typing import Dict

from pydantic import BaseModel, Field


class PlanConfig(BaseModel):
    """执行计划，供流水线组件读取。"""

    difficulty_profile: Dict[str, float] = Field(..., description="归一化后的难度比例")
    question_type_mix: Dict[str, float] = Field(..., description="归一化后的题型比例")
    min_evidence_len: int = Field(..., description="最小参照段落长度")
