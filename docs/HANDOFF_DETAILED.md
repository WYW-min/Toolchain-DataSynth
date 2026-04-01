# TC-DataSynth 详细交接文档

先说阅读顺序：

1. 接手第一天，不要先看这份文档
2. 先看 [`docs/QUICKSTART.md`](/Data_two/wyw/code/TC-DataSynth/docs/QUICKSTART.md)
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
- 配置文件：[`configs/w2_demo.toml`](/Data_two/wyw/code/TC-DataSynth/configs/w2_demo.toml)

选择原因：

1. 相比 `simple_qa`，`concurrent_qa` 显著降低总耗时
2. 相比 `full_concurrent`，默认链路更稳定、更容易解释
3. 在单文档演示场景下，parser 并发没有体现出默认启用价值

## 3.1 LLM 配置说明

LLM 配置入口：

- [`configs/llm.toml`](/Data_two/wyw/code/TC-DataSynth/configs/llm.toml)

环境变量模板：

- [`configs/llm_manager.env.example`](/Data_two/wyw/code/TC-DataSynth/configs/llm_manager.env.example)

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

### 4.2 核心原则

1. `Spec -> Plan`
2. 组件可替换
3. 中间产物可追踪
4. 真实链路与 mock 链路共存

## 5. 模块介绍

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

核心基础设施：

- `config.py`
- `context.py`
- `models.py`
- `logging.py`
- `llm/`

### `src/tc_datasynth/pipeline/`

可替换组件区：

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

### `src/tc_datasynth/reporting/`

运行结果汇总：

- `report_writer.py`
- `manifest_writer.py`

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

- [`docs/QUICKSTART.md`](/Data_two/wyw/code/TC-DataSynth/docs/QUICKSTART.md)

### 面向维护与交接

- [`docs/HANDOFF_DETAILED.md`](/Data_two/wyw/code/TC-DataSynth/docs/HANDOFF_DETAILED.md)
- [`docs/W2_MINIMUM_SCOPE.md`](/Data_two/wyw/code/TC-DataSynth/docs/W2_MINIMUM_SCOPE.md)
- [`docs/ARCHITECTURE.md`](/Data_two/wyw/code/TC-DataSynth/docs/ARCHITECTURE.md)
- [`docs/AGENT_READY_ARCHITECTURE.md`](/Data_two/wyw/code/TC-DataSynth/docs/AGENT_READY_ARCHITECTURE.md)
- [`docs/MINERU_DOCKER_COMPONENT.md`](/Data_two/wyw/code/TC-DataSynth/docs/MINERU_DOCKER_COMPONENT.md)

## 8. 辅助脚本

当前 `scripts/` 目录里保留的脚本都还有明确用途。

### 主入口

- [`scripts/run_w2_demo.sh`](/Data_two/wyw/code/TC-DataSynth/scripts/run_w2_demo.sh)
  - W2 默认一键运行脚本
  - 默认先做 `preflight`，再执行 `local`

### MinerU 服务辅助

- [`scripts/mineru_api_start.sh`](/Data_two/wyw/code/TC-DataSynth/scripts/mineru_api_start.sh)
  - 在 MinerU 仓库根目录后台启动 `mineru-api`
  - 会写 `logs/services/mineru-api.log` 和 PID 文件

- [`scripts/mineru_api_stop.sh`](/Data_two/wyw/code/TC-DataSynth/scripts/mineru_api_stop.sh)
  - 停止后台运行的 `mineru-api`

- [`scripts/mineru_api_parse.sh`](/Data_two/wyw/code/TC-DataSynth/scripts/mineru_api_parse.sh)
  - 独立验证 MinerU HTTP 服务是否能正常解析单个 PDF
  - 适合排查“服务本身问题”与“主仓库接入问题”

### 清理脚本

- [`scripts/clear-all.sh`](/Data_two/wyw/code/TC-DataSynth/scripts/clear-all.sh)
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

1. 看 [`docs/QUICKSTART.md`](/Data_two/wyw/code/TC-DataSynth/docs/QUICKSTART.md)
2. 跑 `pixi run preflight --config configs/w2_demo.toml`
3. 跑 `pixi run w2-demo`
4. 再看 [`docs/W2_MINIMUM_SCOPE.md`](/Data_two/wyw/code/TC-DataSynth/docs/W2_MINIMUM_SCOPE.md)
5. 最后再读架构与演进文档
