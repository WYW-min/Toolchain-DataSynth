from __future__ import annotations

"""
Spec：用户意图配置（想要什么）。
"""

from typing import Dict

from pydantic import BaseModel, Field


class SpecConfig(BaseModel):
    """用户意图配置，定义难度/题型比例等目标。"""

    difficulty_profile: Dict[str, float] = Field(
        default_factory=lambda: {"easy": 0.3, "medium": 0.5, "hard": 0.2},
        description="难度比例分布",
    )
    question_type_mix: Dict[str, float] = Field(
        default_factory=lambda: {"definition": 0.4, "factual": 0.3, "reasoning": 0.3},
        description="题型比例分布",
    )
    min_evidence_len: int = Field(default=80, description="最小参照段落长度")
