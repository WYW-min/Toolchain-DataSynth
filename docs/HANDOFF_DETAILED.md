# TC-DataSynth 详细交接文档

先说阅读顺序：

1. 接手第一天，不要先看这份文档
2. 先看 [`docs/QUICKSTART.md`](./QUICKSTART.md)
3. 先把 `pixi run preflight --config configs/w2_demo.toml` 跑通
4. 再把 `pixi run w2-demo` 跑通
5. 只有在已经跑通后，再回来读这份文档

这份文档面向的是：

- 需要维护仓库的人
- 需要理解模块边界和阶段演进的人

不是给第一次上手时直接照着执行命令用的。

## 1. 项目定位

TC-DataSynth 是一个面向 PDF 文档的 QA 合成工具链。当前仓库已经从早期 mock 骨架推进到真实链路可用状态，具备：

1. 真实 PDF 解析
2. 真实 LLM 生成
3. 基础质量门禁
4. 中间产物可追踪
5. 预检与一键运行入口

当前更适合被理解为：

- 一个 workflow-first 的数据合成系统
- 具备向 agent-ready 编排演进的结构基础

## 2. 阶段划分

### W1

目标：

- 跑通 mock 流程
- 建立 `Spec -> Plan -> Pipeline` 基本骨架

结果：

- CLI 可跑
- 基础组件边界建立
- mock 数据与基础报告可产出

### W2

目标：

- 跑通真实 PDF + 真实 LLM
- 补齐最小质量闭环
- 提供交付级入口

结果：

- `pdf_gpu(MinerU HTTP)` 接入
- `simple_qa / concurrent_qa`
- `validator + gate`
- `preflight`
- `w2-demo`

### W3

建议方向：

1. 提升 evidence 质量
2. 扩展失败回流和报告
3. 在真实批量场景下重新评估 parser 并发
4. 向 orchestration / agent-ready 继续演进

## 3. 默认运行方案

当前默认方案：

- `pdf_gpu + simple_unified + concurrent_qa`
- 配置文件：[`configs/w2_demo.toml`](../configs/w2_demo.toml)

选择原因：

1. 相比 `simple_qa`，`concurrent_qa` 显著降低总耗时
2. 相比 `full_concurrent`，默认链路更稳定、更容易解释
3. 在单文档演示场景下，parser 并发没有体现出默认启用价值

## 3.1 LLM 配置说明

LLM 配置入口：

- [`configs/llm.toml`](../configs/llm.toml)

环境变量模板：

- [`configs/llm_manager.env.example`](../configs/llm_manager.env.example)

当前约定是：

- `configs/llm.toml` 中的 `settings.env_path` 默认写成 `configs/llm_manager.env`
- 该路径优先按“项目根目录相对路径”解析
- 仓库不会提交真实的 `configs/llm_manager.env`

接手时需要先执行：

```bash
cp configs/llm_manager.env.example configs/llm_manager.env
```

再填写实际模型密钥和 base url。

## 4. 整体设计

### 4.1 主流程

主流程是：

1. Reader
2. Adapter / Parser
3. Sampler
4. Planner
5. Generator
6. Gate / Validator
7. Writer / Reporting

### 4.2 RunContext 与 temp_root

`RunContext` 是一次运行的共享上下文，当前集中管理：

- `run_id`
- `temp_root`
- `log_file`
- `RuntimeConfig`
- `Spec`
- `Plan`
- `logger`
- `extras`

其中：

- `run_id`：本次运行的唯一标识
- `temp_root`：本次运行的中间结果根目录，默认是 `data/temp/<run_id>`

这层设计的作用是：

1. 让各组件共享统一运行状态
2. 把中间产物按 `run_id` 归档到同一棵目录下
3. 避免每个组件自己决定日志、临时目录和共享状态的组织方式

当前 parser / sampler / planner / generator / gate 的中间结果，都围绕 `RunContext.temp_root` 落盘。

### 4.3 核心原则

1. `Spec -> Plan`
2. 组件可替换
3. 中间产物可追踪
4. 真实链路与 mock 链路共存

### 4.4 Spec -> Plan 的设计意图

这层设计现在仍然是仓库的核心约束之一。

- `Spec`：用户目标，回答“想要什么”
- `Plan`：执行计划，回答“系统准备怎么做”

当前 `Spec` 里主要是：

- 难度分布
- 题型分布
- `min_evidence_len`

这些内容在运行开始时会被编译成 `Plan`，并写入：

- `RunContext.plan`

这样做的目的有两个：

1. 让下游组件只消费统一计划，而不是直接依赖原始 TOML 细节
2. 让“用户目标”和“执行策略”分开，便于后续替换 planner / generator / gate 实现

