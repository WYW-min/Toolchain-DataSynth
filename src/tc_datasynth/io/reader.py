from __future__ import annotations

"""
输入读取：发现文档并生成 SourceDocument 列表。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Iterable, List, Optional, TypeVar

from tc_datasynth.core.models import SourceDocument
from tc_datasynth.core.registrable import RegistrableComponent


@dataclass(slots=True)
class ReaderConfigBase:
    """读取器基础配置。"""

    input_dir: Path
    suffixes: tuple[str, ...] = (".pdf",)


TReaderConfig = TypeVar("TReaderConfig", bound=ReaderConfigBase)


class ReaderBase(RegistrableComponent, ABC, Generic[TReaderConfig]):
    """输入读取器接口。"""

    config: TReaderConfig

    def __init__(self, config: Optional[TReaderConfig] = None) -> None:
        self.config = config or self.default_config()

    @classmethod
    @abstractmethod
    def default_config(cls) -> TReaderConfig:
        """返回默认配置。"""
        raise NotImplementedError

    @abstractmethod
    def discover(self, limit: Optional[int] = None) -> List[SourceDocument]:
        """遍历目录收集文档，可选限制数量。"""
        raise NotImplementedError


@dataclass(slots=True)
class SimpleReaderConfig(ReaderConfigBase):
    """Simple 读取器配置。"""

    pass


class SimpleDocumentReader(ReaderBase[SimpleReaderConfig]):
    """最小实现：按后缀从目录发现文档。"""

    component_name = "simple"

    def __init__(
        self,
        input_dir: Optional[Path] = None,
        suffixes: Optional[Iterable[str]] = None,
        config: Optional[SimpleReaderConfig] = None,
    ) -> None:
        """初始化读取器，指定输入目录与允许的后缀。"""
        if input_dir is None and config is None:
            raise ValueError("input_dir 不能为空，或传入 ReaderConfigBase")
        cfg = config or SimpleReaderConfig(
            input_dir=input_dir if input_dir is not None else Path("."),
            suffixes=tuple(suffixes) if suffixes else (".pdf",),
        )
        super().__init__(cfg)

    @classmethod
    def default_config(cls) -> SimpleReaderConfig:
        """返回默认配置。"""
        return SimpleReaderConfig(input_dir=Path("."), suffixes=(".pdf",))

    def discover(self, limit: Optional[int] = None) -> List[SourceDocument]:
        """遍历目录收集文档，可选限制数量。"""
        docs: List[SourceDocument] = []
        for path in sorted(self.config.input_dir.rglob("*")):
            if not path.is_file():
                continue
            if not path.suffix.lower() in self.config.suffixes:
                continue
            doc_id = path.stem
            docs.append(SourceDocument(doc_id=doc_id, path=path, metadata={"source": path.suffix.lstrip(".")}))
            if limit and len(docs) >= limit:
                break
        return docs
