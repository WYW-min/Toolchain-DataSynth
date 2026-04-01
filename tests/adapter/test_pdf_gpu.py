"""
PdfGpuAdapter 单元测试。
"""

from __future__ import annotations

import hashlib
from io import BytesIO
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import requests

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.implements.pdf_gpu import (
    PdfGpuAdapter,
    PdfGpuAdapterConfig,
)
from tc_datasynth.pipeline.enhance.mixin import PreflightStage


class _DummyResponse:
    def __init__(self, content: bytes = b"", status_code: int = 200) -> None:
        self.content = content
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"http error: {self.status_code}")

    def json(self):
        return json.loads(self.content.decode("utf-8"))


def _build_mineru_zip(doc_stem: str, md_text: str) -> bytes:
    buffer = BytesIO()
    backend_dir = f"{doc_stem}/hybrid_auto"
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{backend_dir}/{doc_stem}.md", md_text)
        zip_file.writestr(
            f"{backend_dir}/{doc_stem}_middle.json",
            json.dumps({"doc": doc_stem}, ensure_ascii=False),
        )
        zip_file.writestr(f"{backend_dir}/images/figure-1.jpg", b"fake-image-bytes")
    return buffer.getvalue()


class PdfGpuAdapterTest(unittest.TestCase):
    """PDF GPU 适配器单元测试。"""

    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.get")
    def test_preflight_check_returns_ok_result(self, mock_get) -> None:
        """预检成功时应返回结构化健康结果。"""
        mock_get.return_value = _DummyResponse(b'{"status":"healthy","max_concurrent_requests":3}')

        adapter = PdfGpuAdapter(
            config=PdfGpuAdapterConfig(server_url="http://127.0.0.1:8000")
        )
        result = adapter.preflight_check()

        self.assertTrue(result.ok)
        self.assertEqual(result.component_type, "adapter")
        self.assertEqual(result.component_name, "pdf_gpu")
        self.assertEqual(result.stage, PreflightStage.SERVICE)
        self.assertEqual(result.target, "http://127.0.0.1:8000/health")
        self.assertEqual(result.details["status"], "healthy")

    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.get")
    def test_preflight_check_returns_failure_result(self, mock_get) -> None:
        """预检失败时应返回失败结果而非抛异常。"""
        mock_get.side_effect = requests.ConnectionError("connection refused")

        adapter = PdfGpuAdapter(
            config=PdfGpuAdapterConfig(server_url="http://127.0.0.1:8000")
        )
        result = adapter.preflight_check()

        self.assertFalse(result.ok)
        self.assertEqual(result.component_name, "pdf_gpu")
        self.assertEqual(result.stage, PreflightStage.SERVICE)
        self.assertEqual(result.details["error_code"], "mineru.health_unavailable")
        self.assertEqual(result.target, "http://127.0.0.1:8000/health")

    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.post")
    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.get")
    def test_parse_outputs_required_artifacts(
        self,
        mock_get,
        mock_post,
    ) -> None:
        """应通过 MinerU API ZIP 响应落出 md + middle.json + images。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf_path = base / "sample.pdf"
            pdf_path.write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            doc = SourceDocument(
                doc_id=pdf_path.stem,
                path=pdf_path,
                metadata={"src": "unit"},
            )

            mock_get.return_value = _DummyResponse(b'{"status":"healthy"}')
            md_text = "hello mineru"
            mock_post.return_value = _DummyResponse(
                _build_mineru_zip(pdf_path.stem, md_text)
            )

            adapter = PdfGpuAdapter()
            result = adapter.parse(doc, ctx)

            expected_md5 = hashlib.md5(md_text.encode("utf-8")).hexdigest()
            self.assertEqual(result.doc_id, expected_md5)
            self.assertEqual(result.adapter_name, "pdf_gpu")
            self.assertTrue(result.workdir.exists())
            self.assertEqual(result.workdir, ctx.workdir_for(subdir="parser") / "sample")
            self.assertTrue(result.text_path.exists())
            self.assertEqual(result.text_path.read_text(encoding="utf-8"), md_text)
            self.assertTrue(result.metadata["middle_json_path"].endswith("sample_middle.json"))
            self.assertEqual(result.metadata["backend"], "hybrid-auto-engine")
            self.assertEqual(result.metadata["parse_method"], "auto")
            self.assertEqual(result.metadata["src"], "unit")
            self.assertEqual(result.metadata["source_doc_name"], "sample")
            self.assertEqual(result.metadata["source_file_name"], "sample.pdf")
            self.assertEqual(result.metadata["attempt_count"], 1)
            self.assertIn("parse_task_id", result.metadata)
            self.assertTrue(Path(result.metadata["attempts_path"]).exists())
            self.assertGreaterEqual(len(result.image_files), 1)
            self.assertTrue(all(path.exists() for path in result.image_files))

    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.time.sleep")
    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.post")
    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.get")
    def test_parse_retries_then_succeeds_and_writes_attempts(
        self,
        mock_get,
        mock_post,
        mock_sleep,
    ) -> None:
        """首轮失败、次轮成功时，应按重试策略恢复并记录 attempts。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf_path = base / "retry.pdf"
            pdf_path.write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            doc = SourceDocument(doc_id=pdf_path.stem, path=pdf_path)

            mock_get.return_value = _DummyResponse(b'{"status":"healthy"}')
            md_text = "retry success"
            mock_post.side_effect = [
                requests.Timeout("boom"),
                _DummyResponse(_build_mineru_zip(pdf_path.stem, md_text)),
            ]

            adapter = PdfGpuAdapter(
                config=PdfGpuAdapterConfig(
                    max_retries=1,
                    retry_backoff_ms=1,
                )
            )
            result = adapter.parse(doc, ctx)

            self.assertEqual(result.metadata["attempt_count"], 2)
            attempts_path = Path(result.metadata["attempts_path"])
            rows = [
                json.loads(line)
                for line in attempts_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["status"], "error")
            self.assertEqual(rows[0]["error_code"], "mineru.request_timeout")
            self.assertEqual(rows[1]["status"], "success")
            self.assertIsNone(rows[1]["error_code"])
            mock_sleep.assert_called_once()

    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.time.sleep")
    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.post")
    @patch("tc_datasynth.pipeline.adapter.implements.pdf_gpu.requests.get")
    def test_parse_retry_exhaustion_raises_and_writes_attempts(
        self,
        mock_get,
        mock_post,
        mock_sleep,
    ) -> None:
        """重试耗尽时，应抛错并把 attempts 落盘。"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pdf_path = base / "fail.pdf"
            pdf_path.write_text("dummy", encoding="utf-8")

            config = RuntimeConfig(
                input_dir=base,
                output_dir=base / "outputs",
                temp_root_base=base / "temp",
                log_level="INFO",
            )
            ctx = RunContext.from_config(config)
            doc = SourceDocument(doc_id=pdf_path.stem, path=pdf_path)

            mock_get.return_value = _DummyResponse(b'{"status":"healthy"}')
            mock_post.side_effect = requests.Timeout("boom")

            adapter = PdfGpuAdapter(
                config=PdfGpuAdapterConfig(
                    max_retries=1,
                    retry_backoff_ms=1,
                )
            )

            with self.assertRaises(RuntimeError) as exc:
                adapter.parse(doc, ctx)

            self.assertIn("mineru.request_timeout", str(exc.exception))
            attempts_path = Path(ctx.extras["parser_attempts_path"])
            rows = [
                json.loads(line)
                for line in attempts_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["status"] == "error" for row in rows))
            self.assertTrue(all(row["error_code"] == "mineru.request_timeout" for row in rows))
            mock_sleep.assert_called_once()
