"""
PDF GPU 适配器：外部 MinerU HTTP 服务客户端。

当前阶段不直接 import mineru，也不负责拉起 MinerU 服务；
仅负责 HTTP 调用、最小重试和结果落盘。
"""

from dataclasses import dataclass, field
import hashlib
from io import BytesIO
import json
from pathlib import Path
import shutil
import time
import zipfile

import requests

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import SourceDocument
from tc_datasynth.pipeline.adapter.base import AdapterConfigBase, DocumentAdapter
from tc_datasynth.pipeline.adapter.types import AdapterResult
from tc_datasynth.pipeline.enhance.mixin import (
    PreflightCheckMixin,
    PreflightCheckResult,
    PreflightStage,
)


@dataclass(slots=True)
class MineruParseOptions:
    """MinerU 解析选项，独立于具体调用方式。"""

    backend: str = "hybrid-auto-engine"
    parse_method: str = "auto"
    formula_enable: bool = True
    table_enable: bool = True
    lang_list: list[str] = field(default_factory=lambda: ["ch"])
    start_page_id: int = 0
    end_page_id: int = 99999


@dataclass(slots=True)
class PdfGpuAdapterConfig(AdapterConfigBase):
    """MinerU 客户端配置。"""

    server_url: str = "http://127.0.0.1:8000"
    api_docs_path: str = "/docs"
    health_path: str = "/health"
    parse_path: str = "/file_parse"
    timeout_seconds: int = 300
    poll_interval_seconds: float = 2.0
    max_retries: int = 1
    retry_backoff_ms: int = 500
    parse_options: MineruParseOptions = field(default_factory=MineruParseOptions)


