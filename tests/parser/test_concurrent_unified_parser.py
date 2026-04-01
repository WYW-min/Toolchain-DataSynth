from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult
from tc_datasynth.pipeline.parser import AdapterRegistry
from tc_datasynth.pipeline.parser.implements.concurrent_unified import (
    ConcurrentParserConfig,
    ConcurrentUnifiedParser,
)


class _DummyAdapter(DocumentAdapter[AdapterConfigBase]):
    component_name = "dummy"

    @classmethod
    def default_config(cls) -> AdapterConfigBase:
        return AdapterConfigBase(output_subdir="parser")

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        sleep_seconds = float(document.metadata.get("sleep_seconds", "0"))
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        workdir = ctx.workdir_for(subdir="parser") / document.path.stem
        workdir.mkdir(parents=True, exist_ok=True)
        text_path = workdir / f"{document.path.stem}.md"
        text_path.write_text(str(document.metadata.get("text", document.doc_id)), encoding="utf-8")
        return AdapterResult(
            doc_id=f"parsed-{document.doc_id}",
            adapter_name=self.get_component_name(),
            workdir=workdir,
            text_path=text_path,
            metadata={
                "source_doc_name": document.path.stem,
                "source_file_name": document.path.name,
                "source_path": str(document.path),
            },
        )


class ConcurrentUnifiedParserTest(unittest.TestCase):
    def test_parse_batch_preserves_input_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "out",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            registry = AdapterRegistry({".pdf": _DummyAdapter()})
            parser = ConcurrentUnifiedParser(
                registry=registry,
                config=ConcurrentParserConfig(max_workers=2),
            )

            docs = [
                SourceDocument(
                    doc_id="doc1",
                    path=base / "doc1.pdf",
                    metadata={"text": "first", "sleep_seconds": "0.2"},
                ),
                SourceDocument(
                    doc_id="doc2",
                    path=base / "doc2.pdf",
                    metadata={"text": "second", "sleep_seconds": "0.0"},
                ),
            ]
            for doc in docs:
                doc.path.write_text("dummy", encoding="utf-8")

            results = parser.parse_batch(docs, ctx)

            self.assertEqual([ir.text for ir in results], ["first", "second"])
            self.assertEqual([ir.doc_id for ir in results], ["parsed-doc1", "parsed-doc2"])

