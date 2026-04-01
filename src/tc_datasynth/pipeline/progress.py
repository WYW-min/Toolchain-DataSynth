from __future__ import annotations

"""
进度管理：统一封装 tqdm 进度条的创建与更新。
"""

from dataclasses import dataclass

from tqdm import tqdm


@dataclass(slots=True)
class ProgressTracker:
    """进度追踪器，维护总进度与阶段进度。"""

    total_docs: int
    total_progress: tqdm
    parse_progress: tqdm
    generate_progress: tqdm

    @classmethod
    def create(cls, total_docs: int) -> "ProgressTracker":
        """创建进度追踪器。"""
        return cls(
            total_docs=total_docs,
            total_progress=tqdm(total=total_docs, desc="总体进度", unit="step", position=0),
            parse_progress=tqdm(total=total_docs, desc="解析文档", unit="doc", position=1),
            generate_progress=tqdm(total=0, desc="生成问答", unit="qa", position=2),
        )

    def add_generate_total(self, count: int) -> None:
        """动态扩展生成阶段总量。"""
        if count <= 0:
            return
        self.generate_progress.total = int(self.generate_progress.total or 0) + count
        self.generate_progress.refresh()
        self.total_progress.total = int(self.total_progress.total or 0) + count
        self.total_progress.refresh()

    def update_parse(self, count: int = 1) -> None:
        """更新解析阶段进度。"""
        self.parse_progress.update(count)
        self.total_progress.update(count)

    def update_generate(self, count: int = 1) -> None:
        """更新生成阶段进度。"""
        self.generate_progress.update(count)
        self.total_progress.update(count)

    def close(self) -> None:
        """关闭所有进度条。"""
        self.parse_progress.close()
        self.generate_progress.close()
        self.total_progress.close()
