# MinerU GPU Docker 参考部署

## 目标

该目录仅保留一份**参考部署说明**，用于把 MinerU 跑成独立服务。

当前仓库不把这套 Docker 服务视为主项目运行时的一部分。

## 为什么独立成 Docker 组件

当前主项目已经依赖：

- `langchain`
- `langchain-openai`
- `openai 2.x`

而 `mineru[vllm]` 这条链会把 `openai` 约束到 `<2.0`。

因此：

- **不要把 MinerU GPU 依赖装进主项目默认 pixi 环境**
- 应通过 Docker 单独部署其运行时

## 参考文档

- MinerU 官方 Docker 部署文档：
  - https://opendatalab.github.io/MinerU/quick_start/docker_deployment/

## 当前边界

主项目侧当前只关心两件事：

1. 你能把 MinerU 服务跑起来
2. 这个服务能暴露稳定的 HTTP 接口

## 运行前提

需要宿主机具备：

1. Docker
2. NVIDIA Container Toolkit（若使用 GPU）
3. 可用 CUDA / GPU 设备

## 最小独立验收

### 1. 启动服务

服务启动方式以官方文档为准。

当前仓库推荐把该目录视为：

- 参考 compose 样例
- 不是主项目自动拉起脚本

### 2. 确认服务接口

独立验收至少应包含：

1. 能访问服务根地址
2. 能访问 API 文档页（通常是 `/docs`）
3. 能完成一次 PDF 解析任务

## 与主项目的接入关系

主项目不应直接 `import mineru`。

推荐接法：

1. `PdfGpuAdapter` 读取外部服务地址
2. 通过 HTTP 请求提交解析任务
3. 拉取或轮询结果
4. 返回 `AdapterResult`

也就是说：

- Docker 服务负责“解析”
- 主项目负责“客户端调用 + 收结果”

## 后续增强方向

1. 钉死 MinerU 官方 API 协议
2. 让 `PdfGpuAdapter` 真正接入 HTTP 客户端逻辑
3. 增加模型缓存目录挂载建议
4. 明确 markdown / middle json 文件命名约定
