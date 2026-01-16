# TC-DataSynth仓库架构介绍 (W1 骨架)

面向 300 篇 PDF 的 QA 合成工具链。当前完成 W1 骨架：CLI 可跑通 mock 流程，产出符合 Schema 的 JSONL（不调用大模型）。
开发规范见 [CONTRIBUTING.md](docs/CONTRIBUTING.md)。

## 快速开始
- 确保 `pixi` 已安装（[安装指南](https://pixi.sh/latest/#installation)），仓库根目录执行：`pixi run main -- --help`
- 推荐方式：  
  - local：`pixi run local`  
  - server（W1 占位）：`pixi run server`
- 冒烟测试：`pixi run test-smoke`
- 删除所有产物：`pixi run clean-all`
- 统一入口方式（`main` 会转发到 local/server）：  
  - 默认 local：`pixi run main`  
  - 显式 local：`pixi run main local`  
  - 显式 server：`pixi run main server`
  
- 覆盖输入/输出或处理数量：`pixi run local --input-dir /path/to/pdfs --output-dir outputs --max-docs 10`  
- 启动 API 服务（W1 占位）：`pixi run server --host 0.0.0.0 --port 8000`  
- 调整解析/生成批处理（1=流式，none/0=全量）： `pixi run local --parse-batch-size 5 --generate-batch-size 10`  
- 也可通过 TOML 加载参数：  `pixi run local --config configs/mock.toml`  
- 强制 mock 模式：  `pixi run local --mock` 或 `pixi run local -m`  
- 若沙箱限制导致 pixi 缓存无法写入，可直接运行：
  - linux/mac: `PYTHONPATH=src python -m tc_datasynth.main --max-docs 2`
  - windows: `set PYTHONPATH=src && python -m tc_datasynth.main --max-docs 2`

## 产物
- `outputs/<run_id>/FinalQA.jsonl`：通过门禁的 QA 对（mock 数据）。
- `outputs/<run_id>/FailedCases.jsonl`：未通过门禁的记录（W1 默认为空）。
- `outputs/<run_id>/report.json`：本次运行的简单统计。

## 代码结构
- `src/tc_datasynth/main.py`：入口脚本，分发到不同启动方式。
- `src/tc_datasynth/arg_parser.py`：主入口解析与子命令占位。
- `src/tc_datasynth/access/`：入口层（CLI / API）  
  - `cli_app.py`：CLI 参数解析与配置构建  
  - `api_app.py`：API 入口，暴露 `create_app`
- `src/tc_datasynth/service.py`：业务服务层（组件装配 + 执行流程），CLI/API 共用。
- `src/tc_datasynth/core/`：核心能力（配置、日志、数据模型、运行上下文、Spec/Plan）。
- `src/tc_datasynth/io/`：输入/输出  
  - `reader.py`：输入发现（Simple 前缀实现）  
  - `writer.py`：产物落盘（Simple 前缀实现）
- `src/tc_datasynth/pipeline/`：可插拔的流水线组件，**组件扩展点**
  - `adapters/`：适配器基类 + `implements/`（PDF mock、Word mock）  
  - `parser/`：`base.py` + `implements/`（Simple 解析器）  
  - `sampler/`：`base.py` + `implements/`（Simple 采样器）  
  - `generator/`：`base.py` + `implements/`（Mock 生成器）  
  - `validator/`：`base.py` + `implements/`（Simple 门禁）  
  - `runner.py`：编排器，串起全链路（从 RunContext 获取 logger）
  - `components.py`：流水线组件容器
  - `batching.py`：批处理逻辑拆分
  - `progress.py`：进度条管理封装
- `src/tc_datasynth/reporting/`：报告输出  
  - `report_writer.py`：运行统计报告落盘
- `configs/mock.toml`：示例配置。
  - `runtime` 中支持 `parse_batch_size` / `generate_batch_size` 控制解析与生成批处理大小。
- `tests/`：mock 流程冒烟测试。
- 预留扩展：`docker/`（镜像相关占位）。
- 命名约定：`Mock*` 表示占位 mock 实现，`Simple*` 表示最小可用实现。
- 配置约定：各组件接口使用 `Generic[TConfig]`，实现可接收对应 `ConfigBase` 子类或使用默认配置。

## 运行上下文与临时目录
- `RunContext` 统一维护 `run_id`、`temp_root`（默认 `data/temp/<run_id>`）、`RuntimeConfig`、`logger` 等，流水线组件通过依赖注入共享。
- 适配器输出中间文件到 `temp_root/adapter_output/<doc_id>/`，统一解析器读取中间产物并生成 IR，后续可扩展表格/图片处理。

## Spec -> Plan（W1 占位）
- `configs/mock.toml` 中新增 `[spec]`：难度比例、题型比例、最小参照段落长度等。
- 启动时由 `MockPlanCompiler` 将 Spec 编译为 Plan，并写入 `RunContext.plan`，生成器读取 Plan 做占位控制。

## 架构与路线
- 总体架构图：`docs/images/architecture.png`（来自计划排班书 `流程图.png`）。
- 设计思路：坚持 “Spec -> Plan” 分离，后续只需替换/扩展组件（真实 PDF 解析、采样策略、LLM 生成、规则门禁、报告生成）。

## 下一步（W2/W3 展望）
- 开发环境下定义各组件的单元测试与集成测试。
- 接入真实 PDF/Word 解析适配器，补充切分插件与 LLM 生成。
- 扩充门禁体系（格式、敏感词、启发式），生成质量报告与回流清单。
- FastAPI 服务化封装与 Docker 交付。
