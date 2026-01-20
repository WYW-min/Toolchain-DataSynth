from __future__ import annotations

"""
批处理通用 Mixins：提供可复用的批量执行策略。
"""

from abc import ABC
from typing import Callable, Generic, Iterable, List, TypeVar

TIn = TypeVar("TIn")
TOut = TypeVar("TOut")


class BatchMixinBase(ABC, Generic[TIn, TOut]):
    """批处理 Mixin 基类，统一管理方法绑定与校验逻辑。"""

    single_method_name: str = ""

    def _resolve_method(self) -> Callable[..., TOut]:
        """解析并返回目标方法。"""
        if not self.single_method_name:
            raise ValueError("single_method_name 不能为空")
        method = getattr(self, self.single_method_name, None)
        if method is None:
            raise AttributeError(f"未找到方法: {self.single_method_name}")
        return method


class LoopBatchMixin(BatchMixinBase[TIn, TOut], ABC):
    """批处理 Mixin：串行循环逐条执行（基于方法名绑定）。"""

    def _run_single(self, item: TIn, *args, **kwargs) -> TOut:
        """根据方法名调用单条接口。"""
        method = self._resolve_method()
        return method(item, *args, **kwargs)

    def batch_run(self, items: Iterable[TIn], *args, **kwargs) -> List[TOut]:
        """批量执行：默认循环调用 _run_single。"""
        return [self._run_single(item, *args, **kwargs) for item in items]


class MultiprocessBatchMixin(LoopBatchMixin[TIn, TOut], ABC):
    """多进程批处理 Mixin，占位实现，当前行为等同 LoopBatchMixin。"""

    pass

class MultithreadBatchMixin(LoopBatchMixin[TIn, TOut], ABC):
    """多线程批处理 Mixin，占位实现，当前行为等同 LoopBatchMixin。"""

    pass

