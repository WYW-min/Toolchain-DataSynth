# TC-DataSynth

面向 PDF 文档的 QA 合成工具链。当前仓库已具备真实 PDF 解析、真实 LLM 生成、基础质量门禁、预检和一键运行入口。

## 交接文档

### 简洁版
- [一键运行与环境说明](docs/QUICKSTART.md)

### 详细版
- [详细交接文档](docs/HANDOFF_DETAILED.md)
- [W2 最小交付范围](docs/W2_MINIMUM_SCOPE.md)

## 当前默认入口

接手第一步建议先跑仓库自检：

```bash
pixi run local --config configs/mock.toml
```

mock 跑通后，再进入真实链路。

首次使用前，先准备 LLM 环境变量文件：

```bash
cp configs/llm_manager.env.example configs/llm_manager.env
```

### 预检
```bash
pixi run preflight --config configs/w2_demo.toml
```

### 一键运行
```bash
pixi run w2-demo
```

### 默认配置
- [`configs/w2_demo.toml`](configs/w2_demo.toml)
- 当前默认方案：`pdf_gpu + simple_unified + concurrent_qa`

## 常用命令

```bash
pixi install
pixi run main -- --help
pixi run local --config configs/w2_demo.toml
pixi run compare-runs --left data/out/<run_a> --right data/out/<run_b> --left-label a --right-label b
```
