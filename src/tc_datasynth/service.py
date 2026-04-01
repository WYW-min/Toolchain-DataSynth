from __future__ import annotations

"""
业务服务层：组件装配与流程执行，CLI/API 共用。
"""

from dataclasses import fields, is_dataclass
from dataclasses import dataclass
from typing import Any, Optional

from tc_datasynth.core import RunArtifacts, RunContext, RuntimeConfig
from tc_datasynth.io.reader import SimpleDocumentReader
from tc_datasynth.io.writer import SimpleQAWriter
from tc_datasynth.pipeline.adapter.implements.pdf_cpu import PdfCpuAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_gpu import PdfGpuAdapter
from tc_datasynth.pipeline import (
    AdapterRegistry,
    ConcurrentParserConfig,
    ConcurrentUnifiedParser,
    EvidenceValidator,
    EvidenceValidatorConfig,
    GreedyAdditionSampler,
    LabelValidator,
    LabelValidatorConfig,
    SamplerRegistry,
    MockPdfAdapter,
    MockQAGenerator,
    MockWordAdapter,
    PipelineComponents,
    PipelineRunner,
    ParserRegistry,
    PlannerRegistry,
    SimpleCompositeGate,
    SimpleCompositeGateConfig,
    SimplePlanner,
    SimplePlannerConfig,
    SimpleChunkSampler,
    SimpleUnifiedParser,
    SimpleSchemaValidator,
)
from tc_datasynth.pipeline.generator import (
    ConcurrentQaConfig,
    ConcurrentQaGenerator,
    GenerationConfig,
    QAGeneratorBase,
    SimpleQaGenerator,
    SimpleQaConfig,
)
from tc_datasynth.pipeline.enhance.mixin import (
    PreflightCheckMixin,
    PreflightCheckResult,
)


@dataclass(slots=True)
class SynthesisRequest:
    """合成请求参数，CLI/API 统一入口。"""

    doc_limit: Optional[int] = None


@dataclass(slots=True)
class SynthesisResponse:
    """合成响应，封装运行结果。"""

    artifacts: Optional[RunArtifacts]
    success: bool = True
    error: Optional[str] = None


@dataclass(slots=True)
class PreflightResponse:
    """预检响应。"""

    results: list[PreflightCheckResult]
    success: bool = True
    error: Optional[str] = None


