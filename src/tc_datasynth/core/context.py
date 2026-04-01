from __future__ import annotations

"""
运行上下文：封装本次运行的全局状态（配置、日志、临时目录等）。
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field

from tc_datasynth.core.config import RuntimeConfig
from tc_datasynth.core.logging import configure_logger
from tc_datasynth.core.plan import PlanConfig
from tc_datasynth.core.planning import MockPlanCompiler, PlanCompiler
from tc_datasynth.core.spec import SpecConfig


class RunContext(BaseModel):
    """本次运行的上下文，集中管理外部参数与状态。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    run_id: str = Field(..., description="运行标识")
    temp_root: Path = Field(..., description="临时工作目录根路径（含 run_id）")
    log_file: Path = Field(..., description="本次运行的日志文件路径")
    config: RuntimeConfig = Field(..., description="运行配置")
    spec: SpecConfig = Field(..., description="本次运行的 Spec")
    plan: PlanConfig = Field(..., description="本次运行的 Plan")
    logger: Any = Field(..., description="日志句柄")
    extras: Dict[str, Any] = Field(
        default_factory=dict, description="跨组件共享的临时状态"
    )

    @classmethod
    def from_config(
        cls,
        config: RuntimeConfig,
        run_id: str | None = None,
        logger: Any | None = None,
        compiler: PlanCompiler | None = None,
    ) -> "RunContext":
        """基于配置创建上下文，并创建默认的临时目录与日志文件。"""
        rid = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        temp_root = Path(config.temp_root_base) / rid
        temp_root.mkdir(parents=True, exist_ok=True)

        logs_root = Path(config.logs_root_base)
        logs_root.mkdir(parents=True, exist_ok=True)
        log_file_path = logs_root / f"{rid}.log"

        log = logger or configure_logger(config.log_level, log_file=log_file_path)

        spec = config.spec or SpecConfig()
        plan_compiler = compiler or MockPlanCompiler()
        try:
            plan = plan_compiler.compile(spec)
        except Exception as exc:
            log.warning(f"Plan 编译失败，已回退默认计划: {exc}")
            plan = MockPlanCompiler().compile(SpecConfig())

        latest_link = Path("latest.log")  # 项目根目录软链

        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()
        try:
            latest_link.symlink_to(log_file_path)
        except OSError:
            ...

        return cls(
            run_id=rid,
            temp_root=temp_root,
            log_file=log_file_path,
            config=config,
            logger=log,
            spec=spec,
            plan=plan,
        )

    def workdir_for(self, subdir: str = "adapter") -> Path:
        """获取（并创建）某文档的工作子目录。"""
        path = self.temp_root / subdir
        path.mkdir(parents=True, exist_ok=True)
        return path
