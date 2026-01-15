"""
核心能力聚合：配置、日志、数据模型。
"""

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.logging import configure_logger
from tc_datasynth.core.models import (
    DocumentChunk,
    IntermediateRepresentation,
    QAPair,
    RunArtifacts,
    SourceDocument,
    ValidationResult,
)
from tc_datasynth.core.plan import PlanConfig
from tc_datasynth.core.planning import MockPlanCompiler, PlanCompiler
from tc_datasynth.core.spec import SpecConfig

__all__ = [
    "RuntimeConfig",
    "RunContext",
    "configure_logger",
    "SpecConfig",
    "PlanConfig",
    "PlanCompiler",
    "MockPlanCompiler",
    "DocumentChunk",
    "IntermediateRepresentation",
    "QAPair",
    "RunArtifacts",
    "SourceDocument",
    "ValidationResult",
]
