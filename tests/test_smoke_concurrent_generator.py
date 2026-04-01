from __future__ import annotations

"""
冒烟测试：验证 concurrent_qa 生成器可接入主流程并产出 attempts manifest。
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

from tc_datasynth.core import RuntimeConfig
from tc_datasynth.core.spec import SpecConfig
from tc_datasynth.pipeline.generator.implements.structured_qa_support import (
    StructuredQaSupport,
)
from tc_datasynth.service import DataSynthService


class _SmokeAsyncChain:
    """第一条任务先失败后成功，其余任务直接成功。"""

    required_inputs = {"text", "meta"}

    def __init__(self) -> None:
        self.calls = 0
        self.calls_by_text: dict[str, int] = {}

    async def arun(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        text = str(payload.get("text") or "")
        self.calls += 1
        current_call = self.calls
        self.calls_by_text[text] = self.calls_by_text.get(text, 0) + 1
        await asyncio.sleep(0)
        if current_call == 1:
            return {
                "parse": {"question": "", "answer": "", "evidences": []},
                "error": None,
                "raw_text": "{}",
            }
        return {
            "parse": {
                "question": f"Q:{text[:12]}?",
                "answer": "A.",
                "evidences": ["E1"],
            },
            "error": None,
            "raw_text": "{}",
        }


class ConcurrentGeneratorSmokeTest(unittest.TestCase):
    """concurrent_qa 端到端冒烟测试。"""

    def test_concurrent_generator_pipeline_writes_attempt_artifacts(self) -> None:
        """主流程应跑通，并校验 generator attempts 与 manifest 一致。"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            input_dir = base_dir / "in"
            output_dir = base_dir / "out"
            temp_root = base_dir / "temp"
            input_dir.mkdir(parents=True, exist_ok=True)
            (input_dir / "sample.pdf").write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=input_dir,
                output_dir=output_dir,
                mode="mock",
                doc_limit=1,
                limit=2,
                log_level="INFO",
                temp_root_base=temp_root,
                components={
                    "generator": {
                        "name": "concurrent_qa",
                        "prompt_id": "simple_qa",
                        "llm_model": "doubao-flash",
                        "questions_per_chunk": 2,
                        "batch_size": 2,
                        "max_retries": 1,
                        "retry_backoff_ms": 0,
                    }
                },
                spec=SpecConfig(min_evidence_len=1),
            )
            config.ensure_output_dir()

            fake_chain = _SmokeAsyncChain()
            with patch.object(
                StructuredQaSupport,
                "get_chain",
                autospec=True,
                side_effect=lambda *_args, **_kwargs: fake_chain,
            ):
                service = DataSynthService(config=config)
                artifacts = service.run_sync(doc_limit=1)

            self.assertEqual(artifacts.qa_count, 2)
            records = [
                json.loads(line)
                for line in artifacts.final_qa_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(records), 2)
            self.assertTrue(all("qa_id" in record for record in records))
            self.assertTrue(
                all(record["provenance"]["generator"] == "concurrent_qa" for record in records)
            )

            attempts_path = temp_root / artifacts.run_id / "generator" / "attempts.jsonl"
            self.assertTrue(attempts_path.exists())
            attempt_rows = [
                json.loads(line)
                for line in attempts_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(attempt_rows), 3)
            self.assertEqual([row["status"] for row in attempt_rows], ["invalid_output", "success", "success"])

            generator_manifest_path = artifacts.output_dir / "manifests" / "generator.json"
            self.assertTrue(generator_manifest_path.exists())
            generator_manifest = json.loads(
                generator_manifest_path.read_text(encoding="utf-8")
            )
            self.assertEqual(generator_manifest["stage"], "generator")
            self.assertEqual(generator_manifest["entry_count"], 1)
            entry = generator_manifest["entries"][0]
            self.assertEqual(entry["backend"], "concurrent_qa")
            self.assertEqual(entry["qa_count"], 2)
            self.assertEqual(entry["attempt_count"], 3)
            self.assertEqual(Path(entry["artifact_path"]), attempts_path.resolve())
