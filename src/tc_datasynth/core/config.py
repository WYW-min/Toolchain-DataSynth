from __future__ import annotations

"""
运行期配置：使用 Pydantic BaseModel 统一校验与加载。
"""

import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from tc_datasynth.core.spec import SpecConfig


class RuntimeConfig(BaseModel):
    """运行期可配置项，支持 TOML 与 CLI 参数组合。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    input_dir: Path = Field(..., description="PDF 输入目录")
    output_dir: Path = Field(..., description="运行产物输出目录")
    mode: str = Field(default="mock", description="运行模式，预留后续扩展")
    max_docs: Optional[int] = Field(default=None, description="限制处理的文档数量")
    parse_batch_size: Optional[int] = Field(default=1, description="解析批处理数量（1=流式，None=全量）")
    generate_batch_size: Optional[int] = Field(default=1, description="生成批处理数量（1=流式，None=全量）")
    mock_questions_per_doc: int = Field(default=3, description="mock 模式每个文档生成的 QA 数量")
    seed: int = Field(default=7, description="随机种子")
    log_level: str = Field(default="INFO", description="日志级别")
    temp_root_base: Path = Field(default=Path("data/temp"), description="临时工作目录根路径")
    spec: SpecConfig = Field(default_factory=SpecConfig, description="用户配置的 Spec")

    @staticmethod
    def normalize_batch_size(value: object | None, default: Optional[int] = 1) -> Optional[int]:
        """规范化批处理大小：None/0/负数表示全量。"""
        if value is None:
            return default
        if isinstance(value, str):
            text = value.strip().lower()
            if text in {"none", "null", "all"}:
                return None
            try:
                value = int(text)
            except ValueError:
                return default
        try:
            number = int(value)
        except (TypeError, ValueError):
            return default
        if number <= 0:
            return None
        return number

    @classmethod
    def from_toml(cls, path: Path) -> "RuntimeConfig":
        """从 TOML 文件加载运行配置。"""
        raw = tomllib.loads(path.read_text())
        runtime = raw.get("runtime", {})
        spec_raw = raw.get("spec", {})
        return cls(
            input_dir=Path(runtime.get("input_dir", ".")),
            output_dir=Path(runtime.get("output_dir", "outputs")),
            mode=runtime.get("mode", "mock"),
            max_docs=runtime.get("max_docs"),
            parse_batch_size=cls.normalize_batch_size(runtime.get("parse_batch_size", 1), default=1),
            generate_batch_size=cls.normalize_batch_size(runtime.get("generate_batch_size", 1), default=1),
            mock_questions_per_doc=runtime.get("mock_questions_per_doc", 3),
            seed=runtime.get("seed", 7),
            log_level=runtime.get("log_level", "INFO"),
            temp_root_base=Path(runtime.get("temp_root_base", "data/temp")),
            spec=SpecConfig.model_validate(spec_raw) if spec_raw else SpecConfig(),
        )

    def ensure_output_dir(self) -> Path:
        """确保输出目录存在并返回路径。"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir
