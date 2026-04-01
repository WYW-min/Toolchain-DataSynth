from __future__ import annotations

"""
简单 QA 生成器：基于提示词 + 结构化输出的最小可用实现。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Type

from pydantic import BaseModel, Field

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.llm.structured_chain import StructuredChain
from tc_datasynth.core.models import DocumentChunk, QAPair
from tc_datasynth.pipeline.enhance.mixin import PreflightCheckMixin, PreflightCheckResult
from tc_datasynth.pipeline.generator.base import GeneratorConfigBase, QAGeneratorBase
from tc_datasynth.pipeline.generator.implements.structured_qa_support import (
    StructuredQaSupport,
)


class _SimpleQaOutput(BaseModel):
    """LLM 输出的最小结构化格式。"""

    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    evidences: List[str] = Field(..., description="直接证据")
    proposition_thought: str = Field(..., description="命题思考过程")
    solution_thought: str = Field(..., description="解题思考过程")

@dataclass(slots=True)
class SimpleQaConfig(GeneratorConfigBase):
    """简单生成器配置。"""

    prompt_id: str = "simple_qa"
    questions_per_chunk: int = 1  # 每个chunk的问题数量
    llm_model: str = "doubao_flash"
    llm_config_path: Path = Path("configs/llm.toml")
    llm_output_structure: Type[BaseModel] = _SimpleQaOutput


class SimpleQaGenerator(
    QAGeneratorBase[SimpleQaConfig],
    PreflightCheckMixin,
):
    """W2 的最小 LLM 生成器，实现稳定的 QA 产出。"""

    component_name = "simple_qa"

    def __init__(self, config: SimpleQaConfig | None = None) -> None:
        """初始化生成器。"""
        super().__init__(config)
        self.support = StructuredQaSupport()

    @property
    def _chain(self) -> StructuredChain | None:
        """兼容测试中的链路注入。"""
        return self.support._chain

    @_chain.setter
    def _chain(self, value: StructuredChain | None) -> None:
        self.support._chain = value

    @classmethod
    def default_config(cls) -> SimpleQaConfig:
        """返回默认配置。"""
        return SimpleQaConfig()

    def preflight_check(self) -> PreflightCheckResult:
        """执行轻量生成器预检。"""
        return self.support.run_preflight_check(
            llm_config_path=self.config.llm_config_path,
            llm_model=self.config.llm_model,
            prompt_id=self.config.prompt_id,
            component_name=self.get_component_name(),
        )

    def generate(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
        metas: List[Dict[str, Any]] | None = None,
    ) -> List[QAPair]:
        """基于 chunk 生成 QA，支持 chunk 级元信息列表。"""
        chain = self.support.get_chain(
            ctx=ctx,
            prompt_id=self.config.prompt_id,
            llm_model=self.config.llm_model,
            llm_output_structure=self.config.llm_output_structure,
        )
        chunk_list = list(chunks)
        qa_pairs: List[QAPair] = []
        metas = self.support.normalize_metas(metas, len(chunk_list))
        per_chunk = max(1, int(self.config.questions_per_chunk))
        qa_limit = ctx.extras.get("generator_qa_limit")
        remaining = int(qa_limit) if isinstance(qa_limit, int) and qa_limit > 0 else None

        for chunk, meta in zip(chunk_list, metas, strict=True):
            payload = self.support.build_payload(
                chain=chain,
                chunk=chunk,
                meta=meta,
            )
            for qa_index in range(1, per_chunk + 1):
                result = chain.run(payload) or {}
                qa_pairs.append(
                    self.support.build_qa(
                        chunk=chunk,
                        result=result,
                        ctx=ctx,
                        meta=meta,
                        qa_index=qa_index,
                        generator_name="simple_qa",
                        llm_model=self.config.llm_model,
                        prompt_id=self.config.prompt_id,
                    )
                )
                self.notify_progress(ctx)
                if remaining is not None and len(qa_pairs) >= remaining:
                    return qa_pairs[:remaining]
        return qa_pairs
