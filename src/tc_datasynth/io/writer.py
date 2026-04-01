from __future__ import annotations

"""
产物写入：FinalQA / FailedCases 落盘。
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Iterable, List, Optional, Tuple, TypeVar

from tc_datasynth.core.models import QAPair
from tc_datasynth.core.registrable import RegistrableComponent


@dataclass(slots=True)
class WriterConfigBase:
    """写入器基础配置。"""

    output_dir: Path


TWriterConfig = TypeVar("TWriterConfig", bound=WriterConfigBase)


class WriterBase(RegistrableComponent, ABC, Generic[TWriterConfig]):
    """写入器接口。"""

    config: TWriterConfig

    def __init__(self, config: Optional[TWriterConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TWriterConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def prepare(self, run_id: str) -> None:
        """准备输出目录。"""
        raise NotImplementedError

    @abstractmethod
    def write(self, final_records: Iterable[QAPair], failed_records: List[dict]) -> Tuple[Path, Path]:
        """写入产物并返回路径。"""
        raise NotImplementedError


@dataclass(slots=True)
class SimpleWriterConfig(WriterConfigBase):
    """Simple 写入器配置。"""

    pass


class SimpleQAWriter(WriterBase[SimpleWriterConfig]):
    """负责将产物输出到指定目录。"""

    component_name = "simple"

    def __init__(self, output_dir: Optional[Path] = None, config: Optional[SimpleWriterConfig] = None) -> None:
        """初始化写入器，设置基础输出目录。"""
        if output_dir is None and config is None:
            raise ValueError("output_dir 不能为空，或传入 WriterConfigBase")
        cfg = config or SimpleWriterConfig(output_dir=output_dir if output_dir is not None else Path("."))
        super().__init__(cfg)
        self.base_output_dir = self.config.output_dir
        self.output_dir = self.config.output_dir

    @classmethod
    def default_config(cls) -> SimpleWriterConfig:
        """返回默认配置。"""
        return SimpleWriterConfig(output_dir=Path("."))

    def prepare(self, run_id: str) -> None:
        """创建本次运行的子目录。"""
        self.output_dir = self.base_output_dir / run_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, final_records: Iterable[QAPair], failed_records: List[dict]) -> Tuple[Path, Path]:
        """写入合格与失败的记录到 JSONL。"""
        final_path = self.output_dir / "FinalQA.jsonl"
        failed_path = self.output_dir / "FailedCases.jsonl"

        with final_path.open("w", encoding="utf-8") as final_out:
            for record in final_records:
                final_out.write(
                    json.dumps(
                        record.model_dump(mode="json", exclude_none=True),
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        with failed_path.open("w", encoding="utf-8") as failed_out:
            for record in failed_records:
                failed_out.write(json.dumps(record, ensure_ascii=False) + "\n")

        return final_path, failed_path
