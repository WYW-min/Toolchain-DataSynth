# TC-DataSynth Workflow -> Agent-Ready 演进设计（W2 草案）

本文档不是“把现有项目重写成纯 Agent 系统”的方案，而是给当前仓库提供一条可落地的演进路径：

- 保留现有 workflow 主干，继续承担高确定性、强约束、批处理的数据生产任务
- 在此基础上补充一层 agent-ready 的编排视角，为后续报告生成、动态路由、失败修复、工具调用留出扩展空间

目标是让仓库同时具备两种表达能力：

1. 作为稳定的企业级工作流系统存在
2. 作为可向 Agent 化编排演进的架构作品存在
## 让模型站在 workflow 上面，负责理解、选择和修正。

## 1. 当前仓库适合的定位

当前仓库已经不是“简单的 Prompt Demo”，而是一个具备明确工程边界的可插拔流水线系统。核心主链路已经成型：

`reader -> adapter/parser -> sampler -> planner -> generator -> validator/gate -> writer/reporting`

代码上对应：

- 输入发现：`src/tc_datasynth/io/reader.py`
- 运行上下文与配置：`src/tc_datasynth/core/context.py`、`src/tc_datasynth/core/config.py`
- Spec -> Plan：`src/tc_datasynth/core/spec.py`、`src/tc_datasynth/core/planning.py`
- 解析：`src/tc_datasynth/pipeline/adapter/`、`src/tc_datasynth/pipeline/parser/`
- 采样：`src/tc_datasynth/pipeline/sampler/`
- 规划：`src/tc_datasynth/pipeline/planner/`
- 生成：`src/tc_datasynth/pipeline/generator/`
- 校验与门控：`src/tc_datasynth/pipeline/validator/`、`src/tc_datasynth/pipeline/gate/`
- 编排执行：`src/tc_datasynth/pipeline/batching.py`、`src/tc_datasynth/pipeline/runner.py`
- 结果与报告：`src/tc_datasynth/io/writer.py`、`src/tc_datasynth/reporting/`

这套骨架本身就已经符合企业系统最看重的几个点：

- 可替换组件
- 可追踪运行上下文
- 有中间产物与 manifest
- 有质检与失败清单
- 有明确的输入、输出和质量边界

这也是为什么当前仓库更适合走“workflow-first, agent-ready”的路线，而不是直接重做成纯 Agent 项目。

补充一个与文档解析和切块密切相关的层次约定：

- **物理段落 / block**：解析器输出的版面分块
- **section**：物理段落之上的语义结构归属，例如 `abstract`、`methods`、`results`
- **chunk**：面向生成任务的工作单元，由 sampler 基于段落和 section 组织得到

因此，未来如果要让 `section` 真正可用，正确边界应是：

- parser / adapter 负责识别或传递结构线索
- sampler 负责在这些线索上组织 chunk，并尽量避免无意义地跨 section 切分

这部分目前仍属于后续增强项。更具体地说：

- 结构信息应优先在 `IntermediateRepresentation` 阶段建立
- sampler 不应承担“从零识别 section”的主要职责
- 更合理的演进方式是让 IR 显式承载 `block/section`，再由 sampler、planner、reporting 共享消费

## 2. 为什么不建议直接重写成纯 Agent 版

### 2.1 当前主任务是高确定性任务

仓库核心任务是：

- 文档解析
- 文本切块
- 配额规划
- 问答生成
- 结构化校验
- 结果落盘与报告

这类任务的大部分步骤都具有明显的输入输出契约，适合固定 workflow，而不是开放式自主决策。

### 2.2 纯 Agent 化会削弱已有工程优势

当前仓库的价值点在于：

- 组件化设计
- 稳定批处理
- 结果可回放
- 失败可追责
- 质量门控清晰

如果为了求职而把所有模块都包装成“自主 Agent”，容易带来两个问题：

- 技术叙事失焦
- 面试时被追问“为什么这里要 Agent，而不是 workflow”时难以自洽

### 2.3 企业更需要“受控智能编排”，不是“炫技智能体”

对企业知识应用、报告生成、知识库问答、规则约束输出这类场景，更合理的目标通常是：

- 让系统按业务目标动态选择子流程
- 让系统在必要时调用工具
- 让系统在失败时采取有限的修复策略

而不是让系统在完全开放的空间里自由探索。

## 3. 建议的总体方向

建议把本项目定义为：

**面向数据合成、知识处理与报告生成场景的可扩展 LLM 编排系统，支持固定工作流与 Agent 化动态调度两种模式。**

其中，任务级 Agent 的职责可以概括为：

- 意图转化：把用户目标翻译成结构化配置和执行计划
- 自动执行：调用现有 workflow 或工具链完成任务
- 迭代反馈：根据报告、失败清单、质量结果决定是否调参、重试或切换策略