class PdfGpuAdapterError(RuntimeError):
    """带标准错误码的 MinerU 调用异常。"""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class PdfGpuAdapter(
    DocumentAdapter[PdfGpuAdapterConfig],
    PreflightCheckMixin,
):
    """W2 使用的 GPU PDF 解析器（外部 HTTP 服务客户端）。"""

    component_name = "pdf_gpu"

    @classmethod
    def default_config(cls) -> PdfGpuAdapterConfig:
        """返回默认配置。"""
        return PdfGpuAdapterConfig()

    def parse(self, document: SourceDocument, ctx: RunContext) -> AdapterResult:
        """调用外部 MinerU HTTP 服务并将返回结果落到 parser 目录。"""
        parser_root = ctx.workdir_for(subdir=self.config.output_subdir)
        doc_root = parser_root / document.path.stem
        parse_task_id = f"{ctx.run_id}__parse__{document.path.stem}"
        attempt_rows: list[dict[str, str | int | None]] = []
        last_error: PdfGpuAdapterError | None = None

        for attempt in range(1, self.config.max_retries + 2):
            self._reset_doc_root(doc_root)
            try:
                self._ensure_service_healthy()
                response_bytes = self._request_parse_zip(document)
                self._extract_zip(response_bytes, parser_root)
                text_path, middle_json_path, image_files = self._locate_required_results(
                    doc_root
                )
                content = text_path.read_text(encoding="utf-8")
                content_md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
                attempt_rows.append(
                    self._make_attempt_row(
                        parse_task_id=parse_task_id,
                        document=document,
                        attempt=attempt,
                        status="success",
                        error_code=None,
                        error_message=None,
                    )
                )
                attempts_path = self._write_attempt_rows(ctx, attempt_rows)
                return AdapterResult(
                    doc_id=content_md5,
                    adapter_name=self.get_component_name(),
                    workdir=doc_root,
                    text_path=text_path,
                    table_files=[],
                    image_files=image_files,
                    metadata={
                        "md5": content_md5,
                        "parsed_text_md5": content_md5,
                        "source_doc_name": document.path.stem,
                        "source_file_name": document.path.name,
                        "source_path": str(document.path),
                        "middle_json_path": str(middle_json_path),
                        "artifact_root": str(doc_root),
                        "backend": self.config.parse_options.backend,
                        "parse_method": self.config.parse_options.parse_method,
                        "parse_task_id": parse_task_id,
                        "attempt_count": attempt,
                        "attempts_path": str(attempts_path),
                        **document.metadata,
                    },
                )
            except PdfGpuAdapterError as exc:
                last_error = exc
                attempt_rows.append(
                    self._make_attempt_row(
                        parse_task_id=parse_task_id,
                        document=document,
                        attempt=attempt,
                        status="error",
                        error_code=exc.code,
                        error_message=str(exc),
                    )
                )
                if attempt <= self.config.max_retries:
                    time.sleep(self.config.retry_backoff_ms / 1000)

        attempts_path = self._write_attempt_rows(ctx, attempt_rows)
        raise RuntimeError(
            f"MinerU 解析失败: task={parse_task_id}, code={last_error.code if last_error else 'mineru.unknown'}, "
            f"attempts={len(attempt_rows)}, attempts_path={attempts_path}"
        ) from last_error

    def preflight_check(self) -> PreflightCheckResult:
        """执行 MinerU 服务预检。"""
        health_url = self._build_url(self.config.health_path)
        try:
            response = requests.get(health_url, timeout=self.config.timeout_seconds)
            response.raise_for_status()
            details = self._load_json_safely(response)
            return PreflightCheckResult(
                component_type="adapter",
                component_name=self.get_component_name(),
                ok=True,
                stage=PreflightStage.SERVICE,
                message="MinerU 服务可用",
                target=health_url,
                details=details,
            )
        except requests.Timeout:
            return PreflightCheckResult(
                component_type="adapter",
                component_name=self.get_component_name(),
                ok=False,
                stage=PreflightStage.SERVICE,
                message="MinerU 服务健康检查超时",
                target=health_url,
                details={"error_code": "mineru.health_timeout"},
            )
        except requests.RequestException as exc:
            return PreflightCheckResult(
                component_type="adapter",
                component_name=self.get_component_name(),
                ok=False,
                stage=PreflightStage.SERVICE,
                message=f"MinerU 服务不可用: {exc}",
                target=health_url,
                details={"error_code": "mineru.health_unavailable"},
            )

    def _ensure_service_healthy(self) -> None:
        """检查 MinerU 服务是否可用。"""
        health_url = self._build_url(self.config.health_path)
        docs_url = self._build_url(self.config.api_docs_path)
        try:
            response = requests.get(health_url, timeout=self.config.timeout_seconds)
            response.raise_for_status()
        except requests.Timeout as exc:
            raise PdfGpuAdapterError(
                "mineru.health_timeout",
                f"MinerU 服务健康检查超时: {health_url}",
            ) from exc
        except requests.RequestException as exc:
            raise PdfGpuAdapterError(
                "mineru.health_unavailable",
                f"MinerU 服务不可用: {health_url}。请先确认服务已启动，并参考 {docs_url}"
            ) from exc

    @staticmethod
    def _load_json_safely(response: requests.Response) -> dict[str, object]:
        """尽量从响应中解析 JSON。"""
        try:
            payload = response.json()
        except ValueError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _request_parse_zip(self, document: SourceDocument) -> bytes:
        """调用同步解析接口并返回 ZIP 二进制内容。"""
        parse_url = self._build_url(self.config.parse_path)
        with document.path.open("rb") as file_obj:
            files = {
                "files": (document.path.name, file_obj, "application/pdf"),
            }
            data = {
                "backend": self.config.parse_options.backend,
                "parse_method": self.config.parse_options.parse_method,
                "formula_enable": str(self.config.parse_options.formula_enable).lower(),
                "table_enable": str(self.config.parse_options.table_enable).lower(),
                "lang_list": self.config.parse_options.lang_list,
                "return_md": "true",
                "return_middle_json": "true",
                "return_images": "true",
                "response_format_zip": "true",
                "start_page_id": str(self.config.parse_options.start_page_id),
                "end_page_id": str(self.config.parse_options.end_page_id),
            }
            try:
                response = requests.post(
                    parse_url,
                    files=files,
                    data=data,
                    timeout=self.config.timeout_seconds,
                )
                response.raise_for_status()
            except requests.Timeout as exc:
                raise PdfGpuAdapterError(
                    "mineru.request_timeout",
                    f"调用 MinerU 解析超时: {parse_url}",
                ) from exc
            except requests.HTTPError as exc:
                raise PdfGpuAdapterError(
                    "mineru.http_error",
                    f"调用 MinerU 解析返回异常状态: {parse_url}",
                ) from exc
            except requests.RequestException as exc:
                raise PdfGpuAdapterError(
                    "mineru.request_failed",
                    f"调用 MinerU 解析失败: {parse_url}",
                ) from exc
        return response.content

    @staticmethod
    def _extract_zip(content: bytes, output_root: Path) -> None:
        """将返回的 ZIP 内容解压到目标目录。"""
        try:
            with zipfile.ZipFile(BytesIO(content)) as zip_file:
                zip_file.extractall(output_root)
        except zipfile.BadZipFile as exc:
            raise PdfGpuAdapterError(
                "mineru.invalid_zip",
                "MinerU 返回结果不是有效 ZIP 文件",
            ) from exc

    @staticmethod
    def _locate_required_results(doc_root: Path) -> tuple[Path, Path, list[Path]]:
        """定位最小必需产物：md + middle.json + images。"""
        if not doc_root.exists():
            raise PdfGpuAdapterError(
                "mineru.output_dir_missing",
                f"MinerU 输出目录不存在: {doc_root}",
            )

        md_files = sorted(doc_root.rglob("*.md"))
        if not md_files:
            raise PdfGpuAdapterError(
                "mineru.missing_markdown",
                f"MinerU 结果中缺少 markdown 文件: {doc_root}",
            )
        text_path = md_files[0]

        middle_json_files = sorted(doc_root.rglob("*_middle.json"))
        if not middle_json_files:
            raise PdfGpuAdapterError(
                "mineru.missing_middle_json",
                f"MinerU 结果中缺少 middle.json 文件: {doc_root}",
            )
        middle_json_path = middle_json_files[0]

        image_files = sorted(
            path for path in doc_root.rglob("*") if path.is_file() and "images" in path.parts
        )
        if not image_files:
            raise PdfGpuAdapterError(
                "mineru.missing_images",
                f"MinerU 结果中缺少 images 目录或图片文件: {doc_root}",
            )

        return text_path, middle_json_path, image_files

    def _build_url(self, path: str) -> str:
        """拼接服务地址。"""
        return self.config.server_url.rstrip("/") + path

    @staticmethod
    def _reset_doc_root(doc_root: Path) -> None:
        """确保单文档输出目录每次尝试前为干净状态。"""
        if doc_root.exists():
            shutil.rmtree(doc_root)
        doc_root.mkdir(parents=True, exist_ok=True)

    def _make_attempt_row(
        self,
        *,
        parse_task_id: str,
        document: SourceDocument,
        attempt: int,
        status: str,
        error_code: str | None,
        error_message: str | None,
    ) -> dict[str, str | int | None]:
        """构造单次解析尝试记录。"""
        return {
            "parse_task_id": parse_task_id,
            "doc_id": document.doc_id,
            "source_file_name": document.path.name,
            "attempt": attempt,
            "status": status,
            "error_code": error_code,
            "error": error_message,
            "adapter": self.get_component_name(),
        }

    def _write_attempt_rows(
        self,
        ctx: RunContext,
        attempt_rows: list[dict[str, str | int | None]],
    ) -> Path:
        """将本轮解析 attempt 记录追加写入 parser 中间产物。"""
        output_dir = ctx.workdir_for(subdir=self.config.output_subdir)
        output_path = output_dir / "attempts.jsonl"
        with output_path.open("a", encoding="utf-8") as f:
            for row in attempt_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        ctx.extras["parser_attempts_path"] = str(output_path)
        ctx.extras["parser_attempts_count"] = int(
            ctx.extras.get("parser_attempts_count", 0)
        ) + len(attempt_rows)
        return output_path
