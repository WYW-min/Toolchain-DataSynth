# W2 最小交付范围

## 目标
W2 的目标不是继续扩张组件数量，而是把当前真实链路收成一个可演示、可交接、可复现的最小版本。

这一版本需要满足：

1. 可以处理真实 PDF
2. 可以调用真实 LLM
3. 具备基础质量门禁与失败清单
4. 具备中间产物与报告输出
5. 具备运行前预检与一键运行入口

## 当前默认方案
当前默认演示配置是：

- `pdf_gpu + simple_unified + concurrent_qa`
- 配置文件：[`configs/w2_demo.toml`](../configs/w2_demo.toml)
- 一键运行：`pixi run w2-demo`

选择这个方案的原因：

1. `simple_unified + concurrent_qa` 在真实 MinerU + 真实 LLM 条件下具备更好的整体均衡性
2. 相比 `simple_unified + simple_qa`，耗时显著降低
3. 相比 `concurrent_unified + concurrent_qa`，默认链路更稳定、更容易解释

## 当前已完成能力

### 真实链路
- `pdf_cpu` 与 `pdf_gpu(MinerU HTTP)` 两条 PDF 解析链路可用
- `simple_qa` 与 `concurrent_qa` 两种生成器实现可用

### 质量闭环
- `schema / evidence / label` 三类 validator
- `simple_composite` gate
- `FailedCases.jsonl`
- `report.json`

### 中间产物
- parser / sampler / planner / generator / gate manifests
- parser / generator attempts trace
- `data/temp/<run_id>` 中间目录

### 运行入口
- `preflight` 子命令
- `w2-demo` 一键运行任务

## 推荐运行方式

### 一键运行
```bash
pixi run w2-demo
```

### 仅预检
```bash
pixi run preflight --config configs/w2_demo.toml
```

### 对照配置
以下配置保留用于实验和对照，不作为默认入口：

- [`configs/smoke_mineru.toml`](../configs/smoke_mineru.toml)
- [`configs/smoke_mineru_concurrent.toml`](../configs/smoke_mineru_concurrent.toml)
- [`configs/smoke_mineru_parser_concurrent.toml`](../configs/smoke_mineru_parser_concurrent.toml)
- [`configs/smoke_mineru_full_concurrent.toml`](../configs/smoke_mineru_full_concurrent.toml)

## 当前已知边界

1. `limit` 目前是 QA 级限制，不是 parser 前置限制
2. 当前主要失败原因仍集中在 `evidence.too_short`
3. `concurrent_unified` 在单文档演示场景下没有体现出默认启用价值
4. MinerU 服务当前作为外部依赖接入，本仓库负责调用与预检，不负责服务端运维

## W3 的自然方向

1. 收紧生成质量，优先改善 evidence 质量
2. 继续完善报告与失败回流机制
3. 根据真实批量场景再评估 parser 并发策略
4. 在 workflow 内核稳定后，再向更高层的 orchestration / agent-ready 能力扩展
