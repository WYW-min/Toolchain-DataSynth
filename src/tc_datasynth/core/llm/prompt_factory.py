from __future__ import annotations

"""
提示词工厂：基于提示词标识加载文本模板。
"""

from pathlib import Path
from typing import Dict, Optional


class PromptFactory:
    """提示词工厂，单例模式，按标识加载提示词内容。"""

    _instance: Optional["PromptFactory"] = None

    def __new__(cls, prompt_dir: Path | str | None = None, suffix: str = ".txt"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, prompt_dir: Path | str | None = None, suffix: str = ".txt"):
        if self._initialized:
            return

        self._initialized = True
        self._prompt_dir = self._resolve_prompt_dir(prompt_dir)
        self._suffix = suffix
        self._paths: Dict[str, Path] = {}
        self._prompts: Dict[str, str] = {}
        self._discover_prompts()

    def _resolve_prompt_dir(self, prompt_dir: Path | str | None) -> Path:
        """解析提示词目录路径。"""
        if prompt_dir is None:
            root = Path(__file__).resolve().parents[4]
            return root / "configs" / "prompts"
        return Path(prompt_dir)

    def _discover_prompts(self) -> None:
        """扫描提示词目录并建立索引。"""
        if not self._prompt_dir.exists():
            raise FileNotFoundError(f"提示词目录不存在: {self._prompt_dir}")
        for path in self._prompt_dir.glob(f"*{self._suffix}"):
            self._paths[path.stem] = path

    def _normalize_id(self, prompt_id: str) -> str:
        """规范化提示词标识。"""
        if prompt_id.endswith(self._suffix):
            return Path(prompt_id).stem
        return prompt_id

    def __getitem__(self, prompt_id: str) -> str:
        """通过标识获取提示词内容（懒加载）。"""
        key = self._normalize_id(prompt_id)
        if key not in self._prompts:
            if key not in self._paths:
                available = ", ".join(sorted(self._paths.keys()))
                raise KeyError(f"提示词 '{key}' 未定义。可用提示词: {available}")
            self._prompts[key] = self._paths[key].read_text(encoding="utf-8")
        return self._prompts[key]

    def get(self, prompt_id: str, default: Optional[str] = None) -> Optional[str]:
        """安全获取提示词内容。"""
        try:
            return self[prompt_id]
        except KeyError:
            return default

    def render(self, prompt_id: str, **kwargs: object) -> str:
        """渲染提示词模板，使用 format 填充占位符。"""
        template = self[prompt_id]
        return template.format(**kwargs)

    def list_prompts(self) -> list[str]:
        """列出所有提示词标识。"""
        return sorted(self._paths.keys())

    def reload(self, prompt_dir: Path | str | None = None) -> None:
        """重新扫描提示词目录并清空缓存。"""
        if prompt_dir is not None:
            self._prompt_dir = self._resolve_prompt_dir(prompt_dir)
        self._paths.clear()
        self._prompts.clear()
        self._discover_prompts()


_prompt_factory: Optional[PromptFactory] = None


def get_prompt_factory(
    prompt_dir: Path | str | None = None, suffix: str = ".txt"
) -> PromptFactory:
    """获取提示词工厂单例。"""
    global _prompt_factory
    if _prompt_factory is None:
        _prompt_factory = PromptFactory(prompt_dir=prompt_dir, suffix=suffix)
    return _prompt_factory


def get_prompt(prompt_id: str) -> str:
    """快捷方式：获取提示词内容。"""
    return get_prompt_factory()[prompt_id]


def render_prompt(prompt_id: str, **kwargs: object) -> str:
    """快捷方式：渲染提示词模板。"""
    return get_prompt_factory().render(prompt_id, **kwargs)
