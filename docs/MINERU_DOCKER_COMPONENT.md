# MinerU 外部组件接入设计

## 目标

在不破坏主项目 `pixi` 主环境的前提下，引入一个**独立部署的 MinerU HTTP 解析服务**。

当前约束：

- 主项目保留：
  - `langchain`
  - `langchain-openai`
  - `openai 2.x`
- MinerU GPU / vLLM 单独通过 Docker 运行

## 组件定位与边界

MinerU 不是主项目运行环境的一部分，而是：

- 一个外部解析服务
- 一个由主项目通过 HTTP 调用的独立组件

当前仓库负责：

- `PdfGpuAdapter` 的客户端配置与调用逻辑
- 解析结果向 `AdapterResult` 的映射
- 调用失败、超时、轮询等客户端行为

当前仓库不负责：

- MinerU 服务本身的镜像构建与运维
- CUDA / vLLM / 模型缓存环境治理
- 强绑定的服务拉起逻辑

## 最小阶段划分

### 阶段 1：外部服务可独立运行

验收标准：

1. 给定一个 PDF
2. 外部 MinerU 服务能完成解析
3. 服务能通过 HTTP API 暴露结果或任务状态

### 阶段 2：主项目 HTTP 客户端接入

`PdfGpuAdapter` 只做以下事情：

1. 读取 `server_url`
2. 向外部 MinerU 服务发起解析请求
3. 轮询结果或拉取结果
4. 读取 markdown 主文件 / 中间 json
5. 组装 `AdapterResult`

## 输入输出协议

### 输入

- `input_pdf`: 单个 PDF
- `server_url`: MinerU HTTP 服务地址

### 输出约定

以外部服务的实际协议为准。当前仓库只约定消费结果应至少包含：

- markdown 主文本
- middle json（若服务侧启用）
- 图片/表格等附属产物（若服务侧启用）

### 主项目侧最小消费要求

主项目后续只要求：

1. 能找到 markdown 主文件
2. 能记录服务返回的解析产物目录或下载结果
3. 能把 markdown 主文件作为 `text_path`
4. 把其他产物作为 `metadata / table_files / image_files`

## 当前与主项目的边界

- `docker/mineru-gpu/`
  - 仅保留参考部署说明
- `PdfGpuAdapter`
  - 负责 HTTP 客户端接入
- `components.adapter.pdf`
  - 负责声明使用 `pdf_cpu` 还是 `pdf_gpu`

## 后续增强项

1. 钉死 MinerU 官方 API 协议后实现 `PdfGpuAdapter.parse`
2. 明确 markdown 主文件的扫描优先级
3. 为结果下载与轮询补齐重试 / 超时策略
4. 如需远程部署，再补认证与多租户隔离策略