也就是说，对当前仓库而言：

- `workflow` 负责“怎么稳定做”
- `agent` 负责“做什么、怎么选、结果不对时怎么再做一次”

这个定义有三个好处：

- 不否认当前 workflow 的工程价值
- 给后续 Agent 化预留空间
- 求职叙事更贴近“企业级智能应用平台”而不是“单点 Demo”

## 4. 推荐的三层架构

### 4.1 稳定生产层

这一层就是当前仓库已经具备的主体能力，核心目标是：

- 高确定性
- 可回放
- 可观测
- 成本可控

建议继续保持确定性的模块：

- `adapter`
- `parser`
- `sampler`
- `planner`
- `validator`
- `gate`
- `writer`
- `reporting`

这些模块应该继续做成可配置、可替换、可测试的基础设施，而不是优先 Agent 化。

### 4.2 策略编排层

这是最值得新增的一层。它不直接替代现有 pipeline，而是站在 pipeline 之上负责：

- 任务识别
- 路由决策
- 模式选择
- 失败恢复
- 工具选择

建议后续新增一个上层编排包，例如：

- `src/tc_datasynth/orchestration/`

可包含：

- `task_router.py`：根据任务目标选择执行链路
- `strategy.py`：描述不同任务模式的路由策略
- `executor.py`：调用底层 workflow 或工具
- `recovery.py`：根据失败类型决定 retry / repair / fallback

这一层就是未来最自然的“agent-ready 入口”。

更细的职责边界建议如下：

- `task_router`
  - 负责任务识别与场景归类
  - 负责决定这是 `synth_dataset`、`report_generation` 还是 `knowledge_qa`
  - 不直接执行 workflow
- `strategy`
  - 负责为某类任务生成“允许的执行策略集合”
  - 负责限制允许使用的工具、模型、重试次数、恢复动作
  - 不直接执行具体工具调用
- `executor`
  - 负责真正执行 workflow / tool 调用
  - 负责收集结构化执行结果
  - 不负责高层任务判断与策略选择
- `recovery`
  - 负责根据失败码、质量信号、资源约束选择修复动作
  - 只处理失败后的纠偏，不抢 `strategy` 的高层决策职责

这几个模块必须保持边界清楚，否则 orchestration 层很容易演变成多个模块都在做一点判断，最终难以维护。

### 4.3 工具代理层

这层的目标不是把所有组件都人格化，而是把可复用能力包装成可调度工具。

建议优先工具化的能力：

- 文档解析工具
- 切块工具
- 配置编译工具
- QA 生成工具
- 校验工具
- 报告拼装工具
- 结果查询工具

可新增目录，例如：

- `src/tc_datasynth/tools/`

每个工具都应满足：

- 输入输出结构稳定
- 有明确副作用边界
- 能被上层编排安全调用

## 5. 任务级状态模型

如果未来引入 orchestration，仅有“层”是不够的，还必须显式定义层与层之间传递的状态对象。

建议新增一组任务级状态模型，例如：

- `TaskSpec`
  - 用户目标的结构化表达
  - 包括任务类型、目标产物、约束、优先级、预算、允许的工具范围
- `ExecutionState`
  - 当前任务执行到哪个阶段
  - 已执行步骤、已产生中间结果、当前配置、运行状态、剩余预算
- `DecisionRecord`
  - 某一步为什么做这个决策
  - 包括触发条件、候选方案、最终选择、依据的信号
- `RecoveryAction`
  - 失败后采取的修复动作
  - 包括重试、切换模型、切换策略、转人工、终止执行
- `ScenarioResult`
  - 某个场景最终的统一输出
  - 包括业务结果、运行统计、关键指标、失败摘要、产物路径

推荐的流转关系：

```text
TaskSpec
  -> task_router
  -> strategy
  -> ExecutionState
  -> executor
  -> DecisionRecord / RecoveryAction
  -> ScenarioResult
```

对当前仓库而言，这组对象是未来连接：

- `RunContext`
- `Plan`
- `manifest`
- `report`
- `FailedCases`

的关键桥梁。

没有这层模型，后续 orchestration 代码会很容易散成“多个函数在传 dict”。

## 6. 哪些能力适合 Agent 化

### 6.1 适合 Agent 化的能力

#### 顶层任务路由

例如根据用户目标决定走：

- 数据合成链路
- 知识问答链路
- 报告生成链路

#### 失败修复与重试策略

例如根据 `gate` 的失败原因，决定：

- 改写 Prompt 后重试
- 更换模型
- 切换到更保守模板
- 转人工确认

#### 报告生成与多步生成任务

例如：

