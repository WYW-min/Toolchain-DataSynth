from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Literal
from unittest.mock import patch

import requests
import tc_datasynth.core.llm.llm_factory as llm_factory_module
from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.pipeline.adapter.implements.mock_pdf import MockPdfAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_cpu import PdfCpuAdapter
from tc_datasynth.pipeline.adapter.implements.pdf_gpu import PdfGpuAdapter
from tc_datasynth.pipeline.enhance.mixin import PreflightStage
from tc_datasynth.pipeline.parser import ConcurrentUnifiedParser, SimpleUnifiedParser
from tc_datasynth.pipeline.generator import (
    ConcurrentQaGenerator,
    MockQAGenerator,
    SimpleQaGenerator,
)
from tc_datasynth.pipeline.gate import SimpleCompositeGate
from tc_datasynth.pipeline.validator import EvidenceValidator, LabelValidator, SimpleSchemaValidator
from tc_datasynth.pipeline.planner import SimplePlanner
from tc_datasynth.pipeline.sampler import GreedyAdditionSampler, SimpleChunkSampler
from tc_datasynth.service import DataSynthService


class ServiceGeneratorBackendTest(unittest.TestCase):
    """校验主流程生成器实现装配。"""

    def test_default_backend_is_mock(self) -> None:
        """未指定后端时应装配 MockQAGenerator。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.generator, MockQAGenerator)

    def test_simple_qa_backend_is_used(self) -> None:
        """指定 simple_qa 时应装配 SimpleQaGenerator。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, generator_name="simple_qa")
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.generator, SimpleQaGenerator)
            self.assertEqual(components.generator.config.llm_model, "doubao-flash")

    def test_mock_mode_uses_mock_pdf_adapter(self) -> None:
        """mock 模式应装配 MockPdfAdapter。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, mode="mock")
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.parser.registry.mapping[".pdf"], MockPdfAdapter)

    def test_real_mode_uses_pdf_cpu_adapter(self) -> None:
        """real 模式应装配 PdfCpuAdapter。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, mode="real")
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.parser.registry.mapping[".pdf"], PdfCpuAdapter)

    def test_pdf_adapter_can_be_configured_from_components(self) -> None:
        """components.adapter.pdf 应可切换实现并覆盖参数。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, mode="real")
            config.components = {
                "generator": {"name": "mock"},
                "adapter": {
                    "pdf": {
                        "name": "pdf_gpu",
                        "server_url": "http://127.0.0.1:8000",
                        "timeout_seconds": 600,
                        "parse_options": {
                            "backend": "hybrid-auto-engine",
                            "parse_method": "auto",
                        },
                    }
                },
            }
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            pdf_adapter = components.parser.registry.mapping[".pdf"]
            self.assertIsInstance(pdf_adapter, PdfGpuAdapter)
            self.assertEqual(pdf_adapter.config.server_url, "http://127.0.0.1:8000")
            self.assertEqual(pdf_adapter.config.timeout_seconds, 600)
            self.assertEqual(pdf_adapter.config.parse_options.backend, "hybrid-auto-engine")

    def test_parser_can_be_configured_from_components(self) -> None:
        """components.parser 应可切换实现并覆盖并发参数。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            config.components = {
                "parser": {
                    "name": "concurrent_unified",
                    "max_workers": 3,
                }
            }
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.parser, ConcurrentUnifiedParser)
            self.assertEqual(components.parser.config.max_workers, 3)

    def test_default_parser_is_simple_unified(self) -> None:
        """未指定 parser 时应装配 simple_unified。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.parser, SimpleUnifiedParser)

    def test_default_sampler_is_greedy_addition(self) -> None:
        """主流程默认应装配 GreedyAdditionSampler。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.sampler, GreedyAdditionSampler)

    def test_sampler_can_be_configured_from_components(self) -> None:
        """components.sampler 应可切换实现并覆盖参数。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            config.components = {
                "sampler": {
                    "name": "simple_chunk",
                    "chunk_size": 128,
                }
            }
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.sampler, SimpleChunkSampler)
            self.assertEqual(components.sampler.config.chunk_size, 128)

    def test_planner_can_be_configured_from_components(self) -> None:
        """components.planner 应可覆盖轻量启发式参数。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            config.components = {
                "planner": {
                    "name": "simple",
                    "skip_below_evidence_ratio": 0.25,
                }
            }
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.planner, SimplePlanner)
            self.assertEqual(components.planner.config.skip_below_evidence_ratio, 0.25)

    def test_gate_can_be_configured_with_validator_names_and_overrides(self) -> None:
        """components.gate / components.validator 应可组合配置校验器。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            config.components = {
                "gate": {
                    "name": "simple_composite",
                    "validators": ["simple_schema", "evidence"],
                    "stop_on_first_error": False,
                },
                "validator": {
                    "evidence": {
                        "min_evidence_len": 32,
                    }
                },
            }
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.gate, SimpleCompositeGate)
            self.assertFalse(components.gate.config.stop_on_first_error)
            self.assertEqual(len(components.gate.validators), 2)
            self.assertIsInstance(components.gate.validators[0], SimpleSchemaValidator)
            self.assertIsInstance(components.gate.validators[1], EvidenceValidator)
            self.assertEqual(components.gate.validators[1].config.min_evidence_len, 32)

    def test_gate_uses_default_validator_set_when_unspecified(self) -> None:
        """未显式指定 validators 时应使用默认推荐集合。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base)
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertEqual(len(components.gate.validators), 3)
            self.assertIsInstance(components.gate.validators[0], SimpleSchemaValidator)
            self.assertIsInstance(components.gate.validators[1], EvidenceValidator)
            self.assertIsInstance(components.gate.validators[2], LabelValidator)

    def test_preflight_returns_empty_results_for_mock_stack(self) -> None:
        """无外部服务依赖时，预检应成功且结果为空。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, generator_name="mock", mode="mock")
            service = DataSynthService(config=config)
            response = service.preflight()
            self.assertTrue(response.success)
            self.assertEqual(response.results, [])

    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.get")
    def test_preflight_checks_pdf_gpu_adapter(self, mock_get) -> None:
        """启用 pdf_gpu 时，预检应调用其健康检查。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, generator_name="mock", mode="real")
            config.components = {
                "generator": {"name": "mock"},
                "adapter": {
                    "pdf": {
                        "name": "pdf_gpu",
                        "server_url": "http://127.0.0.1:8000",
                    }
                },
            }
            mock_get.side_effect = requests.ConnectionError("connection refused")
            service = DataSynthService(config=config)
            response = service.preflight()
            self.assertFalse(response.success)
            self.assertEqual(len(response.results), 1)
            result = response.results[0]
            self.assertEqual(result.component_name, "pdf_gpu")
            self.assertFalse(result.ok)
            self.assertEqual(result.details["error_code"], "mineru.health_unavailable")

    def test_preflight_checks_simple_qa_generator(self) -> None:
        """启用 simple_qa 时，预检应包含 generator 的模型检查结果。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            env_path = base / "llm.env"
            env_path.write_text(
                "TEST_BASE_URL=https://unit.example.com\nTEST_API_KEY=test-key\n",
                encoding="utf-8",
            )
            llm_config_path = base / "llm.toml"
            llm_config_path.write_text(
                """
