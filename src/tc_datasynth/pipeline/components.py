from __future__ import annotations

"""
流水线组件容器：统一装配与注入。
"""

from dataclasses import dataclass

from tc_datasynth.io.reader import ReaderBase
from tc_datasynth.io.writer import WriterBase
from tc_datasynth.pipeline.gate import QualityGateBase
from tc_datasynth.pipeline.generator import QAGeneratorBase
from tc_datasynth.pipeline.parser import ParserBase
from tc_datasynth.pipeline.planner import PlannerBase
from tc_datasynth.pipeline.sampler import SamplerBase


@dataclass(slots=True)
class PipelineComponents:
    """流水线组件容器，便于统一装配与注入。"""

    reader: ReaderBase
    parser: ParserBase
    sampler: SamplerBase
    planner: PlannerBase
    generator: QAGeneratorBase
    gate: QualityGateBase
    writer: WriterBase