### 4.5 仓库根目录层级

接手时建议先把仓库根目录理解成下面几块：

- `configs/`
  - 运行配置、LLM 配置、prompt 模板
- `data/`
  - 输入、输出、中间结果
  - 当前默认演示输入在 `data/in/pdf_demo`
- `docs/`
  - 交接文档、架构说明、阶段说明
- `scripts/`
  - 一键运行、MinerU 服务辅助、清理脚本
- `src/`
  - 主代码
- `tests/`
  - 单元测试、集成测试、smoke
- `docker/`
  - MinerU 外部组件的参考部署资料
- `logs/`
  - 运行日志

如果只按交接视角看，最常接触的目录是：

1. `configs/`
2. `data/`
3. `scripts/`
4. `src/`
5. `tests/`

## 5. 模块介绍与代码结构总览

当前代码结构可以按“入口层 -> 服务层 -> 核心层 -> 流水线组件层 -> 报告层 -> 测试层”来理解。

### `src/tc_datasynth/access/`

入口层：

- `cli_app.py`
- `api_app.py`
- `components_app.py`
- `preflight_app.py`

### `src/tc_datasynth/service.py`

服务层，负责：

- 组件装配
- 预检入口
- 主流程运行入口

### `src/tc_datasynth/core/`

这是**核心基础设施层**，主要回答：

- 系统怎么保存配置
- 一次运行的共享上下文是什么
- 通用数据模型怎么定义
- LLM 调用能力怎么封装

这一层不直接负责业务流水线步骤，而是给上层提供公共能力。

核心内容包括：

- `config.py`
- `context.py`
- `models.py`
- `spec.py`
- `plan.py`
- `planning.py`
- `llm/`
- `registrable.py`

其中：

- `config.py`
  - 负责读取 TOML 并构造运行配置
- `context.py`
  - 定义 `RunContext`
- `models.py`
  - 定义运行期和产物相关的数据模型
- `spec.py`
  - 定义用户目标配置
- `plan.py`
  - 定义执行计划结构
- `planning.py`
  - 负责把 `Spec` 编译成 `Plan`
- `llm/`
  - 管理 prompt、模型工厂、结构化调用链
- `registrable.py`
  - 给组件注册提供统一能力

### `src/tc_datasynth/pipeline/`

这是**可替换的流水线组件层**，主要回答：

- 文档怎么解析
- 文本怎么切块
- 出题大纲怎么规划
- QA 怎么生成
- 质量怎么校验

大部分业务能力演进都会落在这一层。

核心内容包括：

- `adapter/`
- `parser/`
- `sampler/`
- `planner/`
- `generator/`
- `validator/`
- `gate/`
- `runner.py`
- `batching.py`
- `progress.py`
- `components.py`
- `enhance/`

其中当前最关键的实现路径是：

- `adapter/`
  - 单文档解析能力单元
  - `mock_pdf`
  - `pdf_cpu`
  - `pdf_gpu`
- `parser/`
  - 批量解析编排层
  - `simple_unified`
  - `concurrent_unified`
- `sampler/`
  - 基于 IR 组织 chunk
  - `simple_chunk`
  - `greedy_addition`
- `planner/`
  - 负责为 chunk 分配出题纲要
  - `simple`
- `generator/`
  - 负责把 chunk + meta 变成最终 QA
  - `mock`
  - `simple_qa`
  - `concurrent_qa`
- `validator/`
  - 原子校验器
  - `simple_schema`
  - `evidence`
  - `label`
- `gate/`
  - 聚合 validator 结果并做 `pass/reject`
  - `simple_composite`
- `runner.py`
  - 运行总编排
- `batching.py`
  - 分批处理与阶段衔接
- `progress.py`
  - 进度条和运行进度展示
- `components.py`
  - 运行期组件容器
- `enhance/`
  - 放横切增强能力，目前主要是 mixin / filter 这类支撑模块

### `src/tc_datasynth/reporting/`

运行结果汇总：

- `report_writer.py`
- `manifest_writer.py`

### `src/tc_datasynth/io/`

输入输出：

- `reader.py`
  - 输入发现
- `writer.py`
  - 最终 QA / failed cases 落盘

### `src/tc_datasynth/tools/`

辅助工具：

- `compare_runs.py`
  - 对照不同运行结果的摘要统计

### `tests/`

测试按组件和链路分层，详细说明见后文的“测试目录”小节。

## 6. 当前关键实现

### 6.1 PDF 解析

支持：

- `pdf_cpu`
- `pdf_gpu`

其中 `pdf_gpu` 是通过 MinerU HTTP 服务接入，当前仓库只负责：

