"""流水线核心组件与适配器的聚合入口。"""

from tc_datasynth.pipeline.adapters import (
    AdapterConfigBase,
    AdapterResult,
    DocumentAdapter,
    MockPdfAdapter,
    MockWordAdapter,
)
from tc_datasynth.pipeline.components import PipelineComponents
from tc_datasynth.pipeline.generator import (
    GenerationConfig,
    GeneratorConfigBase,
    MockQAGenerator,
    QAGeneratorBase,
)
from tc_datasynth.pipeline.parser import (
    AdapterRegistry,
    ParserBase,
    ParserConfigBase,
    SimpleParserConfig,
    SimpleUnifiedParser,
)
from tc_datasynth.pipeline.runner import PipelineRunner
from tc_datasynth.pipeline.sampler import (
    SamplerBase,
    SamplerConfigBase,
    SamplingConfig,
    SimpleChunkSampler,
)
from tc_datasynth.pipeline.validator import (
    QualityGateBase,
    SimpleCompositeConfig,
    SimpleCompositeGate,
    SimpleSchemaGate,
    SimpleValidatorConfig,
    ValidatorConfigBase,
)

__all__ = [
    "AdapterConfigBase",
    "AdapterResult",
    "DocumentAdapter",
    "MockPdfAdapter",
    "MockWordAdapter",
    "AdapterRegistry",
    "ParserBase",
    "ParserConfigBase",
    "SimpleParserConfig",
    "SimpleUnifiedParser",
    "SamplerBase",
    "SamplerConfigBase",
    "SamplingConfig",
    "SimpleChunkSampler",
    "QAGeneratorBase",
    "GeneratorConfigBase",
    "GenerationConfig",
    "MockQAGenerator",
    "QualityGateBase",
    "ValidatorConfigBase",
    "SimpleValidatorConfig",
    "SimpleSchemaGate",
    "SimpleCompositeGate",
    "SimpleCompositeConfig",
    "PipelineRunner",
    "PipelineComponents",
]
