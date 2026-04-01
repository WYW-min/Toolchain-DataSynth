from __future__ import annotations

"""
统一解析器公共支持逻辑。
"""

from tc_datasynth.core.context import RunContext
from tc_datasynth.core.models import IntermediateRepresentation, SourceDocument
from tc_datasynth.pipeline.adapter import AdapterResult
from tc_datasynth.pipeline.parser.base import AdapterRegistry


def parse_document_to_ir(
    registry: AdapterRegistry,
    document: SourceDocument,
    ctx: RunContext,
    *,
    encoding: str,
) -> IntermediateRepresentation:
    """调用适配器并读取文本文件，生成统一 IR。"""
    adapter = registry.resolve(document)
    result: AdapterResult = adapter.parse(document, ctx)
    text = result.text_path.read_text(encoding=encoding)
    source_doc_name = result.metadata.get("source_doc_name") or document.path.stem
    return IntermediateRepresentation(
        doc_id=result.doc_id,
        text=text,
        sections=[source_doc_name],
        metadata={
            "parsed_doc_id": result.doc_id,
            "source_doc_name": source_doc_name,
            "source_file_name": result.metadata.get("source_file_name")
            or document.path.name,
            "source_path": result.metadata.get("source_path")
            or str(document.path),
            "display_doc_id": document.doc_id,
            "adapter": result.adapter_name,
            "text_path": str(result.text_path),
            "workdir": str(result.workdir),
            **result.metadata,
        },
    )
