from __future__ import annotations

import tempfile
import unittest
from collections import Counter
from pathlib import Path

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import DocumentChunk
from tc_datasynth.core.spec import SpecConfig
from tc_datasynth.pipeline.planner import SimplePlanner


class SimplePlannerUnitTest(unittest.TestCase):
    """SimplePlanner 单元测试。"""

    def test_plan_keeps_target_distribution_across_batches(self) -> None:
        """分批调用时仍应维持累计分布。"""
        ctx = _make_context(
            SpecConfig(
                difficulty_profile={"easy": 0.2, "medium": 0.3, "hard": 0.5},
                question_type_mix={"definition": 0.5, "factual": 0.3, "reasoning": 0.2},
                min_evidence_len=40,
            )
        )
        planner = SimplePlanner()

        metas = planner.plan(_make_chunks(4), ctx) + planner.plan(_make_chunks(6, start=4), ctx)

        self.assertEqual(len(metas), 10)
        self.assertEqual(
            Counter(meta["prompt_meta"]["difficulty"] for meta in metas),
            Counter({"easy": 2, "medium": 3, "hard": 5}),
        )
        self.assertEqual(
            Counter(meta["prompt_meta"]["question_type"] for meta in metas),
            Counter({"definition": 5, "factual": 3, "reasoning": 2}),
        )
        self.assertEqual(
            [meta["system_meta"]["plan_index"] for meta in metas],
            list(range(1, 11)),
        )
        self.assertTrue(
            all(meta["system_meta"]["planner"] == "simple" for meta in metas)
        )

    def test_harder_labels_are_assigned_to_longer_chunks(self) -> None:
        """更高难度优先分配给更长文本。"""
        ctx = _make_context(
            SpecConfig(
                difficulty_profile={"easy": 1.0, "medium": 1.0, "hard": 1.0},
                question_type_mix={"definition": 1.0},
                min_evidence_len=1,
            )
        )
        planner = SimplePlanner()
        chunks = [
            DocumentChunk(chunk_id="c1", content="x" * 20, source_doc_id="doc"),
            DocumentChunk(chunk_id="c2", content="x" * 60, source_doc_id="doc"),
            DocumentChunk(chunk_id="c3", content="x" * 120, source_doc_id="doc"),
        ]

        metas = planner.plan(chunks, ctx)
        mapping = {
            chunk.chunk_id: meta["prompt_meta"]["difficulty"]
            for chunk, meta in zip(chunks, metas, strict=True)
        }

        self.assertEqual(mapping["c1"], "easy")
        self.assertEqual(mapping["c2"], "medium")
        self.assertEqual(mapping["c3"], "hard")

    def test_short_chunks_are_marked_as_skipped_with_hints(self) -> None:
        """极短 chunk 应被跳过，并补充轻量可读 hints。"""
        ctx = _make_context(
            SpecConfig(
                difficulty_profile={"easy": 1.0},
                question_type_mix={"definition": 1.0},
                min_evidence_len=80,
            )
        )
        planner = SimplePlanner()
        chunks = [
            DocumentChunk(chunk_id="c1", content="x" * 20, source_doc_id="doc"),
            DocumentChunk(
                chunk_id="c2",
                content="Abstract: this is a longer passage that means something important.",
                source_doc_id="doc",
            ),
        ]

        metas = planner.plan(chunks, ctx)

        self.assertFalse(metas[0]["system_meta"]["should_generate"])
        self.assertEqual(
            metas[0]["system_meta"]["skip_reason"], "below_min_evidence_window"
        )
        self.assertEqual(metas[0]["system_meta"]["length_bucket"], "short")
        self.assertTrue(metas[1]["system_meta"]["should_generate"])
        self.assertEqual(metas[1]["system_meta"]["length_bucket"], "medium")
        self.assertIn("evidence_ready", metas[1]["system_meta"])
        self.assertIn("definition_signal", metas[1]["prompt_meta"])
        self.assertEqual(metas[1]["prompt_meta"]["question_type"], "definition")


def _make_context(spec: SpecConfig) -> RunContext:
    """构造最小 RunContext。"""
    base_dir = Path(tempfile.mkdtemp())
    input_dir = base_dir / "in"
    output_dir = base_dir / "out"
    temp_root = base_dir / "temp"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = RuntimeConfig(
        input_dir=input_dir,
        output_dir=output_dir,
        mode="mock",
        doc_limit=1,
        log_level="INFO",
        temp_root_base=temp_root,
        spec=spec,
    )
    config.ensure_output_dir()
    return RunContext.from_config(config=config)


def _make_chunks(total: int, start: int = 0) -> list[DocumentChunk]:
    """构造测试用 chunk 列表。"""
    return [
        DocumentChunk(
            chunk_id=f"c{start + idx + 1}",
            content="x" * (50 + idx * 10),
            source_doc_id="doc",
            section=f"s{start + idx + 1}",
        )
        for idx in range(total)
    ]
