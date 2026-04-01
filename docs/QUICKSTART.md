# TC-DataSynth 简洁版一键运行

这份文档只面向接手同学的第一步：把环境起起来，完成预检，并跑通一条真实链路。

如果你对这个仓库完全不熟，先按下面这条路径做，不要先看架构文档。

## 0. 5 分钟最短路径

### 第一步：先跑 mock，确认仓库本体能正常运行

先执行：

```bash
pixi install
pixi run local --config configs/mock.toml
```

这一步的目的不是验证真实链路，而是先确认：

- pixi 环境没问题
- CLI 能跑
- 主流程能跑
- `report.json` / `FinalQA.jsonl` 能正常写出

如果这一步都跑不通，不要继续排查 MinerU 或 LLM。

### 第二步：再跑真实链路

按顺序执行：

```bash
cp configs/llm_manager.env.example configs/llm_manager.env
pixi run preflight --config configs/w2_demo.toml
pixi run w2-demo
```

但这 4 条命令能成功的前提是：

1. MinerU HTTP 服务已经启动，并且 `http://127.0.0.1:8000/health` 可访问
2. `configs/llm_manager.env` 里已经填了真实 `BASEURL / API KEY`
3. `data/in/pdf_demo` 里已经有演示 PDF，或你已经把 `input_dir` 改成自己的目录

如果这三个前提你还没准备好，就继续按后面的步骤做。

## 1. 先区分两种运行方式

这个仓库有两条运行路径：

### 路径 A：mock 流程

- 配置文件：`configs/mock.toml`
- 不依赖 MinerU
- 不依赖真实 LLM
- 用来确认仓库本体和 pixi 环境正常

运行命令：

```bash
pixi run local --config configs/mock.toml
```

### 路径 B：真实流程

- 配置文件：`configs/w2_demo.toml`
- 依赖 MinerU HTTP 服务
- 依赖真实 LLM 配置
- 用来跑当前 W2 默认方案

运行命令：

```bash
pixi run w2-demo
```

接手时建议顺序：

1. 先跑 mock
2. mock 跑通后再跑真实链路

## 2. 你先要知道的 3 件事

这个仓库要跑起来，依赖 3 个东西：

1. **MinerU HTTP 服务**
   - 用来解析 PDF
   - 默认地址写在 `configs/w2_demo.toml` 里：
     - `http://127.0.0.1:8000`

2. **LLM 配置**
   - 用来调用大模型生成 QA
   - 配置文件是：
     - `configs/llm.toml`
   - 密钥文件是：
     - `configs/llm_manager.env`

3. **输入 PDF**
   - 默认放在：
     - `data/in/pdf_demo`

## 3. 环境要求

- Linux
- 已安装 `pixi`
- 已有可用的 MinerU HTTP 服务
- 已准备好 LLM 配置文件

## 4. 关键目录

- 输入目录：`data/in/pdf_demo`
- 输出目录：`data/out`
- 中间目录：`data/temp/<run_id>`
- 日志目录：`logs`

默认演示配置是：

- [`configs/w2_demo.toml`](/Data_two/wyw/code/TC-DataSynth/configs/w2_demo.toml)

这份配置默认使用：

- `pdf_gpu`
- `simple_unified`
- `concurrent_qa`

## 5. pixi 环境

仓库根目录执行：

```bash
pixi install
```

常用入口：

```bash
pixi run main -- --help
pixi run preflight --help
pixi run w2-demo --help
```

## 6. 准备 MinerU HTTP 服务

默认配置里，MinerU 服务地址写在：

- [`configs/w2_demo.toml`](/Data_two/wyw/code/TC-DataSynth/configs/w2_demo.toml)

对应字段：

```toml
[components.adapter.pdf]
name = "pdf_gpu"
server_url = "http://127.0.0.1:8000"
```

也就是说，主仓库默认会访问：

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/file_parse`

如果你的 MinerU 服务不在这个地址，需要修改 `server_url`。

### 6.1 启动方式

如果你本地已经有 MinerU 仓库，可以在 MinerU 仓库根目录启动：

```bash
bash mineru_api_start.sh --host 127.0.0.1 --port 8000 --cuda-devices 0
```

说明：

- 这个脚本在本仓库里提供参考版本：
  - [`scripts/mineru_api_start.sh`](/Data_two/wyw/code/TC-DataSynth/scripts/mineru_api_start.sh)
- 需要复制到 MinerU 仓库根目录下执行

### 6.2 服务自检

先确认 MinerU 服务已启动：

```bash
curl http://127.0.0.1:8000/health
```

如果要独立验证单个 PDF 解析能力，可使用：

```bash
bash scripts/mineru_api_parse.sh \
  --input "/绝对路径/你的PDF.pdf" \
  --output "/绝对路径/输出目录"
