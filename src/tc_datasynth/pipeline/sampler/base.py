from __future__ import annotations
import json
from pathlib import Path
from pprint import pprint

from tc_datasynth.core.context import RunContext
from tc_datasynth.pipeline.enhance.filter.base import ChunkFilterBase, TextFilterBase
from tc_datasynth.pipeline.enhance.filter.implements.simple_chunk_filter import (
    SimpleChunkFilter,
)
from tc_datasynth.pipeline.enhance.filter.implements.simple_text_filter import (
    SimpleTextFilter,
)

"""
切片采样器接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.models import DocumentChunk, IntermediateRepresentation
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


@dataclass(slots=True)
class SamplerConfigBase:
    """采样器基础配置。"""

    chunk_size: int = 400
    strip_whitespace: bool = True
    text_filter: TextFilterBase | None = field(default_factory=SimpleTextFilter)
    chunk_filter: ChunkFilterBase | None = field(default_factory=SimpleChunkFilter)
    output_subdir: str = "sampler"
    write_result: bool = True  # 是否落盘


TSamplerConfig = TypeVar("TSamplerConfig", bound=SamplerConfigBase)


class SamplerBase(
    LoopBatchMixin[IntermediateRepresentation, List[DocumentChunk]],
    ABC,
    Generic[TSamplerConfig],
):
    """切片采样器接口。"""

    config: TSamplerConfig
    single_method_name: str = "sample"

    def __init__(self, config: Optional[TSamplerConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TSamplerConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def _do_sample(self, ir: IntermediateRepresentation) -> List[DocumentChunk]:
        """核心切分逻辑，由子类实现。"""
        raise NotImplementedError

    def sample(
        self, ir: IntermediateRepresentation, ctx: RunContext
    ) -> Iterable[DocumentChunk]:
        """
        切分流程（模板方法）：
        1. 前置：文本过滤
        2. 核心：切分
        3. 后置：chunk 过滤
        4. 落盘
        """
        # 1. 文本过滤
        filtered_text = ir.text or ""
        if self.config.text_filter:
            filtered_text = self.config.text_filter.filter([filtered_text])[0]

        # 构造过滤后的 IR
        filtered_ir = IntermediateRepresentation(
            doc_id=ir.doc_id,
            text=filtered_text,
            sections=ir.sections,
            metadata={**ir.metadata, "text_filtered": True},
        )

        # 2. 核心切分
        chunks = self._do_sample(filtered_ir)

        # 3. chunk 过滤
        if self.config.chunk_filter and chunks:
            chunks = list(self.config.chunk_filter.filter(chunks))

        # 4. 落盘
        if self.config.write_result and chunks:
            self._write_chunks(chunks, ctx)

        return chunks

    def _write_chunks(
        self,
        chunks: List[DocumentChunk],
        ctx: RunContext,
    ) -> Path:
        """将切分结果落盘为 JSONL 文件。"""

        output_path = ctx.temp_root / "sampler.jsonl"

        with output_path.open("w", encoding="utf-8") as f:
            for chunk in chunks:
                line = json.dumps(chunk.model_dump(), ensure_ascii=False)
                f.write(line + "\n")
        return output_path

    def sample_batch(
        self,
        ir_list: Iterable[IntermediateRepresentation],
        ctx: RunContext,
    ) -> List[List[DocumentChunk]]:
        """批量切分 IR。"""
        return self.batch_run(ir_list, ctx)
