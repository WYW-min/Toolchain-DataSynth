from __future__ import annotations

"""
LLM 链路封装：提示词 + 模型 + 结构化解析。
"""

import asyncio
import re
from typing import Any, Dict, Iterable, List, Tuple, Type

from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate

from langchain_core.output_parsers import PydanticOutputParser


class MyChain:
    """简化版结构化输出链封装。"""

    def __init__(
        self,
        prompt_text: str,
        data_model: Type[BaseModel],
        llm: Any,
    ) -> None:
        """初始化 MyChain，仅依赖提示词文本与模型实例。"""
        self._parser = PydanticOutputParser(pydantic_object=data_model)
        self._prompt = self._build_prompt(prompt_text).partial(
            schema_define=self._parser.get_format_instructions()
        )
        self._llm = llm
        self.chain = self._prompt | self._llm | self._parser

    def run(self, input_data: Dict[str, Any]) -> BaseModel | None:
        """同步执行链路，返回最后一次解析结果。"""
        results = list(self.chain.stream(input_data))
        if not results:
            return None
        return results[-1]

    def batch(self, input_datas: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """同步批量执行，并统一返回字典结构。"""
        results: List[Dict[str, Any]] = []
        for input_data in input_datas:
            try:
                chain_response = self.run(input_data)
                final_data = self.get_final_data(chain_response)
            except Exception as exc:  # pragma: no cover - 防御性处理
                final_data = self.get_final_data(exc)
            results.append(final_data)
        return results

    async def arun(
        self, input_data: Dict[str, Any]
    ) -> BaseModel | Dict[str, Any] | None:
        """异步执行链路，返回最后一次解析结果。"""
        results = [item async for item in self.chain.astream(input_data)]
        if not results:
            return None
        if isinstance(results[-1], Exception):
            return {"error": str(results[-1])}
        return results[-1]

    async def abatch(
        self, input_datas: Iterable[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """异步批量执行，使用并发调用聚合结果。"""
        coroutine_list = [self.arun(data) for data in input_datas]
        chain_results = await asyncio.gather(*coroutine_list, return_exceptions=True)
        return [self.get_final_data(result) for result in chain_results]

    @staticmethod
    def get_final_data(
        chain_response: BaseModel | Exception | object,
    ) -> Dict[str, Any]:
        """统一解析链路输出为字典结构。"""
        if isinstance(chain_response, Exception):
            return {"error": str(chain_response)}
        if isinstance(chain_response, BaseModel):
            return chain_response.model_dump(mode="json")
        if chain_response is None:
            return {}
        if isinstance(chain_response, dict):
            return chain_response
        return {"value": chain_response}

    def _build_prompt(self, prompt_text: str) -> ChatPromptTemplate:
        """根据提示词文本构建 ChatPromptTemplate。"""
        blocks = self._parse_prompt_blocks(prompt_text)
        if not blocks:
            return ChatPromptTemplate.from_template(prompt_text)
        return ChatPromptTemplate.from_messages(blocks)

    @staticmethod
    def _parse_prompt_blocks(prompt_text: str) -> List[Tuple[str, str]]:
        """解析 <system>/<user>/<assistant> 块。"""
        pattern = re.compile(
            r"<(system|user|assistant)>\s*(.*?)\s*</\1>", re.IGNORECASE | re.DOTALL
        )
        matches = pattern.findall(prompt_text)
        if not matches:
            return []
        return [(role.lower(), content.strip()) for role, content in matches]
