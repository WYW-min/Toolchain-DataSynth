from __future__ import annotations

"""
组件目录：统一维护当前可用的组件注册信息。
"""

from typing import Dict, Iterable, Type

from tc_datasynth.core.registrable import RegistrableComponent
from tc_datasynth.io.reader import SimpleDocumentReader
from tc_datasynth.io.writer import SimpleQAWriter
from tc_datasynth.pipeline.adapter.implements.mock_pdf import MockPdfAdapter
from tc_datasynth.pipeline.adapter.implements.mock_word import MockWordAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_cpu import PdfCpuAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_gpu import PdfGpuAdapter
from tc_datasynth.pipeline.gate.implements.simple_composite import SimpleCompositeGate
from tc_datasynth.pipeline.generator.implements.concurrent_qa import ConcurrentQaGenerator
from tc_datasynth.pipeline.generator.implements.mock_generator import MockQAGenerator
from tc_datasynth.pipeline.generator.implements.simple_qa import SimpleQaGenerator
from tc_datasynth.pipeline.parser.implements.simple_unified import SimpleUnifiedParser
from tc_datasynth.pipeline.parser.implements.concurrent_unified import ConcurrentUnifiedParser
from tc_datasynth.pipeline.planner.implements.simple_planner import SimplePlanner
from tc_datasynth.pipeline.sampler.implements.ga_sampler import GreedyAdditionSampler
from tc_datasynth.pipeline.sampler.implements.simple_chunk import SimpleChunkSampler
from tc_datasynth.pipeline.validator.implements.simple_schema import (
    SimpleSchemaValidator,
)
from tc_datasynth.pipeline.validator.implements.evidence_validator import EvidenceValidator
from tc_datasynth.pipeline.validator.implements.label_validator import LabelValidator


COMPONENT_CLASS_GROUPS: Dict[str, list[Type[RegistrableComponent]]] = {
    "reader": [SimpleDocumentReader],
    "parser": [SimpleUnifiedParser, ConcurrentUnifiedParser],
    "adapter": [MockPdfAdapter, MockWordAdapter, PdfCpuAdapter, PdfGpuAdapter],
    "sampler": [SimpleChunkSampler, GreedyAdditionSampler],
    "planner": [SimplePlanner],
    "generator": [ConcurrentQaGenerator, MockQAGenerator, SimpleQaGenerator],
    "validator": [EvidenceValidator, LabelValidator, SimpleSchemaValidator],
    "gate": [SimpleCompositeGate],
    "writer": [SimpleQAWriter],
}


def _build_mapping(
    implementations: Iterable[Type[RegistrableComponent]],
) -> Dict[str, Type[object]]:
    """基于实现类的 component_name 构建目录映射。"""
    return {
        impl_cls.get_component_name(): impl_cls
        for impl_cls in implementations
    }


def get_component_catalog() -> Dict[str, Dict[str, Type[object]]]:
    """返回当前已登记的组件目录。"""
    return {
        base_component: _build_mapping(implementations)
        for base_component, implementations in COMPONENT_CLASS_GROUPS.items()
    }


def format_component_catalog() -> str:
    """格式化组件目录输出。"""
    lines = ["已注册组件:"]
    for base_component, implementations in sorted(get_component_catalog().items()):
        lines.append(f"{base_component}:")
        for name, impl_cls in sorted(implementations.items()):
            lines.append(f"  - {name} | {impl_cls.__name__}")
    return "\n".join(lines)
