from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field
from pprint import pprint

from tc_datasynth.core.llm.prompt_factory import get_prompt_factory
from tc_datasynth.core.llm.structured_chain import StructuredChain
from tc_datasynth.core.llm.llm_factory import get_llm_factory
from tc_datasynth.utilities.tiny_tool import format_dict

"""
StructuredChain 单元与集成测试。
"""


class DummyQA(BaseModel):
    """用于测试的结构化输出模型。"""

    question: str = Field(..., description="问题文本")
    answer: str = Field(..., description="答案文本")
    evidence: str = Field(..., description="证据文本")


class StructuredChainUnitTest(unittest.TestCase):
    """StructuredChain 单元测试。"""

    def test_required_inputs_and_missing_key(self) -> None:
        """required_inputs 正确，缺失变量会抛错。"""

        def fake_llm(_: Any) -> str:
            return '{"question":"Q","answer":"A","evidence":"E"}'

        prompt_template = ChatPromptTemplate.from_template("Q: {text}\n{schema_define}")
        chain = StructuredChain(
            prompt_template=prompt_template,
            data_model=DummyQA,
            llm=RunnableLambda(fake_llm),
        )

        self.assertEqual(chain.required_inputs, {"text"})
        with self.assertRaises(ValueError):
            chain.run({"wrong": "x"})


class StructuredChainIntegrationTest(unittest.TestCase):
    """StructuredChain 集成测试：提示词 + 解析链。"""

    prompt_tempt = get_prompt_factory()["simple_qa"]
    llm = get_llm_factory()["doubao-flash"]

    def test_run_and_batch(self) -> None:
        """链路可使用提示词模板并解析结构化输出（mock LLM）。"""

        def fake_llm(_: Any) -> AIMessage:
            return AIMessage(content='{"question":"Q","answer":"A","evidence":"E"}')

        llm = RunnableLambda(fake_llm)
        chain = StructuredChain(
            prompt_template=self.prompt_tempt,
            data_model=DummyQA,
            llm=llm,
        )

        result = chain.run({"text": "sample"})
        self.assertIsNotNone(result)
        self.assertIn("parse", result)
        self.assertEqual(result["parse"]["answer"], "A")

        batch_result = chain.batch([{"text": "a"}, {"text": "b"}])
        self.assertEqual(len(batch_result), 2)
        self.assertEqual(batch_result[0].get("parse", {}).get("evidence"), "E")

    def test_run_arun_abatch_with_real_llm(self) -> None:
        """真实 LLM 下验证 run/arun/abatch 可用。"""
        test_text = "马斯克认为 2026 年可能实现 AGI（具备人类范围各类任务能力的 AI），并预计到 2030 年 AI 的智能总量将超越全人类之和"

        chain = StructuredChain(
            prompt_template=self.prompt_tempt, data_model=DummyQA, llm=self.llm
        )

        result = chain.run({"text": test_text})
        self.assertIsNotNone(result)
        self.assertIn("parse", result)
        self.assertIn("question", result["parse"])

        async_result = asyncio.run(chain.arun({"text": test_text}))
        pprint(f"结果<async_result>如下：\n{format_dict(async_result)}")
        self.assertIsNotNone(async_result)
        self.assertIn("parse", async_result)
        self.assertIn("question", async_result.get("parse", {}))

        batch_result = asyncio.run(
            chain.abatch([{"text": test_text}, {"text": test_text}])
        )

        pprint(f"结果<batch_result>如下：\n{format_dict(batch_result)}")
        self.assertEqual(len(batch_result), 2)
        self.assertIn("parse", batch_result[0])
        self.assertIn("question", batch_result[0].get("parse", {}))
