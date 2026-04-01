from __future__ import annotations

"""
SimpleQaGenerator 单元与集成测试。
"""

import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

from langchain_core.runnables import RunnableLambda
from langchain_core.messages import AIMessage

import tc_datasynth.core.llm.llm_factory as llm_factory_module
from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.llm.structured_chain import StructuredChain
from tc_datasynth.core.models import DocumentChunk
from tc_datasynth.core.llm.prompt_factory import get_prompt_manager
from tc_datasynth.pipeline.enhance.mixin import PreflightStage
from tc_datasynth.pipeline.generator.implements.simple_qa import (
    SimpleQaConfig,
    SimpleQaGenerator,
)


class _FakeChain:
    """用于单元测试的假链路。"""

    required_inputs = {"text", "meta"}

    def run(self, _: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "parse": {
                "question": "Q?",
                "answer": "A.",
                "evidences": ["E1"],
                "proposition_thought": "P",
                "solution_thought": "S",
            },
            "error": None,
            "raw_text": "{}",
        }


class SimpleQaGeneratorUnitTest(unittest.TestCase):
    """SimpleQaGenerator 单元测试（假链路）。"""

    def setUp(self) -> None:
        llm_factory_module.llm_manager = None
        llm_factory_module.LlmFactory._instance = None

    def tearDown(self) -> None:
        llm_factory_module.llm_manager = None
        llm_factory_module.LlmFactory._instance = None

    def test_generate_with_fake_chain(self) -> None:
        """使用假链路生成 QAPair。"""
        chunk = DocumentChunk(
            chunk_id="c1",
            content="sample content",
            source_doc_id="doc1",
            section="intro",
        )
        config = SimpleQaConfig(prompt_id="simple_qa")
        generator = SimpleQaGenerator(config=config)
        generator._chain = _FakeChain()  # type: ignore[assignment]

        ctx = _make_context()
        metas = [
            {
                "system_meta": {"planner": "simple", "plan_index": 1},
                "prompt_meta": {"difficulty": "easy", "question_type": "definition"},
            }
        ]
        qas = generator.generate([chunk], ctx, metas=metas)

        self.assertEqual(len(qas), 1)
        self.assertEqual(qas[0].question, "Q?")
        self.assertEqual(qas[0].evidences, ["E1"])
        self.assertEqual(qas[0].metadata.get("generator"), "simple_qa")
        self.assertEqual(qas[0].metadata.get("difficulty"), "easy")
        self.assertEqual(qas[0].metadata.get("planner"), "simple")

    def test_preflight_check_validates_prompt_and_single_model(self) -> None:
        """预检应校验 prompt 与当前模型，而不是全量模型。"""
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

            generator = SimpleQaGenerator(
                config=SimpleQaConfig(
                    prompt_id="simple_qa",
                    llm_model="demo-model",
                    llm_config_path=llm_config_path,
                )
            )
            with patch.object(
                llm_factory_module, "init_chat_model", return_value=_FakeModel()
            ) as mock_init:
                result = generator.preflight_check()

            self.assertTrue(result.ok)
            self.assertEqual(result.stage, PreflightStage.PING)
            self.assertEqual(result.component_name, "simple_qa")
            self.assertEqual(result.details["llm_model"], "demo-model")
            self.assertEqual(result.details["prompt_id"], "simple_qa")
            self.assertEqual(mock_init.call_count, 1)


class SimpleQaGeneratorIntegrationTest(unittest.TestCase):
    """SimpleQaGenerator 集成测试（结构化链路 + 假 LLM）。"""

    def test_generate_with_structured_chain(self) -> None:
        """使用 StructuredChain + 假 LLM 走完整生成流程。"""
        chunk = DocumentChunk(
            chunk_id="c-real-1",
            content=(
                "Polymer X exhibits a glass transition at 120 C and a tensile "
                "strength of 35 MPa under standard conditions."
            ),
            source_doc_id="doc-real",
            section="results",
        )
        metas = [
            {
                "system_meta": {"planner": "simple", "plan_index": 1},
                "prompt_meta": {
                    "difficulty": "medium",
                    "question_type": "factual",
                    "domain": "polymer",
                },
            }
        ]

        def fake_llm(_: Any) -> AIMessage:
            return AIMessage(
                content=(
                    '{"question":"What is the tensile strength of Polymer X?",'
                    '"answer":"35 MPa.",'
                    '"evidences":["tensile strength of 35 MPa"],'
                    '"proposition_thought":"extract numeric fact",'
                    '"solution_thought":"quote value"}'
                )
            )

        prompt_template = get_prompt_manager()["chem_qa"]
        chain = StructuredChain(
            prompt_template=prompt_template,
            data_model=SimpleQaConfig().llm_output_structure,
            llm=RunnableLambda(fake_llm),
        )

        config = SimpleQaConfig(prompt_id="chem_qa")
        generator = SimpleQaGenerator(config=config)
        generator._chain = chain

        ctx = _make_context()
        qas = generator.generate([chunk], ctx, metas=metas)

        self.assertEqual(len(qas), 1)
        self.assertIn("35 MPa", qas[0].answer)
        self.assertEqual(qas[0].metadata.get("generator"), "simple_qa")
        self.assertEqual(qas[0].metadata.get("difficulty"), "medium")
        self.assertEqual(qas[0].metadata.get("question_type"), "factual")

    @unittest.skip("待接入真实 LLM 与真实题源数据")
    def test_generate_with_real_llm_and_real_content(self) -> None:
        """真实 LLM + 真实题源内容的占位测试。"""
        chunk = DocumentChunk(
            chunk_id="c-real-2",
            content=(
                "Here is a placeholder for real chemistry paper text. "
                "Replace this content with actual parsed text in W2."
            ),
            source_doc_id="doc-real-2",
            section="discussion",
        )
        metas = [
            {
                "system_meta": {"planner": "simple", "plan_index": 1},
                "prompt_meta": {
                    "difficulty": "hard",
                    "question_type": "calculation",
                },
            }
        ]

        # TODO: 替换为真实 LLM，例如 get_llm_manager()[ctx.config.llm_model]
        def fake_llm(_: Any) -> AIMessage:
            return AIMessage(
                content=(
                    '{"question":"Placeholder question?",'
                    '"answer":"Placeholder answer.",'
                    '"evidences":["placeholder evidence"],'
                    '"proposition_thought":"placeholder",'
                    '"solution_thought":"placeholder"}'
                )
            )

        prompt_template = get_prompt_manager()["chem_qa"]
        chain = StructuredChain(
            prompt_template=prompt_template,
            data_model=SimpleQaConfig().llm_output_structure,
            llm=RunnableLambda(fake_llm),
        )

        config = SimpleQaConfig(prompt_id="chem_qa")
        generator = SimpleQaGenerator(config=config)
        generator._chain = chain

        ctx = _make_context()
        qas = generator.generate([chunk], ctx, metas=metas)

        self.assertEqual(len(qas), 1)


def _make_context() -> RunContext:
    """构造最小 RunContext。"""
    base_dir = Path(tempfile.mkdtemp())
    input_dir = base_dir / "in"
    output_dir = base_dir / "out"
    temp_root = base_dir / "temp"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = RuntimeConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        mode="mock",
        doc_limit=1,
        log_level="INFO",
        temp_root_base=temp_root,
    )
    config.ensure_output_dir()
    return RunContext.from_config(config=config)
