from __future__ import annotations

"""
业务服务层：组件装配与流程执行，CLI/API 共用。
"""

from dataclasses import dataclass
from typing import Optional

from tc_datasynth.core import RunArtifacts, RunContext, RuntimeConfig
from tc_datasynth.io.reader import SimpleDocumentReader
from tc_datasynth.io.writer import SimpleQAWriter
from tc_datasynth.pipeline import (
    AdapterRegistry,
    MockPdfAdapter,
    MockQAGenerator,
    MockWordAdapter,
    PipelineComponents,
    PipelineRunner,
    SimpleChunkSampler,
    SimpleCompositeGate,
    SimpleSchemaGate,
    SimpleUnifiedParser,
)
from tc_datasynth.pipeline.generator import GenerationConfig


@dataclass(slots=True)
class SynthesisRequest:
    """合成请求参数，CLI/API 统一入口。"""

    limit: Optional[int] = None


@dataclass(slots=True)
class SynthesisResponse:
    """合成响应，封装运行结果。"""

    artifacts: Optional[RunArtifacts]
    success: bool = True
    error: Optional[str] = None


class DataSynthService:
    """数据合成服务，封装组件装配与执行。"""

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config

    def _build_context(self) -> RunContext:
        """构建运行上下文。"""
        return RunContext.from_config(config=self.config, logger=None)

    def _build_components(self, ctx: RunContext) -> PipelineComponents:
        """基于配置装配流水线组件。"""
        if self.config.mode != "mock":
            ctx.logger.warning("当前仅实现 mock 模式，已回退为 mock 组件。")

        registry = AdapterRegistry({".pdf": MockPdfAdapter(), ".docx": MockWordAdapter()})
        return PipelineComponents(
            reader=SimpleDocumentReader(self.config.input_dir),
            parser=SimpleUnifiedParser(registry=registry),
            sampler=SimpleChunkSampler(),
            generator=MockQAGenerator(
                GenerationConfig(
                    mock_questions_per_doc=self.config.mock_questions_per_doc, seed=self.config.seed
                )
            ),
            validator=SimpleCompositeGate([SimpleSchemaGate()]),
            writer=SimpleQAWriter(self.config.output_dir),
        )

    def run(self, request: SynthesisRequest) -> SynthesisResponse:
        """执行合成流程并返回响应。"""
        ctx: Optional[RunContext] = None
        try:
            self.config.ensure_output_dir()
            ctx = self._build_context()
            components = self._build_components(ctx)
            runner = PipelineRunner(components=components, context=ctx)
            artifacts = runner.run(limit=request.limit)
            return SynthesisResponse(artifacts=artifacts, success=True)
        except Exception as exc:
            if ctx is not None:
                ctx.logger.exception(f"合成流程失败: {exc}")
            return SynthesisResponse(artifacts=None, success=False, error=str(exc))

    def run_sync(self, limit: Optional[int] = None) -> RunArtifacts:
        """同步执行并返回结果，失败则抛异常。"""
        response = self.run(SynthesisRequest(limit=limit))
        if not response.success or response.artifacts is None:
            raise RuntimeError(response.error or "合成流程失败")
        return response.artifacts
