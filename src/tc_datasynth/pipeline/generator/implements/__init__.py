"""
生成器实现集合。
"""

from tc_datasynth.pipeline.generator.implements.mock_generator import GenerationConfig, MockQAGenerator
from tc_datasynth.pipeline.generator.implements.concurrent_qa import (
    ConcurrentQaConfig,
    ConcurrentQaGenerator,
)
from tc_datasynth.pipeline.generator.implements.simple_qa import SimpleQaConfig, SimpleQaGenerator

__all__ = [
    "GenerationConfig",
    "MockQAGenerator",
    "ConcurrentQaConfig",
    "ConcurrentQaGenerator",
    "SimpleQaConfig",
    "SimpleQaGenerator",
]
