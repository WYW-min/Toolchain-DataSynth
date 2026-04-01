from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation
from tc_datasynth.pipeline.sampler.implements.simple_chunk import (
    SamplingConfig,
    SimpleChunkSampler,
)


class SimpleChunkSamplerTest(unittest.TestCase):
    """SimpleChunkSampler 单元测试。"""

    def _build_ctx(self) -> RunContext:
        tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(tmp_dir.cleanup)
        base = Path(tmp_dir.name)
        config = RuntimeConfig(
            input_dir=base / "in",
            output_dir=base / "out",
            temp_root_base=base / "temp",
            log_level="INFO",
        )
        return RunContext.from_config(config)

    def test_short_text_keeps_single_chunk_without_ellipsis(self) -> None:
        """短文本不应添加截断标识。"""
        ctx = self._build_ctx()
        sampler = SimpleChunkSampler(SamplingConfig(chunk_size=10))
        ir = IntermediateRepresentation(
            doc_id="doc-short",
            text="abcdefgh",
            sections=[],
            metadata={},
        )

        chunks = list(sampler.sample(ir, ctx))

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content, "abcdefgh")
        self.assertEqual(chunks[0].chunk_id, "doc-short__chunk-1")
        self.assertFalse(chunks[0].metadata["truncated_prefix"])
        self.assertFalse(chunks[0].metadata["truncated_suffix"])

    def test_long_text_uses_prefix_and_suffix_ellipsis(self) -> None:
        """长文本切块时，中间块应带前后截断标识。"""
        ctx = self._build_ctx()
        sampler = SimpleChunkSampler(
            SamplingConfig(
                chunk_size=10,
                text_filter=None,
                chunk_filter=None,
            )
        )
        ir = IntermediateRepresentation(
            doc_id="doc-long",
            text="abcdefghijklmnopqrstuvwxyz",
            sections=[],
            metadata={},
        )

        chunks = list(sampler.sample(ir, ctx))

        self.assertEqual(
            [chunk.content for chunk in chunks],
            [
                "abcdefg...",
                "...hijk...",
                "...lmno...",
                "...pqrs...",
                "...tuvwxyz",
            ],
        )
        self.assertEqual(chunks[0].chunk_id, "doc-long__chunk-1")
        self.assertEqual(chunks[-1].chunk_id, "doc-long__chunk-5")
        self.assertTrue(all(len(chunk.content) <= 10 for chunk in chunks))
        self.assertFalse(chunks[0].metadata["truncated_prefix"])
        self.assertTrue(chunks[0].metadata["truncated_suffix"])
        self.assertTrue(chunks[1].metadata["truncated_prefix"])
        self.assertTrue(chunks[1].metadata["truncated_suffix"])
        self.assertTrue(chunks[-1].metadata["truncated_prefix"])
        self.assertFalse(chunks[-1].metadata["truncated_suffix"])

    def test_chunk_size_too_small_raises(self) -> None:
        """过小的 chunk_size 应显式失败。"""
        ctx = self._build_ctx()
        sampler = SimpleChunkSampler(
            SamplingConfig(
                chunk_size=6,
                text_filter=None,
                chunk_filter=None,
            )
        )
        ir = IntermediateRepresentation(
            doc_id="doc-small",
            text="abcdefghijklmnopqrstuvwxyz",
            sections=[],
            metadata={},
        )

        with self.assertRaisesRegex(ValueError, "chunk_size 过小"):
            list(sampler.sample(ir, ctx))
