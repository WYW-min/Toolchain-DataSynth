from __future__ import annotations

"""
数据模型定义，采用 Pydantic BaseModel，便于校验与序列化。
"""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SourceDocument(BaseModel):
    """输入源文档的元信息，主要用于定位文件。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    doc_id: str = Field(..., description="文档唯一标识，通常取文件名（不含后缀）")
    path: Path = Field(..., description="文档所在路径")
    metadata: Dict[str, str] = Field(default_factory=dict, description="额外元数据，如来源类型")


class IntermediateRepresentation(BaseModel):
    """解析后的中间表示，统一为可进一步切分的文本形态。"""

    doc_id: str = Field(..., description="对应的文档 ID")
    text: str = Field(..., description="主体文本")
    sections: List[str] = Field(default_factory=list, description="可选的章节标题列表")
    metadata: Dict[str, str] = Field(default_factory=dict, description="解析阶段产出的辅助信息")


class DocumentChunk(BaseModel):
    """切分后的文档片段，供生成器消费。"""

    chunk_id: str = Field(..., description="片段唯一标识")
    content: str = Field(..., description="片段内容")
    source_doc_id: str = Field(..., description="对应原文档 ID")
    section: Optional[str] = Field(default=None, description="片段所属章节")
    metadata: Dict[str, str] = Field(default_factory=dict, description="切分策略等元信息")


class QAPair(BaseModel):
    """单条问答对的标准结构（对外输出/交互）。"""

    question: str = Field(..., description="问题")
    answer: str = Field(..., description="答案")
    evidence: str = Field(..., description="溯源证据文本")
    source_doc_id: str = Field(..., description="来源文档 ID")
    chunk_id: str = Field(..., description="来源片段 ID")
    metadata: Dict[str, str] = Field(default_factory=dict, description="生成或校验时的元信息")

    def to_jsonable(self) -> Dict[str, object]:
        """以 dict 形式返回，便于 JSON/JSONL 落盘。"""
        return self.model_dump()


class ValidationResult(BaseModel):
    """门禁校验结果，记录错误列表。"""

    qa: QAPair = Field(..., description="被校验的 QA 记录")
    errors: List[str] = Field(default_factory=list, description="错误码列表")

    @property
    def is_valid(self) -> bool:
        """是否通过校验。"""
        return len(self.errors) == 0


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
