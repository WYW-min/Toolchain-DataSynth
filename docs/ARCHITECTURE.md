# TC-DataSynth 架构概览（W1 草案）

![架构图](./images/architecture.png)

## 核心理念
- **Spec -> Plan**：用户配置（目标、约束）先被编译为执行计划；核心框架只感知 Plan，便于后续插拔。
- **组件可替换**：解析、采样、生成、门禁、报告均以接口形式存在，可按阶段逐步替换 mock/真实实现。

## RunContext 与临时目录
- **RunContext**：一次运行的统一上下文，集中持有 `run_id`、`temp_root`、`RuntimeConfig`、`Spec`、`Plan`、`logger` 等公共状态。
- **temp_root**：本次运行的中间结果根目录，默认是 `data/temp/<run_id>`。
- **共享方式**：各流水线组件通过依赖注入共享同一个 `RunContext`，需要写中间产物时再通过 `workdir_for(...)` 获取各自子目录。
- **作用**：
  - 统一 run 级路径和日志
  - 给 parser / sampler / planner / generator / gate 提供一致的中间结果落盘位置
  - 避免各组件自行拼接路径，降低运行时状态分散

## Spec -> Plan 的设计意图
- **Spec** 表示“用户想要什么”，例如：
  - 难度分布
  - 题型分布
  - `min_evidence_len`
- **Plan** 表示“系统准备怎么做”，是运行前编译出的执行计划。
- 这层拆分的目的不是为了抽象而抽象，而是为了把：
  - 用户目标
  - 执行策略
  分开。
- 这样后面替换 `sampler / planner / generator / gate` 时，组件只需要消费统一的 `Plan`，而不直接依赖原始配置文件细节。
- 当前仓库里这层已经成立：
  - `SpecConfig` 负责描述目标
  - `PlanConfig` 负责描述执行计划
  - `RunContext.plan` 作为流水线组件共享输入

## 流水线阶段（与代码对应）
1) **Document Reader (`io/reader.py`)**  
   - 负责枚举输入文件，产生 `SourceDocument`。
2) **Parser (`pipeline/parser/`)**  
   - 将原始文件转为统一的 `IntermediateRepresentation`；当前已支持 `simple_unified` 与 `concurrent_unified`。
3) **Sampler (`pipeline/sampler/`)**  
   - 基于 IR 切分出 `DocumentChunk`；当前已支持简单切块与贪心切块。

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


4) **Planner (`pipeline/planner/`)**
   - 基于 `Plan` 为 chunk 分配轻量“出题大纲”，区分 `system_meta` 与 `prompt_meta`。
5) **Generator (`pipeline/generator/`)**  
   - 生成 `QAPair`；当前已支持 `mock`、`simple_qa`、`concurrent_qa`。
6) **Quality Gates (`pipeline/validator/` + `pipeline/gate/`)**  
   - validator 负责检查，gate 负责聚合并做 `pass/reject` 裁决。
7) **Writer / Reporting (`io/writer.py` + `reporting/`)**  
   - 将通过/失败的数据分别落盘，并写出 `report.json` 与各阶段 manifest。

## 运行模式
- **Mock 模式**：不依赖 MinerU 和真实 LLM，用于验证仓库本体与编排流程。
- **W2 默认真实模式**：`pdf_gpu + simple_unified + concurrent_qa`，通过 `configs/w2_demo.toml` 运行。
- **Spec -> Plan**：`spec` 中描述难度/题型比例与最小证据长度，`plan` 编译后由 planner / generator 消费。
- **后续计划**：继续提升 evidence 质量、失败回流、以及更大规模批处理下的 parser 策略。
