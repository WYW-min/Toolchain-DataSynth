"""
GreedyAdditionSampler 单元/集成测试。
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation
from tc_datasynth.pipeline.sampler.implements.ga_sampler import (
    GreedyAdditionSampler,
    GreedyAdditionSamplingConfig,
)


class GreedyAdditionSamplerTest(unittest.TestCase):
    """贪心追加采样器测试。"""

    def test_greedy_merge_short_sentences(self) -> None:
        """短句按锚点长度与误差反馈进行句级打包。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)

            sampler_config = GreedyAdditionSamplingConfig(
                chunk_size=8,
                separators=["。"],
                min_sentence_len=3,
                strip_whitespace=True,
                text_filter=None,  # 禁用过滤，专注测试切分逻辑
                chunk_filter=None,
            )
            sampler = GreedyAdditionSampler(sampler_config)
            ir = IntermediateRepresentation(
                doc_id="doc-1",
                text="a。bb。ccc。dddd。",
                sections=[],
                metadata={},
            )

            chunks = sampler.sample(ir, ctx)

            # 验证切分结果
            self.assertEqual(len(chunks), 2)
            self.assertEqual([c.content for c in chunks], ["a。bb。ccc。", "dddd。"])
            self.assertTrue(all(c.source_doc_id == "doc-1" for c in chunks))
            self.assertTrue(all(c.section is None for c in chunks))
            self.assertTrue(
                all(c.metadata.get("strategy") == "greedy_addition" for c in chunks)
            )
            self.assertTrue(
                all(c.metadata.get("split_level") == "sentence" for c in chunks)
            )
            self.assertEqual(chunks[0].chunk_id, "doc-1__chunk-0")
            self.assertEqual(chunks[-1].chunk_id, "doc-1__chunk-1")

            # 验证落盘产物
            chunks_file = ctx.workdir_for(subdir="sampler") / "chunks.jsonl"
            self.assertTrue(chunks_file.exists())
            lines = chunks_file.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), 2)
            for line in lines:
                data = json.loads(line)
                self.assertIn("chunk_id", data)
                self.assertIn("content", data)

    def test_write_result_disabled(self) -> None:
        """验证 write_result=False 时不落盘。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)

            sampler_config = GreedyAdditionSamplingConfig(
                chunk_size=100,
                text_filter=None,
                chunk_filter=None,
                write_result=False,  # 禁用落盘
            )
            sampler = GreedyAdditionSampler(sampler_config)
            ir = IntermediateRepresentation(
                doc_id="doc-no-write",
                text="测试文本。不需要落盘。",
                sections=[],
                metadata={},
            )

            chunks = sampler.sample(ir, ctx)

            self.assertGreater(len(chunks), 0)
            # 验证没有落盘
            workdir = ctx.workdir_for(subdir="sampler")
            chunks_file = workdir / "chunks.jsonl"
            self.assertFalse(chunks_file.exists())

    def test_write_human_readable_outputs_chunk_files(self) -> None:
        """开启 human-readable 后，应为每个 chunk 写出文本文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)

            sampler = GreedyAdditionSampler(
                GreedyAdditionSamplingConfig(
                    chunk_size=8,
                    separators=["。"],
                    min_sentence_len=3,
                    text_filter=None,
                    chunk_filter=None,
                    write_human_readable=True,
                )
            )
            ir = IntermediateRepresentation(
                doc_id="doc-readable",
                text="a。bb。ccc。dddd。",
                sections=[],
                metadata={"source_doc_name": "paper-a"},
            )

            chunks = list(sampler.sample(ir, ctx))

            human_dir = ctx.workdir_for(subdir="sampler/human-readable")
            self.assertTrue(human_dir.exists())
            first_chunk_file = human_dir / f"{chunks[0].chunk_id}.txt"
            self.assertTrue(first_chunk_file.exists())
            self.assertEqual(len(list(human_dir.glob("*.txt"))), len(chunks))
            content = first_chunk_file.read_text(encoding="utf-8")
            self.assertIn(f"chunk_id: {chunks[0].chunk_id}", content)
            self.assertIn("chunk_index: 1/2", content)
            self.assertIn("source_doc_id: doc-readable", content)
            self.assertIn("source_doc_name: paper-a", content)
            self.assertIn("line_start: 1", content)
            self.assertIn("chunk:", content)
            self.assertIn("--- 前文上下文@- ---", content)
            self.assertIn("--- 文本块@1-1 ---", content)
            self.assertIn("--- 后文上下文@1-1 ---", content)
            self.assertIn(chunks[1].content, content)
            self.assertIn(chunks[0].content, content)

    def test_write_human_readable_respects_max_files(self) -> None:
        """human_readable_max_files 应按 chunk 序号自然截取前 N 个。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)

            sampler = GreedyAdditionSampler(
                GreedyAdditionSamplingConfig(
                    chunk_size=8,
                    separators=["。"],
                    min_sentence_len=3,
                    text_filter=None,
                    chunk_filter=None,
                    write_human_readable=True,
                    human_readable_max_files=2,
                )
            )
            ir = IntermediateRepresentation(
                doc_id="doc-readable",
                text="a。bb。ccc。dddd。",
                sections=[],
                metadata={},
            )

            chunks = list(sampler.sample(ir, ctx))

            human_dir = ctx.workdir_for(subdir="sampler/human-readable")
            actual_names = sorted(path.name for path in human_dir.glob("*.txt"))
            expected_names = [f"{chunk.chunk_id}.txt" for chunk in chunks[:2]]
            self.assertEqual(actual_names, expected_names)

    def test_greedy_integration_with_fixture(self) -> None:
        """使用真实 md 文件验证切分输出与落盘。"""
        fixture = Path("tests/fixtures/advs.202415937-cpu.md")
        if not fixture.exists():
            self.skipTest("缺少测试文本: tests/fixtures/advs.202415937-cpu.md")

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)

            text = fixture.read_text(encoding="utf-8")
            ir = IntermediateRepresentation(
                doc_id=fixture.stem,
                text=text,
                sections=[],
                metadata={},
            )
            sampler_config = GreedyAdditionSamplingConfig(
                chunk_size=800,
                min_sentence_len=10,
            )
            sampler = GreedyAdditionSampler(sampler_config)

            chunks = sampler.sample(ir, ctx)

            # 验证切分结果
            self.assertGreater(len(chunks), 1)
            self.assertTrue(all(chunk.content for chunk in chunks))
            self.assertTrue(
                all(chunk.source_doc_id == fixture.stem for chunk in chunks)
            )

            # 验证落盘产物
            chunks_file = ctx.workdir_for(subdir="sampler") / "chunks.jsonl"
            self.assertTrue(chunks_file.exists())
            self.assertGreater(chunks_file.stat().st_size, 0)

            # 验证 JSONL 格式正确
            lines = chunks_file.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), len(chunks))
            for i, line in enumerate(lines):
                data = json.loads(line)
                self.assertEqual(data["chunk_id"], chunks[i].chunk_id)
                self.assertEqual(data["content"], chunks[i].content)

    def test_chunks_are_appended_to_run_level_file(self) -> None:
        """多个文档的 chunks 应追加到同一个运行级文件。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            sampler = GreedyAdditionSampler(
                GreedyAdditionSamplingConfig(
                    chunk_size=100,
                    text_filter=None,
                    chunk_filter=None,
                )
            )

            first_ir = IntermediateRepresentation(
                doc_id="doc-1",
                text="第一份文档。",
                sections=[],
                metadata={},
            )
            second_ir = IntermediateRepresentation(
                doc_id="doc-2",
                text="第二份文档。",
                sections=[],
                metadata={},
            )

            first_chunks = list(sampler.sample(first_ir, ctx))
            second_chunks = list(sampler.sample(second_ir, ctx))

            chunks_file = ctx.workdir_for(subdir="sampler") / "chunks.jsonl"
            self.assertTrue(chunks_file.exists())
            lines = chunks_file.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), len(first_chunks) + len(second_chunks))
            payloads = [json.loads(line) for line in lines]
            self.assertEqual(payloads[0]["source_doc_id"], "doc-1")
            self.assertEqual(payloads[-1]["source_doc_id"], "doc-2")

    def test_prefers_blank_line_boundaries_before_sentence_boundaries(self) -> None:
        """应先按双换行分段，再进行句级回退。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            sampler = GreedyAdditionSampler(
                GreedyAdditionSamplingConfig(
                    chunk_size=10,
                    min_sentence_len=1,
                    paragraph_separators=["\n\n"],
                    text_filter=None,
                    chunk_filter=None,
                )
            )
            ir = IntermediateRepresentation(
                doc_id="doc-lines",
                text="aaaa。\n\nbbbb。",
                sections=[],
                metadata={},
            )

            chunks = list(sampler.sample(ir, ctx))

            self.assertEqual([chunk.content for chunk in chunks], ["aaaa。", "bbbb。"])
            self.assertEqual(
                [chunk.metadata.get("split_level") for chunk in chunks],
                ["paragraph", "paragraph"],
            )

    def test_oversize_sentence_is_kept_as_single_chunk(self) -> None:
        """单句超长时应保留整句，不做字符级截断。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            sampler = GreedyAdditionSampler(
                GreedyAdditionSamplingConfig(
                    chunk_size=5,
                    separators=["。"],
                    paragraph_separators=["\n\n"],
                    text_filter=None,
                    chunk_filter=None,
                )
            )
            ir = IntermediateRepresentation(
                doc_id="doc-fallback",
                text="abcdefghijk",
                sections=[],
                metadata={},
            )

            chunks = list(sampler.sample(ir, ctx))

            self.assertEqual([chunk.content for chunk in chunks], ["abcdefghijk"])
            self.assertTrue(
                all(chunk.metadata.get("strategy") == "greedy_addition" for chunk in chunks)
            )
            self.assertTrue(
                all(chunk.metadata.get("split_level") == "sentence" for chunk in chunks)
            )

    def test_find_soft_break_prefers_soft_breaks(self) -> None:
        """字符兜底工具应优先在空白等软边界附近切分。"""
        sampler = GreedyAdditionSampler(
            GreedyAdditionSamplingConfig(
                chunk_size=8,
                separators=["。"],
                paragraph_separators=["\n\n"],
                text_filter=None,
                chunk_filter=None,
            )
        )

        next_cursor = sampler._find_soft_break("alpha beta gamma", 0, 8)

        self.assertEqual(next_cursor, 6)