- 提纲规划
- 证据召回
- 章节分段生成
- 章节级校验
- 最终汇总与润色

#### 跨工具的查询与编排

例如：

- 先查文档索引
- 再调检索工具
- 再调结构化抽取工具
- 再调用报告模板工具

### 6.2 不适合优先 Agent 化的能力

这些模块应优先保持确定性：

- `sampler` 的底层切块
- `validator` 的原子规则校验
- `writer` 的落盘逻辑
- `manifest/report` 的统计逻辑
- 批处理与运行上下文管理

这些部分的价值在于稳定和可审计，不在于自主性。

## 7. 决策可观测与审计产物

如果未来要强调“先审计后智能”，那任务级编排不能只输出最终结果，还应显式落盘决策依据。

建议在 `<run_id>/` 下新增一类 orchestration 产物，例如：

- `decision_log.jsonl`
  - 每次关键决策一条记录
  - 包括输入信号、候选策略、最终选择、时间戳
- `orchestration_trace.json`
  - 任务级执行轨迹
  - 包括步骤顺序、工具调用、耗时、是否成功、重试次数
- `recovery_history.json`
  - 所有修复动作的历史
  - 包括触发失败码、恢复策略、执行结果、是否最终修复成功

每条 `DecisionRecord` 至少应包含：

- `task_id`
- `step`
- `decision_type`
- `input_signals`
- `candidates`
- `selected_action`
- `reason`
- `timestamp`

这样未来在面试或系统演示里，“可信”和“可追踪”就不只是理念，而是有明确产物支撑的工程能力。

## 8. 当前仓库最自然的 Agent 化切入点

结合当前代码结构，推荐按下面顺序演进。

在这个仓库里，Agent 更适合定义为“任务级控制器”，而不是“组件级自治体”：

```text
用户目标
  -> Agent / Orchestrator
  -> 生成结构化配置与执行计划
  -> 调用现有 workflow / tools
  -> 读取 report / manifests / failed cases
  -> 必要时调参并重试
```

因此，未来最推荐的工作模式不是“让 Agent 亲自完成数据合成”，而是：

- 由 Agent 负责任务理解、参数编译、任务路由与结果反馈
- 由现有 workflow 负责真正的解析、切块、规划、生成、校验与落盘

这也是“workflow-first, agent-ready”路线最核心的边界。

### 阶段 1：任务路由

先做最保守的一步：新增顶层任务路由，不改底层组件。

示例：

- `task = synth_dataset` -> 走当前主流程
- `task = report_generation` -> 走报告链路
- `task = knowledge_qa` -> 走检索 + 生成链路

这一步即可把仓库从“单工作流”升级为“多任务编排系统”。

### 阶段 2：工具包装

把当前能力包装成受控工具，而不是直接上自由 Agent。

建议的工具包装优先级：

1. `parse_document`
2. `sample_chunks`
3. `plan_generation`
4. `generate_qa`
5. `validate_qa`
6. `build_report`

这一步完成后，后续接 LangChain tool calling、OpenAI function calling 或 MCP 都会更顺。

### 阶段 3：规划-执行-校验-修复闭环

这是最值得在求职场景里强调的一层。

可以将上层逻辑定义为：

- `Planner`：生成步骤或选择策略
- `Executor`：执行底层 workflow / tool
- `Validator`：检查目标是否达成
- `Recovery`：失败后选择修复动作

注意这里的 `Planner` 和当前 `pipeline/planner/` 不是同一个概念：

- 当前仓库的 `pipeline/planner/` 是数据分布规划器
- 未来上层 Agent 里的 `Planner` 是任务级策略规划器

文档和代码命名上必须区分，避免概念混乱。

### 阶段 4：场景化输出

为了求职表达，建议至少做一个“Agent 风格的业务出口”，而不是只停留在数据合成。

优先级建议：

1. 报告生成
2. 知识库问答
3. 失败样本修复

这三个场景都比“纯 autonomous agent”更贴企业需求。

## 9. 指标体系

如果后续要回答“为什么引入 agent-enhanced orchestration，而不只是纯 workflow”，必须提前定义评估指标。

建议至少跟踪下面这些指标：

- 任务成功率
  - 最终是否成功生成目标产物
- 首次通过率
  - 不经过 recovery 的一次执行成功率
- 平均重试次数
  - 每个任务平均触发多少次修复动作
- 恢复成功率
  - 进入 recovery 后最终成功收敛的比例
- 平均时延
  - 从任务提交到产物完成的平均耗时
- 平均 token / 成本
  - 每个任务或每个成功样本的模型调用成本
- 人工介入率
  - 需要人工确认或人工回流的占比
- 结构一致性 / 报告完整性
  - 是否满足预定义输出结构、章节、字段完整率

