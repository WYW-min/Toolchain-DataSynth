# Docker 组件

当前 `docker/` 目录只承载**与主项目 Python 环境解耦的外部能力**。

当前规划：

- `mineru-gpu/`
  - MinerU GPU 解析参考部署
  - 目标：在不污染主项目 `pixi` 环境的前提下，独立提供 HTTP 解析服务
  - 主项目后续通过 `PdfGpuAdapter` 以 HTTP 客户端方式调用

设计原则：

1. 主项目继续使用 `pixi`
2. Docker 组件独立部署、独立验收
3. 主项目只做服务调用，不直接 `import` 容器内依赖
