from __future__ import annotations

"""
数据模型定义，采用 Pydantic BaseModel，便于校验与序列化。
"""

from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SourceDocument(BaseModel):
    """输入源文档的元信息，主要用于定位文件。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    doc_id: str = Field(..., description="文档唯一标识，通常取文件名（不含后缀）")
    path: Path = Field(..., description="文档所在路径")
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="额外元数据，如来源类型"
    )


class IntermediateRepresentation(BaseModel):
    """解析后的中间表示，统一为可进一步切分的文本形态。"""

    doc_id: str = Field(..., description="对应的文档 ID")
    text: str = Field(..., description="主体文本")
    sections: List[str] | None = Field(
        default_factory=list, description="可选的章节标题列表"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="解析阶段产出的辅助信息"
    )


class DocumentChunk(BaseModel):
    """切分后的文档片段，供生成器消费。"""

    chunk_id: str = Field(..., description="片段唯一标识")
    content: str = Field(..., description="片段内容")
    source_doc_id: str = Field(..., description="对应原文档 ID")
    section: Optional[str] = Field(default=None, description="片段所属章节")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="切分策略等元信息"
    )


class QAProvenance(BaseModel):
    """QA 的追踪信息。"""

    run_id: str = Field(..., description="运行标识")
    source_doc_id: str = Field(..., description="来源文档 ID")
    chunk_id: str = Field(..., description="来源片段 ID")
    qa_index: int = Field(..., description="该 chunk 内的第几个 QA（1-based）")
    source_doc_name: Optional[str] = Field(default=None, description="来源文档名")
    source_file_name: Optional[str] = Field(default=None, description="来源文件名")
    source_path: Optional[str] = Field(default=None, description="来源文件路径")
    line_start: Optional[int] = Field(default=None, description="起始行号")
    line_end: Optional[int] = Field(default=None, description="结束行号")
    generator: Optional[str] = Field(default=None, description="生成器名称")
    planner: Optional[str] = Field(default=None, description="规划器名称")
    plan_index: Optional[int] = Field(default=None, description="规划序号")
    llm_name: Optional[str] = Field(default=None, description="模型名称")
    prompt_id: Optional[str] = Field(default=None, description="提示词模板 ID")
    extra: Optional[Dict[str, Any]] = Field(
        default=None, description="额外异常或补充追踪信息"
    )


class QAInfo(BaseModel):
    """QA 的内容与训练标签。"""

    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    evidences: List[str] = Field(..., description="溯源证据列表")
    labels: Dict[str, Any] = Field(
        default_factory=dict, description="训练标签，如难度、题型"
    )


def build_qa_id(run_id: str, source_doc_id: str, chunk_id: str, qa_index: int) -> str:
    """构造 QA 唯一标识。"""
    chunk_suffix = chunk_id
    if "__" in chunk_id:
        _, chunk_suffix = chunk_id.split("__", 1)
    return f"{run_id}__doc-{source_doc_id}__{chunk_suffix}__qa-{qa_index}"


class QAPair(BaseModel):
    """单条问答对的标准结构（对外输出/交互）。"""

    qa_id: str = Field(..., description="QA 唯一标识")
    qa_info: QAInfo = Field(..., description="QA 内容与标签")
    provenance: QAProvenance = Field(..., description="追踪信息")

    @model_validator(mode="before")
    @classmethod
    def _upgrade_legacy_payload(cls, data: Any) -> Any:
        """兼容旧版扁平结构输入。"""
        if not isinstance(data, dict):
            return data
        if "qa_id" in data and "provenance" in data and "qa_info" in data:
            return data

        question = str(data.get("question") or "")
        answer = str(data.get("answer") or "")
        evidences = data.get("evidences") or []
        source_doc_id = str(data.get("source_doc_id") or "")
        chunk_id = str(data.get("chunk_id") or "")
        metadata = data.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {"value": metadata}
        run_id = str(
            metadata.get("run_id")
            or metadata.get("runtime_run_id")
            or "run-unknown"
        )
        qa_index = int(metadata.get("qa_index") or 1)
        prompt_meta = {}
        other = metadata.get("other")
        if isinstance(other, dict):
            nested_prompt_meta = other.get("prompt_meta")
            if isinstance(nested_prompt_meta, dict):
                prompt_meta = nested_prompt_meta
        labels = {}
        for key in ("difficulty", "question_type"):
            value = metadata.get(key)
            if value in (None, ""):
                value = prompt_meta.get(key)
            if value not in (None, ""):
                labels[key] = value
        extra = {
            key: value
            for key, value in metadata.items()
            if key
            not in {
                "difficulty",
                "question_type",
                "run_id",
                "runtime_run_id",
                "qa_index",
                "source_doc_name",
                "source_file_name",
                "source_path",
                "line_start",
                "line_end",
                "generator",
                "planner",
                "plan_index",
                "llm_name",
                "prompt_id",
            }
        }
        return {
            "qa_id": data.get("qa_id")
            or build_qa_id(run_id, source_doc_id, chunk_id, qa_index),
            "provenance": {
                "run_id": run_id,
                "source_doc_id": source_doc_id,
                "chunk_id": chunk_id,
                "qa_index": qa_index,
                "source_doc_name": metadata.get("source_doc_name"),
                "source_file_name": metadata.get("source_file_name"),
                "source_path": metadata.get("source_path"),
                "line_start": metadata.get("line_start"),
                "line_end": metadata.get("line_end"),
                "generator": metadata.get("generator"),
                "planner": metadata.get("planner"),
                "plan_index": metadata.get("plan_index"),
                "llm_name": metadata.get("llm_name"),
                "prompt_id": metadata.get("prompt_id"),
                "extra": extra,
            },
            "qa_info": {
                "question": question,
                "answer": answer,
                "evidences": evidences,
                "labels": labels,
            },
        }

    @property
    def question(self) -> str:
        return self.qa_info.question

    @property
    def answer(self) -> str:
        return self.qa_info.answer

    @property
    def evidences(self) -> List[str]:
        return self.qa_info.evidences

    @property
    def source_doc_id(self) -> str:
        return self.provenance.source_doc_id

    @property
    def chunk_id(self) -> str:
        return self.provenance.chunk_id

    @property
    def metadata(self) -> Dict[str, Any]:
        """兼容旧版访问方式，聚合标签与核心追踪字段。"""
        merged: Dict[str, Any] = dict(self.qa_info.labels)
        for key in (
            "run_id",
            "qa_index",
            "generator",
            "planner",
            "plan_index",
            "llm_name",
            "prompt_id",
            "source_doc_name",
            "source_file_name",
            "source_path",
            "line_start",
            "line_end",
        ):
            value = getattr(self.provenance, key)
            if value is not None and value != "":
                merged[key] = value
        if self.provenance.extra:
            merged.update(self.provenance.extra)
        return merged


class ValidationResult(BaseModel):
    """门禁校验结果，记录错误列表。"""

    qa: QAPair = Field(..., description="被校验的 QA 记录")
    errors: List[str] = Field(default_factory=list, description="错误码列表")

    @property
    def is_valid(self) -> bool:
        """是否通过校验。"""
        return len(self.errors) == 0


class GateDecision(BaseModel):
    """门控决策结果，包含动作与错误列表。"""

    qa: QAPair = Field(..., description="被门控评估的 QA 记录")
    errors: List[str] = Field(default_factory=list, description="错误码列表")
    action: Literal["pass", "reject"] = Field(
        default="pass", description="门控动作"
    )
    stage: str = Field(default="gate", description="拦截阶段名称")

    @property
    def is_valid(self) -> bool:
        """是否通过门控。"""
        return self.action == "pass" and len(self.errors) == 0


class RunArtifacts(BaseModel):
    """单次运行的产物路径与统计。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str = Field(..., description="运行标识")
    output_dir: Path = Field(..., description="产物根目录")
    final_qa_path: Path = Field(..., description="合格 QA 输出路径")
    failed_cases_path: Path = Field(..., description="失败记录输出路径")
    report_path: Path = Field(..., description="报告输出路径")
    documents_processed: int = Field(default=0, description="处理的文档数量")
    qa_count: int = Field(default=0, description="合格 QA 数量")
    failed_count: int = Field(default=0, description="失败记录数量")
    runtime_seconds: float = Field(default=0.0, description="本次运行耗时（秒）")