对于数据合成场景，还应增加：

- 分布命中率
  - 实际题型/难度分布与目标分布的偏差
- 门控拒绝率
  - `gate` 阶段拒绝的比例
- 样本有效率
  - 最终 `FinalQA.jsonl` 占总生成尝试的比例

未来如果要证明 Agent 层是“有用的”，最有说服力的方式不是说“更智能”，而是用这些指标说明：

- 在复杂任务中降低了人工介入率
- 在失败场景中提高了恢复成功率
- 在目标约束更复杂时保持了较高成功率

## 10. 报告生成场景示例链路

`report_generation` 是最适合展示 agent-ready 架构价值的场景之一，建议明确展开为一条完整链路：

```text
任务目标
  -> 资料检索
  -> 证据归并
  -> 提纲规划
  -> 分章节生成
  -> 章节级校验
  -> 全文一致性检查
  -> 导出与落盘
```

更细的步骤可以定义为：

1. `task_router`
   - 识别任务为 `report_generation`
2. `strategy`
   - 生成本次允许的执行策略
   - 例如允许使用检索工具、提纲规划工具、章节生成工具、校验工具
3. `executor`
   - 调资料检索工具，召回证据片段
   - 调提纲规划工具，生成章节树
   - 分章节调用生成工具
4. `validator`
   - 检查章节完整性、结构一致性、引用覆盖率
5. `recovery`
   - 对缺失章节、证据不足章节、格式不合规章节进行修复
6. `writer/reporting`
   - 输出最终报告、trace、评估指标

这个链路之所以重要，是因为它直接对应企业常见的知识型交付任务，也最容易体现：

- 动态路由
- 工具调用
- 规划-执行-校验-修复闭环
- 可审计的决策记录

## 11. 推荐的目录演进方式

当前仓库不建议推翻重来，建议增量扩展。

可以新增：

```text
src/tc_datasynth/
  orchestration/
    base.py
    task_router.py
    executor.py
    recovery.py
    implements/
  tools/
    base.py
    parser_tool.py
    sampler_tool.py
    generator_tool.py
    report_tool.py
  scenarios/
    synth_dataset.py
    report_generation.py
    knowledge_qa.py
```

其中：

- `pipeline/` 继续负责稳定生产链路
- `orchestration/` 负责策略与路由
- `tools/` 负责能力封装
- `scenarios/` 负责业务出口

这样目录边界非常清楚，不会把 Agent 化逻辑硬塞进当前 pipeline 组件里。

## 12. 必须坚持的工程原则

如果未来引入 Agent 化能力，以下原则不能丢。

### 12.1 有界决策空间

不要做开放式“任意调用任意能力”的自由 Agent。

要做：

- 明确任务类型
- 明确允许使用的工具
- 明确失败后的可选动作

### 12.2 强状态管理

要保留当前仓库已经具备的状态优势：

- `RunContext`
- `Plan`
- `manifest`
- `report`

未来即便引入任务级 Agent，也必须保留可追踪状态。

### 12.3 先规则后模型

优先让规则决定：

- 是否进入哪个链路
- 是否允许重试
- 是否触发人工介入

而不是把这些决定全部交给 LLM。

### 12.4 先审计后智能

一个能出报告但不能解释自己做了什么的系统，在企业里价值很有限。

因此未来 Agent 层也应该输出：

- 执行步骤
- 选用工具
- 关键决策依据
- 最终结果与失败原因

## 13. 对求职表达的建议

后续对外表达时，不建议说：

- “我做了一个全自动 autonomous agent”

更建议说：

- “我构建了一个支持固定 workflow 与动态策略编排的 LLM 应用系统”
- “在高确定性任务中使用固定 workflow 保证稳定性、成本与可追踪性”
- “在开放任务中引入任务级规划、工具调用、结果校验与失败修复能力”

这个说法更稳，也更贴企业真实需求。

## 14. 推荐的最小 Agent 化落地方案

如果后续要最小成本补一个 Agent-ready demo，建议按下面顺序做：

1. 新增 `report_generation` 场景
2. 增加 `task_router`
3. 把检索、生成、校验、导出包装为 tools
4. 加一个简单的任务级 planner / recovery
5. 保留现有 dataset synthesis 主流程不变

这样改造量可控，而且最容易在面试里讲清楚。

## 15. 当前结论

当前仓库最合理的未来方向不是：

- “把现有系统重写成纯 Agent”

而是：

- “把当前稳定 workflow 作为生产内核”
- “在其之上增加任务路由、工具调用、规划-执行-校验-修复闭环”
- “形成一个 workflow-first, agent-ready 的企业级智能编排系统”

这条路径最真实，也最适合后续求职表达与持续演进。