```

## 7. 准备 LLM 配置

LLM 配置入口：

- [`configs/llm.toml`](/Data_two/wyw/code/TC-DataSynth/configs/llm.toml)

环境变量模板：

- [`configs/llm_manager.env.example`](/Data_two/wyw/code/TC-DataSynth/configs/llm_manager.env.example)

当前仓库里**只有模板文件**，不会提交真实密钥文件。首次使用前先执行：

```bash
cp configs/llm_manager.env.example configs/llm_manager.env
```

然后编辑：

- `configs/llm_manager.env`

如果你只想先跑默认配置，至少把下面两项填上：

- `DOUBAO_BASEURL`
- `DOUBAO_APIKEY_FS_AGENT`

因为 `w2_demo.toml` 默认模型是：

- `doubao-flash`

如果你不用豆包，也可以改模型，但要保证：

- `configs/llm.toml` 里存在这个模型定义
- `configs/llm_manager.env` 里填了对应 env 变量

最少要填的就是你要使用模型对应的：

- `BASEURL`
- `API KEY`

### 7.1 当前默认模型在哪里改

默认演示配置里，生成器模型写在：

- [`configs/w2_demo.toml`](/Data_two/wyw/code/TC-DataSynth/configs/w2_demo.toml)

对应字段：

```toml
[components.generator]
name = "concurrent_qa"
llm_model = "doubao-flash"
prompt_id = "simple_qa"
```

如果你要切模型，优先改：

- `components.generator.llm_model`

前提是：

- 这个模型已经在 `configs/llm.toml` 中定义
- 对应的 env 变量已经在 `configs/llm_manager.env` 中填好

## 8. 准备输入 PDF

默认输入目录在：

```toml
[runtime]
input_dir = "./data/in/pdf_demo"
```

也就是：

- `data/in/pdf_demo`

你有两种方式：

### 方式 A：直接使用仓库自带演示 PDF

默认演示目录是：

- `data/in/pdf_demo`

这里已经放了演示 PDF，可以直接用于第一次跑通。

### 方式 B：把你自己的 PDF 放到默认目录

把你自己的 PDF 放进：

- `data/in/pdf_demo`

### 方式 C：改配置到你自己的目录

修改：

- [`configs/w2_demo.toml`](/Data_two/wyw/code/TC-DataSynth/configs/w2_demo.toml)

把：

```toml
input_dir = "./data/in/pdf_demo"
```

改成你自己的路径。

## 9. 运行前预检

先执行：

```bash
pixi run preflight --config configs/w2_demo.toml
```

预检通过时，至少应看到：

- `generator.concurrent_qa`
- `adapter.pdf_gpu`

如果这里失败，不要先跑主流程，先修好：

- MinerU 服务
- `configs/llm_manager.env`
- `configs/llm.toml`
- `configs/w2_demo.toml`

## 10. 一键运行

执行：

```bash
pixi run w2-demo
```

脚本会自动：

1. 运行预检
2. 启动主流程
3. 输出本次 `run_id`
4. 提示结果文件位置

如果你只想看预检：

```bash
pixi run w2-demo --preflight-only
```

如果你确认环境没问题，想跳过预检：

```bash
pixi run w2-demo --skip-preflight
```

## 11. 结果查看

重点看 4 个位置：

1. `data/out/<run_id>/FinalQA.jsonl`
2. `data/out/<run_id>/FailedCases.jsonl`
3. `data/out/<run_id>/report.json`
4. `data/temp/<run_id>`

## 12. 最常改的配置项

最常改的是 [`configs/w2_demo.toml`](/Data_two/wyw/code/TC-DataSynth/configs/w2_demo.toml) 里的这几项：

```toml
[runtime]
input_dir = "./data/in/pdf_demo"
doc_limit = 0
limit = 40

[components.adapter.pdf]
server_url = "http://127.0.0.1:8000"

[components.generator]
llm_model = "doubao-flash"
prompt_id = "simple_qa"
```

含义：

- `input_dir`
  - 从哪里读 PDF
- `doc_limit`
  - 最多处理多少篇文档，`0` 表示不限
- `limit`
  - 最终 QA 总量上限，`0` 表示不限
- `server_url`
  - MinerU 服务地址
- `llm_model`
  - 当前使用的模型名
- `prompt_id`
  - 当前使用的 prompt 模板

## 13. 若运行失败，优先排查

1. `pixi run preflight --config configs/w2_demo.toml`
2. `logs/<run_id>.log`
3. `data/out/<run_id>/report.json`
4. `data/out/<run_id>/FailedCases.jsonl`
5. `data/temp/<run_id>`
