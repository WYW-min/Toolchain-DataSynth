from __future__ import annotations

"""
QA 生成器接口。
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk, QAPair
from tc_datasynth.core.registrable import RegistrableComponent
from tc_datasynth.pipeline.enhance.mixin.batch import LoopBatchMixin


@dataclass(slots=True)
class GeneratorConfigBase:
    """生成器基础配置。"""

    seed: int = 0


TGeneratorConfig = TypeVar("TGeneratorConfig", bound=GeneratorConfigBase)


# runner主流程中未进行调用更新
class QAGeneratorBase(
    RegistrableComponent,
    LoopBatchMixin[List[DocumentChunk], List[QAPair]], ABC, Generic[TGeneratorConfig]
):
    """QA 生成器接口。"""

    config: TGeneratorConfig
    single_method_name: str = "generate"

    def __init__(self, config: TGeneratorConfig | None = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TGeneratorConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def generate(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
        metas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[QAPair]:
        """基于 chunk 生成 QA 列表，可传入 chunk 级元信息列表。"""
        raise NotImplementedError

    def generate_batch(
        self,
        batch_chunks: Iterable[Iterable[DocumentChunk]],
        ctx: RunContext,
        metas: Optional[List[List[Dict[str, Any]]]] = None,
    ) -> List[List[QAPair]]:
        """批量生成 QA，默认循环调用 generate。"""
        if metas is None:
            return self.batch_run(batch_chunks, ctx, None)
        return [self.generate(chunks, ctx, meta) for chunks, meta in zip(batch_chunks, metas)]

    async def agenerate(
        self,
        chunks: Iterable[DocumentChunk],
        ctx: RunContext,
        metas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[QAPair]:
        """异步接口，默认回落到同步 generate。"""
        return self.generate(chunks, ctx, metas=metas)

    async def agenerate_batch(
        self,
        batch_chunks: Iterable[Iterable[DocumentChunk]],
        ctx: RunContext,
        metas: Optional[List[List[Dict[str, Any]]]] = None,
    ) -> List[List[QAPair]]:
        """异步批量接口，默认并发回落到 agenerate。"""
        batch_list = list(batch_chunks)
        meta_list = metas or [None] * len(batch_list)
        tasks = [
            self.agenerate(chunks, ctx, metas=meta)
            for chunks, meta in zip(batch_list, meta_list, strict=True)
        ]
        return await asyncio.gather(*tasks)

    @staticmethod
    def notify_progress(ctx: RunContext, count: int = 1) -> None:
        """通知运行时更新生成阶段进度。"""
        callback = ctx.extras.get("generator_progress_callback")
        if callable(callback):
            callback(count)
