from __future__ import annotations

import json
import re
from pathlib import Path

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
from tc_datasynth.core.registrable import RegistrableComponent
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
    write_human_readable: bool = False
    human_readable_subdir: str = "sampler/human-readable"
    human_readable_max_files: int = 0


TSamplerConfig = TypeVar("TSamplerConfig", bound=SamplerConfigBase)


class SamplerRegistry:
    """采样器注册表。"""

    def __init__(self, mapping: dict[str, type["SamplerBase"]]) -> None:
        self.mapping = dict(mapping)

    def resolve(self, name: str) -> type["SamplerBase"]:
        if name not in self.mapping:
            available = ", ".join(sorted(self.mapping))
            raise KeyError(f"未知 sampler: {name}，可选值: {available}")
        return self.mapping[name]


class SamplerBase(
    RegistrableComponent,
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

        # 3.5 统一补充位置信息，便于回溯与人类审查
        if chunks:
            self._annotate_chunk_positions(chunks, filtered_ir.text or "")

        # 4. 落盘
        if self.config.write_result and chunks:
            self._write_chunks(chunks, ctx)
        if self.config.write_human_readable and chunks:
            self._write_human_readable_chunks(chunks, ctx)

        return chunks

    def _write_chunks(
        self,
        chunks: List[DocumentChunk],
        ctx: RunContext,
    ) -> Path:
        """将切分结果追加落盘到单次运行级别的 JSONL 文件。"""
        output_dir = ctx.workdir_for(subdir=self.config.output_subdir)
        output_path = output_dir / "chunks.jsonl"

        with output_path.open("a", encoding="utf-8") as f:
            for chunk in chunks:
                line = json.dumps(chunk.model_dump(), ensure_ascii=False)
                f.write(line + "\n")
        ctx.extras["sampler_output_path"] = str(output_path)
        return output_path

    def _write_human_readable_chunks(
        self,
        chunks: List[DocumentChunk],
        ctx: RunContext,
    ) -> Path:
        """将切分结果展开为人类可读的逐 chunk 文本文件。"""
        output_dir = ctx.workdir_for(subdir=self.config.human_readable_subdir)
        total = len(chunks)
        named_chunks = [
            (self._human_readable_filename(chunk), index, chunk)
            for index, chunk in enumerate(chunks)
        ]
        if self.config.human_readable_max_files > 0:
            named_chunks = sorted(
                named_chunks,
                key=lambda item: self._human_readable_sort_key(item[2], item[0], item[1]),
            )[
                : self.config.human_readable_max_files
            ]
        for file_name, index, chunk in named_chunks:
            output_path = output_dir / f"{file_name}.txt"
            output_path.write_text(
                self._format_human_readable_chunk(
                    chunk=chunk,
                    index=index,
                    total=total,
                    prev_chunk=chunks[index - 1] if index > 0 else None,
                    next_chunk=chunks[index + 1] if index + 1 < total else None,
                ),
                encoding="utf-8",
            )
        ctx.extras["sampler_human_readable_dir"] = str(output_dir)
        return output_dir

    @staticmethod
    def _safe_chunk_filename(chunk_id: str) -> str:
        """将 chunk_id 转为安全文件名。"""
        safe = "".join(
            char if char.isalnum() or char in {"-", "_"} else "_"
            for char in chunk_id
        )
        return safe or "unknown_chunk"

    @classmethod
    def _human_readable_filename(cls, chunk: DocumentChunk) -> str:
        """生成人类可读 chunk 文件名：<chunk_id>.txt。"""
        return cls._safe_chunk_filename(chunk.chunk_id)

    @staticmethod
    def _human_readable_sort_key(
        chunk: DocumentChunk,
        file_name: str,
        index: int,
    ) -> tuple[str, int, str, int]:
        """按文档主键和 chunk 序号进行自然排序。"""
        match = re.search(r"__chunk-(\d+)$", chunk.chunk_id)
        chunk_order = int(match.group(1)) if match else index
        return (chunk.source_doc_id, chunk_order, file_name, index)

    @staticmethod
    def _format_human_readable_chunk(
        chunk: DocumentChunk,
        index: int,
        total: int,
        prev_chunk: DocumentChunk | None,
        next_chunk: DocumentChunk | None,
    ) -> str:
        """格式化单个 chunk 的人类可读文本。"""
        metadata_lines = []
        for key in (
            "source_doc_name",
            "source_file_name",
            "strategy",
            "split_level",
            "unit_count",
            "char_start",
            "char_end",
            "line_start",
            "line_end",
        ):
            value = chunk.metadata.get(key)
            if value is not None:
                metadata_lines.append(f"{key}: {value}")
        if chunk.section is not None:
            metadata_lines.append(f"section: {chunk.section}")
        chunk_range = SamplerBase._chunk_line_range(chunk)
        prev_range = SamplerBase._chunk_line_range(prev_chunk)
        next_range = SamplerBase._chunk_line_range(next_chunk)
        header_lines = [
            f"chunk_id: {chunk.chunk_id}",
            f"chunk_index: {index + 1}/{total}",
            f"source_doc_id: {chunk.source_doc_id}",
            *metadata_lines,
            "",
            "chunk:",
            f"--- 前文上下文@{prev_range} ---",
            prev_chunk.content if prev_chunk else "",
            f"--- 文本块@{chunk_range} ---",
            chunk.content,
            f"--- 后文上下文@{next_range} ---",
            next_chunk.content if next_chunk else "",
            "",
        ]
        return "\n".join(header_lines)

    @staticmethod
    def _chunk_line_range(chunk: DocumentChunk | None) -> str:
        """生成 chunk 的行号范围表示。"""
        if chunk is None:
            return "-"
        line_start = chunk.metadata.get("line_start")
        line_end = chunk.metadata.get("line_end")
        if isinstance(line_start, int) and isinstance(line_end, int):
            return f"{line_start}-{line_end}"
        return "-"

    @staticmethod
    def _annotate_chunk_positions(chunks: List[DocumentChunk], text: str) -> None:
        """为 chunk 补充字符区间与行号区间。"""
        if not text:
            return
        search_cursor = 0
        for chunk in chunks:
            metadata = chunk.metadata
            start = metadata.get("char_start")
            end = metadata.get("char_end")
            if not isinstance(start, int) or not isinstance(end, int):
                start, end = SamplerBase._locate_chunk_span(
                    text=text,
                    chunk_content=chunk.content,
                    search_cursor=search_cursor,
                )
                metadata["char_start"] = start
                metadata["char_end"] = end
            metadata["line_start"] = SamplerBase._line_number_at(text, start)
            metadata["line_end"] = SamplerBase._line_number_at(
                text,
                max(start, end - 1),
            )
            search_cursor = max(search_cursor, end)

    @staticmethod
    def _locate_chunk_span(
        text: str,
        chunk_content: str,
        search_cursor: int,
    ) -> tuple[int, int]:
        """在原文中顺序定位 chunk 的字符区间。"""
        if not chunk_content:
            return search_cursor, search_cursor
        start = text.find(chunk_content, search_cursor)
        if start < 0:
            start = text.find(chunk_content.strip(), search_cursor)
        if start < 0:
            start = search_cursor
            end = min(len(text), start + len(chunk_content))
            return start, end
        return start, start + len(chunk_content)

    @staticmethod
    def _line_number_at(text: str, char_index: int) -> int:
        """计算给定字符偏移对应的 1-based 行号。"""
        if not text:
            return 1
        bounded = max(0, min(char_index, len(text)))
        return text.count("\n", 0, bounded) + 1

    @staticmethod
    def _build_source_metadata(ir: IntermediateRepresentation) -> dict:
        """提取需要透传到 chunk 的来源元数据。"""
        source_metadata: dict = {}
        for key in (
            "parsed_doc_id",
            "source_doc_name",
            "source_file_name",
            "source_path",
            "display_doc_id",
            "adapter",
        ):
            value = ir.metadata.get(key)
            if value is not None:
                source_metadata[key] = value
        return source_metadata

    def sample_batch(
        self,
        ir_list: Iterable[IntermediateRepresentation],
        ctx: RunContext,
    ) -> List[List[DocumentChunk]]:
        """批量切分 IR。"""
        return self.batch_run(ir_list, ctx)