[settings]
env_path = "llm.env"

[models.demo_model]
model = "dummy"
model_provider = "openai"
base_url_env = "TEST_BASE_URL"
api_key_env = "TEST_API_KEY"
""".strip(),
                encoding="utf-8",
            )

            class _FakeModel:
                def stream(self, _: str):
                    yield "1"

            llm_factory_module.llm_manager = None
            llm_factory_module.LlmFactory._instance = None
            config = self._make_config(base, generator_name="simple_qa", mode="mock")
            config.llm_config_path = llm_config_path
            config.llm_model = "demo-model"
            config.components = {
                "generator": {
                    "name": "simple_qa",
                    "llm_model": "demo-model",
                    "llm_config_path": llm_config_path,
                    "prompt_id": "simple_qa",
                }
            }
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=_FakeModel()
            ):
                service = DataSynthService(config=config)
                response = service.preflight()

            self.assertTrue(response.success)
            self.assertEqual(len(response.results), 1)
            result = response.results[0]
            self.assertEqual(result.component_name, "simple_qa")
            self.assertEqual(result.stage, PreflightStage.PING)
            self.assertTrue(result.ok)
            llm_factory_module.llm_manager = None
            llm_factory_module.LlmFactory._instance = None

    @staticmethod
    def _make_config(
        base: Path,
        generator_name: Literal["mock", "simple_qa", "concurrent_qa"] = "mock",
        mode: str = "mock",
    ) -> RuntimeConfig:
        input_dir = base / "in"
        output_dir = base / "out"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        return RuntimeConfig(
            input_dir=input_dir,
            output_dir=output_dir,
            mode=mode,
            doc_limit=1,
            log_level="INFO",
            logs_root_base=base / "logs",
            temp_root_base=base / "temp",
            llm_model="doubao-flash",
            components={"generator": {"name": generator_name}},
        )

    def test_concurrent_qa_backend_is_used(self) -> None:
        """指定 concurrent_qa 时应装配 ConcurrentQaGenerator。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = self._make_config(base, generator_name="concurrent_qa")
            service = DataSynthService(config=config)
            ctx = service._build_context()
            components = service._build_components(ctx)
            self.assertIsInstance(components.generator, ConcurrentQaGenerator)
            self.assertEqual(components.generator.config.llm_model, "doubao-flash")
