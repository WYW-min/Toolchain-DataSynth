from __future__ import annotations

"""
适配器输出契约。
"""

from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class AdapterResult(BaseModel):
    """
    适配器输出结果，包含中间文件路径与元信息。
    中间产物一般在  temp_root/adapter/<doc_id>/
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    doc_id: str = Field(..., description="文档标识（文件名）")
    adapter_name: str = Field(..., description="适配器名称")
    workdir: Path = Field(..., description="适配器工作目录")
    text_path: Path = Field(..., description="纯文本文件路径")
    table_files: List[Path] = Field(default_factory=list, description="表格文件列表")
    image_files: List[Path] = Field(default_factory=list, description="图片文件列表")
    metadata: Dict[str, str] = Field(default_factory=dict, description="解析阶段元数据")