class DataSynthService:
    """数据合成服务，封装组件装配与执行。"""

    DEFAULT_VALIDATOR_NAMES = ("simple_schema", "evidence", "label")

    def __init__(self, config: RuntimeConfig) -> None:
        self.config = config

    def _build_context(self) -> RunContext:
        """构建运行上下文。"""
        return RunContext.from_config(config=self.config, logger=None)

    def _build_components(self, ctx: RunContext) -> PipelineComponents:
        """基于配置装配流水线组件。"""
        ctx.logger.info(f"运行模式: {self.config.mode}")
        ctx.logger.info(f"生成器实现: {self._resolve_generator_name()}")

        registry = self._build_adapter_registry()
        return PipelineComponents(
            reader=SimpleDocumentReader(self.config.input_dir),
            parser=self._build_parser(registry),
            sampler=self._build_sampler(),
            planner=self._build_planner(),
            generator=self._build_generator(),
            gate=self._build_gate(),
            writer=SimpleQAWriter(self.config.output_dir),
        )

    def _build_adapter_registry(self) -> AdapterRegistry:
        """按运行模式装配文档适配器。"""
        pdf_adapter = self._build_pdf_adapter()
        docx_adapter = self._build_docx_adapter()
        return AdapterRegistry(
            {
                ".pdf": pdf_adapter,
                ".docx": docx_adapter,
            }
        )

    def _build_pdf_adapter(self):
        """按配置装配 PDF 适配器。"""
        raw_config = self._get_adapter_component_config("pdf")
        default_name = (
            MockPdfAdapter.get_component_name()
            if self.config.mode == "mock"
            else PdfCpuAdapter.get_component_name()
        )
        return self._build_adapter_from_config(
            raw_config=raw_config,
            default_name=default_name,
            implementations={
                MockPdfAdapter.get_component_name(): MockPdfAdapter,
                PdfCpuAdapter.get_component_name(): PdfCpuAdapter,
                PdfGpuAdapter.get_component_name(): PdfGpuAdapter,
            },
        )

    def _build_docx_adapter(self):
        """按配置装配 DOCX 适配器。"""
        raw_config = self._get_adapter_component_config("docx")
        return self._build_adapter_from_config(
            raw_config=raw_config,
            default_name=MockWordAdapter.get_component_name(),
            implementations={
                MockWordAdapter.get_component_name(): MockWordAdapter,
            },
        )

    def _get_adapter_component_config(self, doc_type: str) -> dict[str, Any]:
        """读取某类文档适配器配置。"""
        raw_adapter_components = self.config.components.get("adapter", {})
        if not isinstance(raw_adapter_components, dict):
            return {}
        raw_value = raw_adapter_components.get(doc_type, {})
        if not isinstance(raw_value, dict):
            raise ValueError(f"components.adapter.{doc_type} 必须为对象")
        return dict(raw_value)

    def _build_adapter_from_config(
        self,
        *,
        raw_config: dict[str, Any],
        default_name: str,
        implementations: dict[str, type],
    ):
        """构造某类文档的具体适配器实例。"""
        adapter_name = str(raw_config.pop("name", default_name))
        try:
            adapter_cls = implementations[adapter_name]
        except KeyError as exc:
            supported = ", ".join(sorted(implementations))
            raise ValueError(
                f"不支持的适配器实现: {adapter_name}，可选值: {supported}"
            ) from exc
        if adapter_cls is PdfGpuAdapter:
            raw_config = self._normalize_pdf_gpu_config(raw_config)
        adapter_config = self._merge_component_config(
            adapter_cls.default_config(),
            raw_config,
        )
        return adapter_cls(config=adapter_config)

    @staticmethod
    def _normalize_pdf_gpu_config(raw_config: dict[str, Any]) -> dict[str, Any]:
        """兼容旧版平铺 MinerU 解析参数，统一归入 parse_options。"""
        normalized = dict(raw_config)
        parse_option_keys = {
            "backend",
            "parse_method",
            "formula_enable",
            "table_enable",
            "lang_list",
            "start_page_id",
            "end_page_id",
        }
        parse_options = normalized.get("parse_options", {})
        if parse_options and not isinstance(parse_options, dict):
            raise ValueError("components.adapter.pdf.parse_options 必须为对象")
        merged_options = dict(parse_options) if isinstance(parse_options, dict) else {}
        for key in list(normalized.keys()):
            if key in parse_option_keys:
                merged_options[key] = normalized.pop(key)
        if merged_options:
            normalized["parse_options"] = merged_options
        return normalized

    def _build_sampler(self):
        """按配置装配采样器实现。"""
        sampler_registry = SamplerRegistry(
            {
                GreedyAdditionSampler.get_component_name(): GreedyAdditionSampler,
                SimpleChunkSampler.get_component_name(): SimpleChunkSampler,
            }
        )
        raw_config = dict(self.config.components.get("sampler", {}))
        sampler_name = str(raw_config.pop("name", GreedyAdditionSampler.get_component_name()))
        sampler_cls = sampler_registry.resolve(sampler_name)
        sampler_config = self._merge_component_config(
            sampler_cls.default_config(),
            raw_config,
        )
        return sampler_cls(config=sampler_config)

    def _build_parser(self, registry: AdapterRegistry):
        """按配置装配解析器实现。"""
        parser_registry = ParserRegistry(
            {
                SimpleUnifiedParser.get_component_name(): SimpleUnifiedParser,
                ConcurrentUnifiedParser.get_component_name(): ConcurrentUnifiedParser,
            }
        )
        raw_config = dict(self.config.components.get("parser", {}))
        parser_name = str(raw_config.pop("name", SimpleUnifiedParser.get_component_name()))
        parser_cls = parser_registry.resolve(parser_name)
        parser_config = self._merge_component_config(
            parser_cls.default_config(),
            raw_config,
        )
        return parser_cls(registry=registry, config=parser_config)

    def _build_planner(self) -> SimplePlanner:
        """按配置装配规划器实现。"""
        planner_registry = PlannerRegistry(
            {
                SimplePlanner.get_component_name(): SimplePlanner,
            }
        )
        raw_config = dict(self.config.components.get("planner", {}))
        planner_name = str(raw_config.pop("name", SimplePlanner.get_component_name()))
        planner_cls = planner_registry.resolve(planner_name)
        planner_config = self._merge_component_config(
            planner_cls.default_config(),
            raw_config,
        )
        return planner_cls(config=planner_config)

    def _build_gate(self) -> SimpleCompositeGate:
        """按配置装配门控器及其下属校验器。"""
        raw_gate_config = dict(self.config.components.get("gate", {}))
        gate_name = str(raw_gate_config.pop("name", "simple_composite"))
        if gate_name != "simple_composite":
            raise ValueError(f"不支持的门控器实现: {gate_name}")
        raw_validator_names = raw_gate_config.pop("validators", None)
        validator_names = self._normalize_validator_names(raw_validator_names)
        gate_config = self._merge_component_config(
            SimpleCompositeGate.default_config(),
            raw_gate_config,
        )
        validators = [self._build_validator(name) for name in validator_names]
        return SimpleCompositeGate(validators=validators, config=gate_config)

    def _normalize_validator_names(self, value: Any) -> list[str]:
        """规范化 validator 名称列表。"""
        if value is None:
            return list(self.DEFAULT_VALIDATOR_NAMES)
        if not isinstance(value, list):
            raise ValueError("components.gate.validators 必须为列表")
        names = [str(item).strip() for item in value if str(item).strip()]
        if not names:
            raise ValueError("components.gate.validators 不能为空列表")
        return names

    def _build_validator(self, name: str):
        """按名称装配单个 validator。"""
        validator_overrides = self._get_validator_overrides(name)
        if name == "simple_schema":
            config = self._merge_component_config(
                SimpleSchemaValidator.default_config(),
                validator_overrides,
            )
            return SimpleSchemaValidator(config)
        if name == "evidence":
            default_config = EvidenceValidatorConfig(
                min_evidence_len=self.config.spec.min_evidence_len
            )
            config = self._merge_component_config(default_config, validator_overrides)
            return EvidenceValidator(config)
        if name == "label":
            default_config = LabelValidatorConfig(
                reasoning_min_evidence_len=self.config.spec.min_evidence_len
            )
            config = self._merge_component_config(default_config, validator_overrides)
            return LabelValidator(config)
        raise ValueError(f"不支持的校验器实现: {name}")

    def _get_validator_overrides(self, name: str) -> dict[str, Any]:
        """读取某个 validator 的细粒度配置。"""
        raw_validator_components = self.config.components.get("validator", {})
        if not isinstance(raw_validator_components, dict):
            return {}
        raw_value = raw_validator_components.get(name, {})
        if not isinstance(raw_value, dict):
            raise ValueError(f"components.validator.{name} 必须为对象")
        return dict(raw_value)

    @staticmethod
    def _merge_component_config(default_config: Any, overrides: dict[str, Any]) -> Any:
        """以 dataclass 默认值为底，合并配置文件中的组件参数。"""
        allowed_fields = {field.name for field in fields(default_config)}
        unknown_fields = set(overrides) - allowed_fields
        if unknown_fields:
            unknown_text = ", ".join(sorted(unknown_fields))
            raise ValueError(f"未知组件参数: {unknown_text}")
        values = {}
        for field_name in allowed_fields:
            default_value = getattr(default_config, field_name)
            override_value = overrides.get(field_name, default_value)
            if (
                is_dataclass(default_value)
                and isinstance(override_value, dict)
            ):
                override_value = DataSynthService._merge_component_config(
                    default_value,
                    override_value,
                )
            values[field_name] = override_value
        return type(default_config)(**values)

    def _build_generator(self) -> QAGeneratorBase:
        """按配置装配生成器实现。"""
        raw_config = dict(self.config.components.get("generator", {}))
        backend = str(raw_config.pop("name", "mock"))
        if backend == "mock":
            default_config = GenerationConfig(
                seed=self.config.seed,
            )
            generator_config = self._merge_component_config(default_config, raw_config)
            return MockQAGenerator(generator_config)
        if backend == "simple_qa":
            default_config = SimpleQaConfig(
                seed=self.config.seed,
                llm_model=self.config.llm_model,
                llm_config_path=self.config.llm_config_path,
            )
            generator_config = self._merge_component_config(default_config, raw_config)
            return SimpleQaGenerator(generator_config)
        if backend == "concurrent_qa":
            default_config = ConcurrentQaConfig(
                seed=self.config.seed,
                llm_model=self.config.llm_model,
                llm_config_path=self.config.llm_config_path,
            )
            generator_config = self._merge_component_config(default_config, raw_config)
            return ConcurrentQaGenerator(generator_config)
        raise ValueError(f"不支持的生成器实现: {backend}")

    def _resolve_generator_name(self) -> str:
        """返回当前生成器实现名称，优先读取组件配置。"""
        generator_config = self.config.components.get("generator", {})
        if isinstance(generator_config, dict) and generator_config.get("name"):
            return str(generator_config["name"])
        return "mock"

    def _iter_preflight_components(
        self, components: PipelineComponents
    ) -> list[PreflightCheckMixin]:
        """收集具备预检能力的组件实例。"""
        candidates: list[object] = [
            components.reader,
            components.parser,
            components.sampler,
            components.planner,
            components.generator,
            components.gate,
            components.writer,
        ]
        parser_registry = getattr(components.parser, "registry", None)
        if parser_registry is not None:
            mapping = getattr(parser_registry, "mapping", {})
            if isinstance(mapping, dict):
                candidates.extend(mapping.values())

        checkables: list[PreflightCheckMixin] = []
        seen_ids: set[int] = set()
        for candidate in candidates:
            if not isinstance(candidate, PreflightCheckMixin):
                continue
            candidate_id = id(candidate)
            if candidate_id in seen_ids:
                continue
            seen_ids.add(candidate_id)
            checkables.append(candidate)
        return checkables

    def preflight(self) -> PreflightResponse:
        """执行外部依赖预检，不启动主流程。"""
        try:
            self.config.ensure_output_dir()
            ctx = self._build_context()
            components = self._build_components(ctx)
            results = [
                component.preflight_check()
                for component in self._iter_preflight_components(components)
            ]
            return PreflightResponse(
                results=results,
                success=all(result.ok for result in results),
            )
        except Exception as exc:
            return PreflightResponse(results=[], success=False, error=str(exc))

    def run(self, request: SynthesisRequest) -> SynthesisResponse:
        """执行合成流程并返回响应。"""
        ctx: Optional[RunContext] = None
        try:
            self.config.ensure_output_dir()
            ctx = self._build_context()
            components = self._build_components(ctx)
            runner = PipelineRunner(components=components, context=ctx)
            artifacts = runner.run(doc_limit=request.doc_limit)
            return SynthesisResponse(artifacts=artifacts, success=True)
        except Exception as exc:
            if ctx is not None:
                ctx.logger.exception(f"合成流程失败: {exc}")
            return SynthesisResponse(artifacts=None, success=False, error=str(exc))

    def run_sync(self, doc_limit: Optional[int] = None) -> RunArtifacts:
        """同步执行并返回结果，失败则抛异常。"""
        response = self.run(SynthesisRequest(doc_limit=doc_limit))
        if not response.success or response.artifacts is None:
            raise RuntimeError(response.error or "合成流程失败")
        return response.artifacts
