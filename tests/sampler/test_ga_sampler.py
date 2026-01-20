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
        """短句向后合并并按 chunk_size 贪心切分。"""
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
            self.assertEqual(len(chunks), 3)
            self.assertEqual(
                [c.content for c in chunks], ["a。bb。", "ccc。", "dddd。"]
            )
            self.assertTrue(all(c.source_doc_id == "doc-1" for c in chunks))
            self.assertTrue(all(c.section is None for c in chunks))
            self.assertTrue(
                all(c.metadata.get("strategy") == "greedy_addition" for c in chunks)
            )

            # 验证落盘产物
            chunks_file = ctx.temp_root / "sampler.jsonl"
            self.assertTrue(chunks_file.exists())
            lines = chunks_file.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), 3)
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
            chunks_file = workdir / "doc-no-write_chunks.jsonl"
            self.assertFalse(chunks_file.exists())

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
            chunks_file = ctx.temp_root / "sampler.jsonl"
            self.assertTrue(chunks_file.exists())
            self.assertGreater(chunks_file.stat().st_size, 0)

            # 验证 JSONL 格式正确
            lines = chunks_file.read_text(encoding="utf-8").strip().split("\n")
            self.assertEqual(len(lines), len(chunks))
            for i, line in enumerate(lines):
                data = json.loads(line)
                self.assertEqual(data["chunk_id"], chunks[i].chunk_id)
                self.assertEqual(data["content"], chunks[i].content)
