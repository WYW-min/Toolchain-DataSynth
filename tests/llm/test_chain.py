from __future__ import annotations

"""
MyChain 单元与集成测试。
"""

import unittest
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from tc_datasynth.core.llm.chain import MyChain


class DummyQA(BaseModel):
    """用于测试的结构化输出模型。"""

    question: str = Field(...)
    answer: str = Field(...)
    evidence: str = Field(...)


class MyChainUnitTest(unittest.TestCase):
    """MyChain 单元测试。"""

    def test_get_final_data_from_model(self) -> None:
        """模型输出可转为字典结构。"""
        data = DummyQA(question="Q", answer="A", evidence="E")
        result = MyChain.get_final_data(data)
        self.assertEqual(result["question"], "Q")
        self.assertEqual(result["answer"], "A")

    def test_get_final_data_from_exception(self) -> None:
        """异常输出可转为 error 字段。"""
        result = MyChain.get_final_data(ValueError("boom"))
        self.assertEqual(result["error"], "boom")


class MyChainIntegrationTest(unittest.TestCase):
    """MyChain 集成测试：提示词 + 解析链。"""

    def test_run_and_batch(self) -> None:
        """链路可使用提示词模板并解析结构化输出。"""
        prompt_path = (
            Path(__file__).resolve().parents[2]
            / "configs"
            / "prompts"
            / "simple_qa.txt"
        )
        prompt_text = prompt_path.read_text(encoding="utf-8")

        def fake_llm(_: Any) -> str:
            return '{"question":"Q","answer":"A","evidence":"E"}'

        llm = RunnableLambda(fake_llm)
        chain = MyChain(
            prompt_text=prompt_text,
            data_model=DummyQA,
            llm=llm,
        )

        result = chain.run({"text": "sample"})
        self.assertIsInstance(result, DummyQA)
        self.assertEqual(result.answer, "A")

        batch_result = chain.batch([{"text": "a"}, {"text": "b"}])
        self.assertEqual(len(batch_result), 2)
        self.assertEqual(batch_result[0]["evidence"], "E")
