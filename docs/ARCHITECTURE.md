# TC-DataSynth 架构概览（W1 草案）

![架构图](./images/architecture.png)

## 核心理念
- **Spec -> Plan**：用户配置（目标、约束）先被编译为执行计划；核心框架只感知 Plan，便于后续插拔。
- **组件可替换**：解析、采样、生成、门禁、报告均以接口形式存在，可按阶段逐步替换 mock/真实实现。

## 流水线阶段（与代码对应）
1) **Document Reader (`io/reader.py`)**  
   - 负责枚举输入文件，产生 `SourceDocument`。
2) **Parser (`pipeline/parser/`)**  
   - 将原始文件转为统一的 `IntermediateRepresentation`；W1 为 mock，后续接入 PDF/Word 解析器。
3) **Sampler (`pipeline/sampler/`)**  
   - 基于 IR 切分出 `DocumentChunk`；W2 会补充章节/语义切分。

## 结构层次约定
- **物理段落 / block**：版面与解析层的文本分块，回答“文本在版面上怎么被切开”。
- **section**：物理段落之上的语义结构归属，回答“这些段落在文档中属于什么部分”，例如 `abstract`、`introduction`、`methods`、`results`、`conclusion`、`references`。
- **chunk**：面向生成任务的工作单元，由 sampler 组织得到，可由一个或多个物理段落组成，通常应尽量保持在同一 `section` 内。

约束上，`section` 不是“第几个段落”，而是文档语义标签；它的底层载体仍然是若干物理段落。

## 后续增强项
- **IR 结构增强**：后续应在 `IntermediateRepresentation` 阶段显式承载 `block/section` 信息，而不是仅在 sampler 中临时推断。
- **职责边界**：
  - `parser/adapter` 负责识别并输出物理段落与 section 线索
  - `sampler` 负责消费这些线索并做 section-aware chunking
- **建议方向**：未来可为 IR 增加 `blocks` 或 `segments` 字段，每个元素至少包含 `text`、`section`、`order`，必要时再扩展 `heading`、`page` 等信息。


4) **Generator (`pipeline/generator/`)**  
   - 生成 `QAPair`；当前 mock，后续对接 LLM + Prompt 管理。
5) **Quality Gates (`pipeline/validator/`)**  
   - 链式校验，阻塞或告警；W3 将扩展格式/敏感词/启发式规则。
6) **Writer (`io/writer.py`)**  
   - 将通过/失败的数据分别落盘；报告由 `runner` 写入。

## 运行模式
- **W1 Mock 模式**：不触碰 PDF 内容，利用文件名生成稳定的 mock 数据，用于验证 CLI 和数据结构。
- **Spec -> Plan**：`spec` 中描述难度/题型比例与最小证据长度，`plan` 编译后被生成器读取。
- **后续计划**：新增 `RealPdfParser`、`SemanticSampler`、`LLMQAGenerator` 等实现并替换当前注入的组件。
