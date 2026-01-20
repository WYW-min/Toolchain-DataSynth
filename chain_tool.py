import asyncio
from pathlib import Path
from typing import Any, Dict, List
from pydantic import BaseModel
from cetc_product.config.llm_factory import llm_manager
from langchain_core.prompts import ChatPromptTemplate
from cetc_product.tools.json_parser import MyJSONParser
from cetc_product.tools.IO_tool import load_prompt


class MyChain:

    def __init__(self, prompt_path: Path, data_model: BaseModel, llm_name="qwen"):

        self.main_llm = llm_manager[llm_name]
        self.prompt_temp = load_prompt(prompt_path, schema_define_cls=data_model)
        self.syn_parser = MyJSONParser(data_model)
        self.chain = (
            self.prompt_temp.partial(
                schema_define=self.syn_parser.get_format_instructions()
            )
            | self.main_llm
            | self.syn_parser
        )

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        results = list(self.chain.stream(input_data))
        if not results:
            return None
        else:
            return results[-1]

    def batch(self, input_datas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """同步批量处理"""
        results = []
        for input_data in input_datas:
            try:
                chain_response = self.run(input_data)
                final_data = self.get_final_data(chain_response)
            except Exception as e:
                final_data = self.get_final_data(e)
            results.append(final_data)
        return results

    async def arun(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        results = [item async for item in self.chain.astream(input_data)]
        if not results:
            return None
        elif isinstance(results[-1], Exception):
            return {"error": str(results[-1])}
        else:
            return results[-1]

    async def abatch(self, input_datas):
        ga_coroutine = [self.arun(i) for i in input_datas]
        ga_coroutine_results = await asyncio.gather(
            *ga_coroutine, return_exceptions=True
        )
        final_data = [
            self.get_final_data(run_chain_result)
            for run_chain_result in ga_coroutine_results
        ]
        return final_data

    @staticmethod
    def get_final_data(chain_response: BaseModel | Exception) -> dict:
        if isinstance(chain_response, Exception):
            chain_response = {"error": str(chain_response)}

        elif isinstance(chain_response, BaseModel):
            chain_response = chain_response.model_dump(mode="json")

        return chain_response