- 调用
- 预检
- 结果接入

不负责 MinerU 服务端运维。

当前默认方案使用的是：

- `pdf_gpu`

但 `pdf_cpu` 仍然建议保留，因为它有两个明确用途：

1. MinerU 服务不可用时的回退解析路径
2. 调试“仓库接入逻辑”和“外部服务依赖”时的隔离对照

如果后续需要走回退路线，可以优先参考 `configs/` 下的非 MinerU smoke 配置。

### 6.2 生成器

支持：

- `mock`
- `simple_qa`
- `concurrent_qa`

其中：

- `simple_qa`：顺序生成
- `concurrent_qa`：窗口式并发、重试、attempt 聚合

### 6.3 质量闭环

当前 validator：

- `simple_schema`
- `evidence`
- `label`

当前 gate：

- `simple_composite`

失败结果会进入：

- `FailedCases.jsonl`

### 6.4 预检

统一预检协议：

- `PreflightCheckMixin`
- `PreflightCheckResult`
- `PreflightStage`

当前接入：

- `PdfGpuAdapter`
- `SimpleQaGenerator`
- `ConcurrentQaGenerator`

### 6.5 测试目录

`tests/` 目录当前已经按组件和链路分层，接手时不需要第一天就全量跑完，但需要知道它的大致结构：

- `tests/adapter/`
  - 适配器测试，例如 `pdf_cpu`、`pdf_gpu`
- `tests/parser/`
  - parser 实现测试
- `tests/generator/`
  - `simple_qa`、`concurrent_qa`
- `tests/validator/`
  - schema / evidence / label validator
- `tests/gate/`
  - gate 聚合逻辑
- `tests/reporting/`
  - report / manifest 写出
- `tests/test_smoke_*.py`
  - 端到端 smoke，用来验证主流程是否可跑

接手后的推荐顺序是：

1. 先跑 `QUICKSTART` 和 `w2-demo`
2. 再看对应模块目录下的单测
3. 最后再根据需要跑 smoke 或对照实验

## 7. 当前文档结构

### 面向快速上手

- [`docs/QUICKSTART.md`](./QUICKSTART.md)

### 面向维护与交接

- [`docs/HANDOFF_DETAILED.md`](./HANDOFF_DETAILED.md)
- [`docs/W2_MINIMUM_SCOPE.md`](./W2_MINIMUM_SCOPE.md)
- [`docs/ARCHITECTURE.md`](./ARCHITECTURE.md)
- [`docs/AGENT_READY_ARCHITECTURE.md`](./AGENT_READY_ARCHITECTURE.md)
- [`docs/MINERU_DOCKER_COMPONENT.md`](./MINERU_DOCKER_COMPONENT.md)

## 8. 辅助脚本

当前 `scripts/` 目录里保留的脚本都还有明确用途。

### 主入口

- [`scripts/run_w2_demo.sh`](../scripts/run_w2_demo.sh)
  - W2 默认一键运行脚本
  - 默认先做 `preflight`，再执行 `local`

### MinerU 服务辅助

- [`scripts/mineru_api_start.sh`](../scripts/mineru_api_start.sh)
  - 在 MinerU 仓库根目录后台启动 `mineru-api`
  - 会写 `logs/services/mineru-api.log` 和 PID 文件

- [`scripts/mineru_api_stop.sh`](../scripts/mineru_api_stop.sh)
  - 停止后台运行的 `mineru-api`

- [`scripts/mineru_api_parse.sh`](../scripts/mineru_api_parse.sh)
  - 独立验证 MinerU HTTP 服务是否能正常解析单个 PDF
  - 适合排查“服务本身问题”与“主仓库接入问题”

### 清理脚本

- [`scripts/clear-all.sh`](../scripts/clear-all.sh)
  - 清理 `logs/`
  - 清理 `data/` 下除 `data/in` 外的内容
  - 对应命令：

```bash
pixi run clear-all
```

## 9. 当前已知边界

1. `limit` 是 QA 级限制，不是 parser 前置限制
2. 当前主要拒绝原因仍然是 `evidence.too_short`
3. `concurrent_unified` 在单文档默认场景下没有体现出默认启用收益
4. README 之外仍有部分实验配置与对照配置保留在 `configs/`

## 10. 交接建议

接手同学先按这个顺序：

1. 看 [`docs/QUICKSTART.md`](./QUICKSTART.md)
2. 跑 `pixi run preflight --config configs/w2_demo.toml`
3. 跑 `pixi run w2-demo`
4. 再看 [`docs/W2_MINIMUM_SCOPE.md`](./W2_MINIMUM_SCOPE.md)
5. 最后再读架构与演进文档
