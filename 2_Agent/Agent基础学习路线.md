# AI Agent 工程：结构化学习报告

> 仅基于一手资料：学术论文、官方工程博客和官方框架文档。
> 编制日期：2026 年 5 月

---

## 目录

1. [范围与方法](#1-范围与方法)
2. [基础论文及其贡献](#2-基础论文及其贡献)
3. [核心知识树](#3-核心知识树)
4. [学习架构：自底向上的学习地图](#4-学习架构自底向上的学习地图)
5. [逐模块分析](#5-逐模块分析)
   - [5.1 推理与行动：ReAct 范式](#51-推理与行动react-范式)
   - [5.2 通过反思实现自我改进](#52-通过反思实现自我改进)
   - [5.3 工具调用与结构化输出](#53-工具调用与结构化输出)
   - [5.4 检索增强生成](#54-检索增强生成rag)
   - [5.5 Anthropic 编排模式](#55-anthropic-编排模式)
   - [5.6 框架对比：LangGraph、OpenAI SDK、Google ADK](#56-框架对比langgraphopenai-sdkgoogle-adk)
   - [5.7 互操作性：MCP 与 A2A](#57-互操作性mcp-与-a2a)
   - [5.8 评估即基础设施](#58-评估即基础设施)
6. [建议学习顺序](#6-建议学习顺序)
7. [参考文献](#7-参考文献)

---

## 1. 范围与方法

本报告仅整合以下一手资料：

| 资料类别 | 具体来源 |
|----------|----------|
| **同行评审论文** | ReAct（Yao et al., 2022, ICLR 2023）；Reflexion（Shinn et al., 2023, NeurIPS 2023）；Augmented Language Models 综述（Mialon et al., 2023, TMLR） |
| **官方工程博客** | Anthropic《Building Effective Agents》（2025）；《Demystifying Evals for AI Agents》（2026）；《Writing Effective Tools for Agents》（2025） |
| **官方框架文档** | LangGraph 参考文档；OpenAI Function Calling 指南（o3/o4-mini, 2025）；OpenAI Responses API |
| **开放协议规范** | MCP（Model Context Protocol）规范，v2025-11-25；Google A2A（Agent-to-Agent）规范，v0.3 |

本报告明确排除：博客聚合器、教程转载、未经验证的社区帖文，以及任何本身即为二次汇总的来源。

---

## 2. 基础论文及其贡献

### 2.1 ReAct：语言模型中的推理与行动协同

**作者：** Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao（Google Research + Princeton）
**发表：** arXiv:2210.03629，2022 年 10 月。**会议：** ICLR 2023。
**链接：** https://arxiv.org/abs/2210.03629

**核心思想。** ReAct 在一个统一循环中将推理轨迹（`Thought`）与任务特定行动（`Action`）以及环境观察（`Observation`）交替进行。关键洞见是推理与行动彼此协同：推理轨迹帮助模型归纳、追踪和更新行动方案；行动则让模型获取外部信息来锚定推理结果，从而减少幻觉。

**架构（单次循环）：**
```
Thought: 我需要找到 X 的定义。让我搜索一下。
Action: search("X 定义")
Observation: X 在来源 Z 中被定义为 Y。
Thought: 现在我知道 X 是 Y 了。我可以回答这个问题。
Action: finish("X 是 Y，来源 Z")
```

**关键实验结果：**

| 基准测试 | 任务类型 | ReAct（6-shot） | ReAct + CoT | 此前最佳 |
|----------|----------|-----------------|-------------|----------|
| HotpotQA | 多跳问答 | 27.4 EM | **35.1 EM** | 25.3 EM |
| FEVER | 事实验证 | 60.9% 准确率 | **64.6% 准确率** | 55.4% 准确率 |
| ALFWorld | 文字游戏决策 | 71% 成功率 | 不适用 | 37%（模仿学习） |
| WebShop | 网络导航 | 40% 成功率 | 不适用 | 30%（标准方法） |

**为什么重要。** ReAct 是每个现代 Agent 框架的直接前身。LangGraph 的 `create_react_agent`、OpenAI 的 Responses API 循环、Anthropic 的工具调用循环——都实现了相同的 Thought→Action→Observation 周期。理解 ReAct 就意味着理解了所有 Agent 系统所依赖的基础循环。

**论文承认的局限性：** ReAct 可能陷入重复循环。论文通过最大步数限制来缓解这一问题。现代实现用更精细的循环控制来解决（LangGraph 的条件边、Anthropic 的 `max_tokens` 预算）。

---

### 2.2 Reflexion：基于语言强化的自我反思 Agent

**作者：** Noah Shinn, Federico Cassano, Edward Berman, Ashwin Gopinath, Karthik Narasimhan, Shunyu Yao
**发表：** arXiv:2303.11366，2023 年 3 月。**会议：** NeurIPS 2023。
**链接：** https://arxiv.org/abs/2303.11366

**核心思想。** Reflexion 在 ReAct 风格的 Actor 之上增加了一个**自我反思**模块。不同于更新模型权重（成本高昂），Agent 将文本形式的反思存储在情景记忆缓冲区中，并在下一次尝试时将反馈作为条件。论文称之为"语言强化学习"——用自然语言作为奖励信号。

**架构（三个模块）：**
```
┌──────────────┐     行动          ┌────────────────┐
│    Actor     │ ────────────────→  │    环境        │
│   (LLM)      │ ←───────────────  │               │
└──────┬───────┘   观察结果          └───────┬────────┘
       │                                     │
       │ 输出                                │ 奖励/评分
       ▼                                     ▼
┌──────────────┐                     ┌───────────────┐
│    自我      │ ←───────────────────│   评估器      │
│   反思模块    │     反馈           │               │
└──────┬───────┘                     └───────────────┘
       │
       │ 将反思文本存入情景记忆
       ▼
┌──────────────────────┐
│   情景记忆缓冲区       │
│                      │
└──────────────────────┘
```

**关键实验结果：**

| 任务 | 基准测试 | Reflexion | 基线 | 提升幅度 |
|------|----------|-----------|------|----------|
| 决策任务 | ALFWorld | **97%**（130/134） | ReAct: 71% | +26% |
| 推理任务 | HotpotQA | **51%** 成功率 | CoT+ReAct: 35% | +16% |
| 代码生成 | HumanEval | **91% pass@1** | GPT-4: 80% | +11% |

**为什么重要。** Reflexion 确立了**生成→评估→反思→重试**的模式，这正是当今 Evaluator-Optimizer 工作流模式的基础（Anthropic 指南将其规范化为六种核心模式之一）。它还首次将情景记忆作为独立的架构组件引入。

**关键架构洞见：** Actor、Evaluator 和 Self-Reflection 模块可以是**同一个 LLM**，只是使用不同的 prompt 调用。这意味着该模式不需要任何模型微调——只需 prompt 工程和状态管理。

---

### 2.3 Augmented Language Models：综述

**作者：** Grégoire Mialon, Roberto Dessì, Maria Lomeli, Christoforos Nalmpantis, Ram Pasunuru, Roberta Raileanu, Baptiste Rozière, Timo Schick, Jane Dwivedi-Yu, Asli Celikyilmaz, Edouard Grave, Yann LeCun, Thomas Scialom（Meta AI）
**发表：** arXiv:2302.07842，2023 年 2 月。**会议：** TMLR 2023。
**链接：** https://arxiv.org/abs/2302.07842

**核心贡献。** 这篇综述首次正式定义了**增强语言模型（Augmented Language Models, ALMs）**这一类别——使用非参数化的外部模块（工具、检索器、代码解释器）来克服纯参数化知识的局限性的 LLM。它是系统性地整理该领域的首批工作之一。

**关键分类体系：**
- **推理方法：** Chain-of-thought、self-consistency、least-to-most prompting、decomposed prompting
- **工具调用：** 搜索引擎、计算器、代码解释器、视觉模型、语音模型
- **检索：** 稀疏检索（BM25）、稠密检索（DPR、Contriever）、混合检索、迭代检索
- **学习范式：** Few-shot prompting、微调、自举（self-play）、强化学习（RLHF、RLAIF）

**持久洞见：** 作者论证了工具调用与参数化知识之间存在权衡关系——随着工具变得更加可靠，LLM 可以将事实召回的责任转移给检索器，从而同时变得更强大和更具可解释性。这一预言已被行业向 RAG 优先架构的转向所验证。

**当今意义。** 这篇论文为"让 LLM 做推理，让工具做知识"的架构理念提供了理论框架。它是主导生产级 Agent 系统的检索增强生成（RAG）范式的学术基础。

---

## 3. 核心知识树

以下是 AI Agent 工程的完整知识分类体系，按层级组织。每一层建立在下层之上。标有论文或文档标题的条目直接对应一手资料。

```
                                   ┌───────────────────────────────────────┐
                                   │            生产系统                    │
                                   │  监控 · 评估 CI · 成本治理 ·         │
                                   │  人机协同                              │
                                   └──────────────────┬────────────────────┘
                                                      │
                                   ┌──────────────────┴────────────────────┐
                                   │         多 Agent 编排                  │
                                   │  Supervisor/Debate/Voting/Pipeline    │
                                   │  A2A 协议 · Agent-to-Agent 网格       │
                                   │  来源：Google A2A 规范 v0.3           │
                                   └──────────────────┬────────────────────┘
                                                      │
                        ┌─────────────────────────────┴─────────────────────────────┐
                        │                   互操作性与通信                          │
                        │  MCP（Model Context Protocol）· 工具即服务 · 资源         │
                        │  来源：MCP 规范 2025-11-25（Anthropic）                    │
                        │  Function Calling · 结构化输出（strict: true）             │
                        │  来源：OpenAI Function Calling 指南（2025）                 │
                        └─────────────────────────────┬─────────────────────────────┘
                                                      │
          ┌───────────────────────────────────────────┴─────────────────────────────────────────────┐
          │                                  Agent 模式                                             │
          │  Augmented LLM → Prompt Chaining → Routing → Parallelization → Orchestrator-Workers     │
          │  → Evaluator-Optimizer → Autonomous Agent                                               │
          │  来源：Anthropic《Building Effective Agents》（2025）                                     │
          │                                                                                          │
          │  ReAct（Thought→Action→Observation）       Reflexion（Actor→Evaluator→Reflect）           │
          │  来源：Yao et al., 2022                    来源：Shinn et al., 2023                      │
          └───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                      │
                              ┌───────────────────────┴─────────────────────────┐
                              │              框架与运行时                        │
                              │  LangGraph（StateGraph + Pregel 执行引擎）        │
                              │  OpenAI Agents SDK（Agent + Handoff + Guardrails）│
                              │  Google ADK（LlmAgent, SequentialAgent, Parallel）│
                              └───────────────────────┬─────────────────────────┘
                                                      │
                    ┌─────────────────────────────────┴─────────────────────────────────┐
                    │                        检索增强生成（RAG）                         │
                    │  索引流水线：加载 → 分块 → 向量化 → 存储                           │
                    │  检索策略：稠密 → 稀疏 → 混合 → 迭代                               │
                    │  重排序 · 查询改写 · Agentic RAG                                   │
                    └─────────────────────────────────┬─────────────────────────────────┘
                                                      │
          ┌───────────────────────────────────────────┴─────────────────────────────────────────────┐
          │                                   评估（EvALS）                                         │
          │  基于代码的评分器 · 基于模型的评分器（LLM-as-jude） · 人工评分器                          │
          │  pass@k 适用于开发工具 · pass^k 适用于面向客户的可靠性                                  │
          │  来源：Anthropic《Demystifying Evals for AI Agents》（2026）                            │
          └───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                      │
          ┌───────────────────────────────────────────┴─────────────────────────────────────────────┐
          │                            工具调用 · 结构化输出                                       │
          │  Function Calling · 工具描述最佳实践 · ACI（Agent-Computer Interface）                   │
          │  来源：Anthropic《Writing Effective Tools for Agents》（2025）                           │
          │  来源：OpenAI Function Calling 指南（o3/o4-mini, 2025）                                  │
          └───────────────────────────────────────────┬─────────────────────────────────────────────┘
                                                      │
          ┌───────────────────────────────────────────┴─────────────────────────────────────────────┐
          │                                  LLM 基础                                               │
          │  Transformers · Tokenization · Attention · Embeddings                                   │
          │  Prompt 工程 · Chain-of-Thought · System Prompts                                        │
          │  参考：Mialon et al., 2023（ALM 综述）中关于工具增强 LLM 的框架                           │
          └─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 学习架构：自底向上的学习地图

上述内容需要按顺序学习。以下是按依赖关系结构化的学习路径——每个条目是位于其上方条目的前置条件。

```
                    ┌────────────────────────────────────────┐
                    │  终章：生产级 Agent 系统                │
                    │  融合：RAG + Agent 模式 +             │
                    │  评估 + MCP 工具 + 部署               │
                    └───────────────┬────────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │              多 Agent 系统                     │
            │  阅读：Anthropic 编排模式                       │
            │  阅读：Google A2A 规范（v0.3）                 │
            │  练习：LangGraph Supervisor 模式               │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │              评估基础设施                      │
            │  阅读："Demystifying Evals"（Anthropic 2026）  │
            │  练习：用 pass@k 方法为代码 Agent               │
            │  构建评估框架                                   │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │           编排 + 框架                          │
            │  阅读：LangGraph StateGraph 参考               │
            │  阅读：OpenAI Agents SDK 文档                  │
            │  练习：用 StateGraph 实现 ReAct                │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │        Reflexion + 自我改进                    │
            │  阅读：Reflexion 论文（Shinn et al., 2023）    │
            │  练习：为代码生成的 ReAct Agent                │
            │  添加 Evaluator-Optimizer 循环                 │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │       ReAct + 工具调用 + MCP                   │
            │  阅读：ReAct 论文（Yao et al., 2022）         │
            │  阅读："Writing Effective Tools"（Anthropic） │
            │  阅读：MCP 规范（2025-11-25）                  │
            │  练习：手动实现 ReAct 循环                      │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │           RAG + 检索                           │
            │  阅读：ALM 综述（Mialon et al., 2023）         │
            │  练习：从零搭建 RAG 流水线                      │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │    LLM API + 结构化输出 + Prompt               │
            │  阅读：OpenAI Function Calling 指南（2025）    │
            │  练习：使用 strict 模式的 Function Calling     │
            └───────────────────────┬───────────────────────┘
                                    │
            ┌───────────────────────┴───────────────────────┐
            │     基础：Transformers + Embeddings            │
            │  参考：ALM 综述以建立整体框架                  │
            │  目标：理解 LLM 是什么、不是什么               │
            └───────────────────────────────────────────────┘
```

---

## 5. 逐模块分析

### 5.1 推理与行动：ReAct 范式

**一手资料。** Yao et al.（2022），arXiv:2210.03629。

**为什么它是基石。** 每个现代 Agent 框架——LangGraph 的 `create_react_agent`、OpenAI 的 Responses API、Anthropic 的 Claude Agent SDK——都实现了 ReAct 所引入的同一基础循环。当今不存在不继承自这篇论文的 Agent 架构。

**ReAct 的架构解剖。**

ReAct 将 LLM 调用不视为一次性的问答，而是顺序决策过程中的一个步骤。Agent 在时刻 `t` 的状态为：

```
state_t = (指令, 上下文, [{思考_1, 行动_1, 观察_1}, ..., {思考_t, 行动_t, 观察_t}])
```

在每一步，LLM 消费整个轨迹并产生：

```
思考_{t+1}  →  行动_{t+1}  →  观察_{t+1}
```

这**不是** Chain-of-Thought。CoT 只产生推理 token；ReAct 产生推理 token **和**可执行的动作。这种区分至关重要：CoT 可能产生幻觉事实，而 ReAct 通过实际调用外部系统来锚定自身。

**论文中的关键设计决策：**

1. **停止条件。** 论文使用最大步数限制（例如 6 步）来防止无限循环。现代系统使用更精细的条件：token 预算、超时、语义收敛检测。

2. **动作空间设计。** 论文的动作空间包含 `search[entity]`、`lookup[string]` 和 `finish[answer]`。其原理可推广：每个动作应该是原子的、可测试的，并具有清晰文档化的返回类型。

3. **Few-shot 轨迹。** 论文为 HotpotQA 手工编写了 6 条 ReAct 轨迹。现代系统改用 system prompt，但原理依然成立：上下文中工具调用的示例能显著提升可靠性。

**论文未涉及的内容（以及后来被构建的）：**
- **循环检测。** 论文观察到了 Agent 在相同的（思考，行动）对之间循环的问题，但没有解决。现代 LangGraph 实现通过状态哈希来处理。
- **记忆。** ReAct 在跨 episode 时是无状态的。Reflexion 在此基础上增加了情景记忆。
- **并行工具调用。** ReAct 循环是严格顺序的。OpenAI 的并行 function calling（2024+）和 LangGraph 的并行节点执行是后来的创新。

---

### 5.2 通过反思实现自我改进

**一手资料。** Shinn et al.（2023），arXiv:2303.11366。NeurIPS 2023。

**作为 ReAct 扩展的架构。**

Reflexion 不是替代 ReAct，而是包裹它。Actor 模块**就是**一个 ReAct agent。创新之处在它之上：

```
对于每次尝试：
  1. Actor（ReAct agent）→ 产生轨迹 + 结果
  2. Evaluator → 对结果评分（二元：成功/失败，或连续分数）
  3. Self-Reflection → 生成自然语言反馈：
      "你失败了，因为你用不完整的查询调用了 search()。
       下次，请使用完整实体名称。"
  4. 情景记忆 → 将反思附加到下一次尝试的 prompt 中
```

**语言强化学习的洞见。**

关键的知识贡献是：语言本身可以作为强化信号。传统 RL 需要标量奖励，通过梯度更新来处理。Reflexion 的"梯度"是对"哪里出了问题"的自然语言描述，"权重更新"是包含该描述的下一次 prompt。

这带来的实际影响：
- **无需模型微调**——仅需 API 即可使用
- **可解释的训练信号**——你可以实际读到 Agent "学到了"什么
- **任务可适配**——相同的架构适用于编程、问答和决策

**实际实现约束：**

论文的架构要求：
- **确定性或可复现的评估。** 当 Evaluator 可以明确判断成功/失败（例如单元测试通过/失败，答案精确匹配）时，Reflexion 效果最佳。在主观任务上效果会下降。
- **情景式任务结构。** Agent 必须能够重试相同或类似的任务。Reflexion 不会提升单次尝试的表现。
- **轨迹长度管理。** 每次尝试会将完整轨迹 + 反思追加到 prompt 中。上下文窗口很快被填满。现代实现会对旧轨迹进行摘要或压缩。

---

### 5.3 工具调用与结构化输出

本节综合了两份应该一起阅读的一手资料：
- **Anthropic（2025）：** "Writing Effective Tools for Agents"。工程博客。
- **OpenAI（2025）：** o3/o4-mini Function Calling 指南。官方开发者文档。

**Anthropic 的 ACI（Agent-Computer Interface）框架。**

Anthropic 的博客引入了 **Agent-Computer Interface** 概念——Agent 的 LLM 与其可调用的工具之间的边界。他们论证了 ACI 设计比 Agent 架构更为重要：设计精良的接口配合简单的 ReAct 循环，其表现优于配备设计糟糕工具的复杂循环。

**工具描述最佳实践（综合两个来源）：**

| 原则 | Anthropic 版本 | OpenAI 版本 |
|------|---------------|------------|
| **描述中规则前置** | "将最重要的使用规则放在工具描述的开头。" | "将关键指令放在首位时，准确率提升 3–6%。" |
| **功能合并** | "用一个 `schedule_event` 工具替代 `list_users`、`list_events`、`create_event`。" | "偏好小型可组合工具（`get_user`、`create_ticket`）胜过 `do_everything`。" |
| **返回有意义的标识符** | "返回自然语言标识符，而非 UUID。" | "设置 `strict: true` 以确保模式合规。" |
| **教授何时调用** | "描述何时应该以及何时**不应该**使用每个工具。" | "明确列出条件：'在……情况下使用。在……情况下不使用。'" |
| **Token 效率** | "支持分页、过滤和截断。" | "保持在 100 个以内工具，每个工具 20 个以内参数。" |

**结构化输出（`strict: true`）。**

OpenAI 的结构化输出功能（2024 年 6 月引入，2025 年持续改进）保证了模型生成的参数严格符合所提供的 JSON Schema。这并非"锦上添花"——它是生产级 Agent 系统可靠性的前置条件。

目前支持的关键约束（截至 2025 年）：
- 字符串字段的正则模式
- 邮箱格式验证
- 数字最小/最大值约束
- 数组长度约束
- `additionalProperties: false`（防止幻觉字段）

**两个来源都强调的重要警示："在服务端进行验证。"** 结构化输出保证模式一致性，但不保证语义正确性。`refund_amount` 为 `$0.01` 可能在模式上是合法的，但在功能上是错误的。

---

### 5.4 检索增强生成（RAG）

**一手资料。** Mialon et al.（2023），"Augmented Language Models: A Survey"，为检索作为工具调用类别提供了理论框架。

**RAG 作为工具调用的特例。**

ALM 综述将检索定义为工具调用的一个特定类别，其中工具是知识库上的搜索引擎。Agent 推理它需要什么信息，调用检索器，并以检索到的上下文为条件进行生成。这是 ReAct 循环的特例，其中动作始终是 `retrieve(query)`。

**RAG 系统的架构组件：**

1. **索引流水线。** 文档→加载器→分块器→向量化器→向量存储。每个阶段都是一个设计决策点。
   - 分块粒度控制精确度与召回率的权衡。
   - Embedding 模型选择（稠密 vs. 稀疏 vs. 混合）决定了"相似性"的含义。

2. **检索策略（来自综述的分类体系）：**
   - **稠密检索**（DPR、Contriever、text-embedding-3）：向量空间中的语义相似性。
   - **稀疏检索**（BM25）：关键词重叠。与稠密检索互补——它们检索出不同的结果。
   - **混合检索**：融合稠密+稀疏分数。在综述的分析中，始终优于单独使用任何一种。
   - **迭代检索**：多步检索，一次查询的结果为下一次查询提供信息。将 RAG 过渡到 Agentic 范畴。

3. **RAG→Agentic RAG 的过渡。**
   标准 RAG 系统检索一次然后生成。Agentic RAG 系统让 LLM 决定："我是否拥有足够的信息，还是应该再次检索？"这不是一种独立的架构——它是应用于检索的 ReAct，其中动作空间包括 `retrieve` 和 `finish`。

---

### 5.5 Anthropic 编排模式

**一手资料。** Anthropic（2025），"Building Effective Agents"。工程博客。
**链接：** https://www.anthropic.com/engineering/building-effective-agents

这份指南可以说是该领域最重要的实践文档。它定义了六种模式的正式分类体系，并且关键的是，为每种模式的使用时机提供了决策规则。

**六种模式，按复杂度排序：**

**1. Augmented LLM（基本构建块）**
一个通过检索、工具和记忆增强的 LLM。Anthropic 推荐通过 MCP 实现工具访问。这是所有更大模式组合的原子单元。

**2. Prompt Chaining**
将任务分解为顺序步骤，每步的输出输入到下一步。程序化的"门控"验证中间输出。
- **何时使用：** 任务可以自然地分解为固定的顺序子任务（例如，营销文案→翻译）。
- **何时不使用：** 当子任务输出无法通过程序验证时。
- **关键属性：** 步骤数量在设计时已知。

**3. Routing**
对输入进行分类并分发到专门的处理程序。
- **何时使用：** 输入属于有明显区别的类别，各自受益于不同处理（例如，退款 vs. 技术支持查询）。
- **关键属性：** 路由决策是确定性的（基于分类），而非生成性的。

**4. Parallelization**
两种形式：**Sectioning**（将任务拆分为独立子任务）和 **Voting**（对同一任务多次运行）。
- **何时使用：** 子任务真正独立时（Sectioning），或需要多角度视角以提升质量时（Voting）。
- **关键属性：** 在聚合之前，并行分支之间无共享状态。

**5. Orchestrator-Workers**
一个中央 LLM 动态地分解任务，委派给 worker LLM，然后合成结果。与 Parallelization 的关键区别：子任务**在设计时不可知**——orchestrator 动态决定分解方式。
- **何时使用：** 无法提前预测分解方式的复杂任务（例如，多文件代码变更、开放式研究）。
- **关键属性：** Orchestrator 可以根据部分结果重新规划。

**6. Evaluator-Optimizer**
Generator + Critic 在迭代循环中工作。Evaluator 提供反馈，Generator 进行改进。
- **何时使用：** 存在明确的评估标准（例如，代码编译通过、翻译保留了原意、答案有事实依据）。
- **何时不使用：** 评估具有主观性或标准不明确。循环会放大 Evaluator 的噪声。
- **实现说明：** Generator 和 Evaluator 可以是同一个 LLM，只是使用不同的 prompt。这在 Anthropic 的术语中就是 Reflexion 架构。

**自主 Agent（隐式的第 7 种模式）**
Agent 在循环中操作，使用工具，做出决策，可能包含人类介入的检查点。Anthropic 的建议是：**仅在**任务绝对需要上述任何模式都无法捕获的开放式决策时才使用这种模式。

**Anthropic 的决策规则（意译）：**

> "从最简单的可能解决方案开始。通常，这只是一个优化过的单次 LLM 调用，加上检索和上下文示例。只有当你能证明更简单的方法在评估套件上失败时，才添加工作流模式。只有当工作流模式失败时，才添加完全的 Agent 自主性。"

这是整份文档中最重要的战略指导原则。

---

### 5.6 框架对比：LangGraph、OpenAI SDK、Google ADK

每个框架以不同的架构权衡实现 §5.5 中的模式。

#### LangGraph（LangChain）

**一手资料。** LangGraph 官方参考文档（Python 和 TypeScript）。

**架构。** LangGraph 将 Agent 工作流建模为**带状态的有向图**。核心抽象是 `StateGraph`，定义如下：
- **状态模式**（带 reducer 的 TypedDict）：每个节点读取和写入的共享"黑板"。
- **节点**（Python 函数）：每个节点接收完整状态并返回状态更新。
- **边**（静态或条件）：定义图拓扑。

**执行引擎。** LangGraph 的运行时受 Google **Pregel** 系统的启发——一个带有离散超级步的消息传递模型。关键能力：
- **检查点**（通过 `BaseCheckpointSaver` 持久化）：状态可保存和恢复。
- **中断**（`interrupt()` / `Command(resume=...)`）：在任意节点实现人机协同。
- **并行执行**：超级步内的节点可并发运行。

**LangGraph 中的 ReAct 循环（规范示例）：**
```
START → agent（LLM）→ 条件边：
  如果有 tool_calls：→ tools → agent（循环回去）
  否则：→ END
```

有了检查点机制，这个循环可以被暂停、检查和恢复——从而实现人机协同监督。

**为什么 LangGraph 对学习很重要。** LangGraph 使 ReAct 循环和状态管理变得显式可见。用 LangGraph 构建 ReAct 循环相当于"编写 Agent 架构的编译器"——它迫使你理解每一个组件。

#### OpenAI Agents SDK

**一手资料。** OpenAI 官方开发者文档（2025）。

**架构。** SDK 提供四个原语：
- **Agent**：配置了指令、工具、护栏和转交设置的 LLM。
- **Handoff**：Agent 到 Agent 的控制转移。接收方 Agent 获得完整的对话上下文。
- **Guardrails**：与 Agent 同时运行的并行输入/输出验证（非顺序运行——这是一个关键设计选择）。
- **Runner**：执行循环。处理工具调用、LLM 迭代和追踪收集。

**关键设计哲学。** 最小抽象。SDK 有意不提供内置工作流模式（Sequential、Parallel、Loop）。取而代之的是，它提供 handoff 机制，让开发者在纯 Python 中组合模式。

**权衡：** 学习更容易（更少抽象），但超过 8–10 个 Agent 后，手动编排变得笨重。适合以下团队：
- 需要干净的 Agent 到 Agent 转交机制。
- 偏好编写 Python 而非配置图状态模式。
- 不需要内置编排模式。

#### Google ADK（Agent Development Kit）

**一手资料。** Google ADK 官方文档（2025–2026）。Google Cloud Blog。

**架构。** ADK 提供了一个层次化的 Agent 模型，包含五种内置 Agent 类型：

| Agent 类型 | 行为 |
|-----------|------|
| `LlmAgent` | 标准 ReAct 风格 LLM agent |
| `SequentialAgent` | 带共享状态的线性流水线 |
| `ParallelAgent` | 并发执行，收集结果 |
| `LoopAgent` | 迭代优化直到满足条件 |
| `CustomAgent` | 扩展 `BaseAgent` 实现任意逻辑 |

**组合模型。** Agent 可以层次化地组合。`LlmAgent` 可以通过 `AgentTool` 将另一个 Agent 作为工具调用。这意味着 Agent 可以任意嵌套：一个 supervisor agent（本身是由多个分类器组成的 `SequentialAgent`）将 worker agent 作为工具进行委派。

**A2A 集成。** ADK 原生支持 A2A 协议，意味着 ADK Agent 可以通过标准 A2A 有线协议与其他框架构建的 Agent（CrewAI、LangGraph 等）通信。这在三个框架中是独特的。

**权衡：** 更多抽象需要学习。相比 OpenAI SDK 认知负担更重。最适合以下团队：
- 在 Google Cloud 上构建企业系统。
- 需要多模态 Agent（通过 Gemini 处理文本+视觉+音频）。
- 需要内置编排模式和 A2A 互操作。

---

### 5.7 互操作性：MCP 与 A2A

这两个协议代表了 Agent 生态系统的"南北"和"东西"通信平面。

#### MCP（Model Context Protocol）

**一手资料。** MCP 规范，版本 2025-11-25。modelcontextprotocol.io。

**角色。** MCP 标准化了**Agent 到工具**的通信（南北方向：Agent 连接到外部系统）。

**架构模型：**
```
Host（例如 Claude Desktop）←→ Client（SDK）←→ MCP Server ←→ 外部系统
```
- **Host**：用户交互的应用程序。
- **Client**：传输层连接器，通过 SSE 或 HTTP 使用 JSON-RPC 2.0 通信。
- **Server**：暴露三种能力类型：
  - **Resources**——可读取的数据（文件、API 响应）。
  - **Tools**——LLM 可调用的函数（搜索、发送邮件等）。
  - **Prompts**——为常见任务预编写的模板。

**关键规范细节（2025-11-25）：**
- **授权**：OAuth 2.0 强制要求 PKCE。支持 OpenID Connect Discovery。
- **传输**：通过 HTTPS 或 SSE 的 JSON-RPC 2.0。不支持批处理（2025-06-18 的破坏性变更中移除）。
- **安全**："混淆代理人"防护——MCP 代理不能盲目转发 Token。需要进行 audience 验证。
- **Tasks（实验性）**：全新的持久化、长运行工作的抽象。状态：`working → input_required → completed / failed / cancelled`。
- **工具命名**：标准化的工具名称约定。

#### A2A（Agent-to-Agent）

**一手资料。** Google A2A 规范，v0.3（2025 年 7 月）。google.github.io/A2A/。

**角色。** A2A 标准化了**Agent 到 Agent**的通信（东西方向：Agent 互相发现和委派任务）。

**架构模型：**
```
Agent A ←→ A2A 协议 ←→ Agent B（任意框架）
```

**核心概念：**
- **Agent Card**（`.well-known/agent.json`）：每个 Agent 发布，描述能力、端点、认证方法。
- **Task**：基本工作单元。生命周期：`submitted → working → input-required → completed / failed / canceled`。
- **Message/Part**：任务中的多模态内容（文本、文件、数据）。
- **PushNotificationService**：解耦的异步更新 webhook，通过 JWT 保障安全。

**关键设计原则：**
- 基于现有 Web 标准（HTTP、SSE、JSON-RPC 2.0）。
- 企业级认证（JWT、OIDC、OAuth 2.0）。
- 支持同步和长时间运行的异步任务。
- 模态无关（文本、视频、音频、结构化数据）。

**MCP vs. A2A（综合对比）：**

| | MCP | A2A |
|---|---|---|
| **方向** | Agent → 工具 | Agent → Agent |
| **标准制定方** | Anthropic | Google |
| **协议** | JSON-RPC 2.0 | JSON-RPC 2.0（+ SSE） |
| **认证** | OAuth 2.0 + PKCE | OAuth 2.0 / OIDC |
| **范围** | 工具/资源访问 | 任务委派 |
| **成熟度** | v2025-11-25（稳定） | v0.3（快速迭代中） |
| **治理** | Anthropic + 社区 | Linux Foundation |

**实际意义：** MCP 和 A2A 是互补的。Agent 使用 MCP 访问工具，使用 A2A 将子任务委派给其他 Agent。

---

### 5.8 评估即基础设施

**一手资料。** Anthropic（2026），"Demystifying Evals for AI Agents"。工程博客（2026 年 1 月 9 日）。
**链接：** https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

**文章的核心论点：**

> "没有评估的团队会陷入被动的调试循环——发布变更，观察到失败，然后回滚。评估在 Agent 的整个生命周期中提供复利价值，实现更快的迭代和更安全的模型升级。"

**三种评分器类型：**

| 评分器 | 示例 | 速度 | 成本 | 可靠性 |
|--------|------|------|------|--------|
| **基于代码的** | 字符串匹配、单元测试、linting | 最快 | 低 | 确定性（但脆弱） |
| **基于模型的** | LLM-as-judge、评分标准打分 | 中等 | 中等 | 不确定性（但有辨别力） |
| **人工** | 专家审查、A/B 测试 | 最慢 | 高 | 黄金标准 |

**针对 Agent 类型的评估策略：**

| Agent 类型 | 推荐评估方法 |
|-----------|-------------|
| **代码 Agent** | 单元测试、静态分析、SWE-bench、Terminal-Bench |
| **对话 Agent** | 状态检查 + LLM rubric + 模拟用户（τ-Bench） |
| **研究 Agent** | 依据性检查 + 覆盖度 + 来源质量 |
| **计算机使用 Agent** | 沙箱环境 + 结果验证（WebArena、OSWorld） |

**处理非确定性（pass@k vs. pass^k）：**

| 指标 | 定义 | 何时使用 |
|------|------|----------|
| **pass@k** | k 次尝试中至少 1 次成功 | 开发工具，允许重试 |
| **pass^k** | 全部 k 次尝试均成功 | 面向客户场景，不允许重试 |

**八步路线图（摘自文章）：**

1. **尽早开始。** 在编写 Agent 代码之前，先用 20-50 个真实失败案例构建评估。
2. **编写明确无歧义的任务。** 两位领域专家应该对正确结果达成一致。
3. **阅读对话记录。** 仅靠聚合指标会掩盖失败模式。定期阅读追踪记录。
4. **监控饱和。** 当评估达到 100% 通过率时，它们就不再有用——添加更困难的任务。
5. **优先任务级别的评估。** 对于大多数用例，任务级别（Agent 是否达成了目标？）优于步骤级别（是否选择了正确的工具？）。
6. **测试模型升级。** 切换模型时运行完整的评估套件。结果会有显著差异。
7. **将评估视为 CI。** 每次 Agent 变更在部署前都通过评估套件运行。
8. **迭代评估质量。** 评估本身会随时间退化——将它们像代码一样维护。

---

## 6. 建议学习顺序

此顺序由**依赖关系**驱动（每项内容是下一个项的前置准备），并**仅使用一手资料**（不使用教程、不使用聚合器）。

### 第一阶段：基础（阅读与理解）

| # | 工作内容 | 以此为顺序的原因 |
|---|---------|-----------------|
| 1 | Mialon et al. 2023——"Augmented Language Models: A Survey" | 建立术语和分类体系。理解文献中"工具调用"、"检索"和"推理"的含义。 |
| 2 | Yao et al. 2022——"ReAct" 论文 | 最具影响力的单篇论文。理解 Thought→Action→Observation 循环。用 LLM API 手动实现它（约 30 行 Python）。 |
| 3 | Anthropic 2025——"Writing Effective Tools for Agents" | 在构建任何 Agent 之前，先理解如何设计 LLM 与其工具之间的接口。 |
| 4 | OpenAI Function Calling 指南（o3/o4-mini, 2025） | 理解工具调用的生产级实现：`strict: true`、结构化输出、描述最佳实践。 |
| 5 | MCP 规范 2025-11-25 | 工具集成的标准协议。阅读规范，然后在本地运行一个 MCP server。 |

### 第二阶段：模式与框架（构建）

| # | 工作内容 | 以此为顺序的原因 |
|---|---------|-----------------|
| 6 | Anthropic 2025——"Building Effective Agents" | 阅读六种模式分类体系。这是你进行架构决策的框架。 |
| 7 | LangGraph 官方 StateGraph 参考 | 用 LangGraph 构建来自（6）的六种模式。从 Prompt Chaining 开始，以 Evaluator-Optimizer 结束。 |
| 8 | Shinn et al. 2023——"Reflexion" 论文 | 理解自我改进。实现一个带 Reflexion 式语言强化学习的代码 Agent。 |
| 9 | OpenAI Agents SDK 文档 | 用不同的框架构建相同的模式。对比开发者体验。 |
| 10 | Google ADK 文档 | 在第三个框架中构建相同的模式。如果多 Agent 在计划内，重点关注 A2A 集成。 |

### 第三阶段：评估与生产（度量）

| # | 工作内容 | 以此为顺序的原因 |
|---|---------|-----------------|
| 11 | Anthropic 2026——"Demystifying Evals for AI Agents" | 阅读评估方法论。这会改变你如何看待之前的所有工作。 |
| 12 | A2A 规范 v0.3 | 多 Agent 互操作性。阅读规范，然后构建一个使用 A2A 的双 Agent 系统。 |
| 13 | **终章项目** | 构建一个融合以下内容的生产级 Agent 系统：RAG 流水线 + ReAct 循环 + MCP 工具 + Evaluator-Optimizer 循环 + 评估框架 + 向一个专家 Agent 的 A2A 转交。 |

### 每个阶段的实现说明

在每个阶段中，正确的顺序是：**先阅读一手资料，然后实现**。不要读关于论文的教程或博客文章——直接读论文本身。论文每篇不到 10 页。工程博客用不到 20 分钟就能读完。规范文档较长但可以略读（专注于架构部分）。

---

## 7. 参考文献

### 学术论文

1. **Yao, S.**, Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y.（2022）。ReAct: Synergizing Reasoning and Acting in Language Models。*arXiv:2210.03629*。ICLR 2023。
   - https://arxiv.org/abs/2210.03629

2. **Shinn, N.**, Cassano, F., Berman, E., Gopinath, A., Narasimhan, K., & Yao, S.（2023）。Reflexion: Language Agents with Verbal Reinforcement Learning。*arXiv:2303.11366*。NeurIPS 2023。
   - https://arxiv.org/abs/2303.11366

3. **Mialon, G.**, Dessì, R., Lomeli, M., Nalmpantis, C., Pasunuru, R., Raileanu, R., Rozière, B., Schick, T., Dwivedi-Yu, J., Celikyilmaz, A., Grave, E., LeCun, Y., & Scialom, T.（2023）。Augmented Language Models: A Survey。*arXiv:2302.07842*。TMLR 2023。
   - https://arxiv.org/abs/2302.07842

### 工程博客（一手资料）

4. **Anthropic.**（2025）。Building Effective Agents。
   - https://www.anthropic.com/engineering/building-effective-agents

5. **Anthropic.**（2025）。Writing Effective Tools for Agents。
   - https://www.anthropic.com/engineering/writing-tools-for-agents

6. **Anthropic.**（2026）。Demystifying Evals for AI Agents。
   - https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

### 框架与协议文档（一手资料）

7. **LangChain.** LangGraph 官方文档——StateGraph, CompiledGraph, create_agent API。
   - https://langchain-ai.github.io/langgraph/
   - https://reference.langchain.com/javascript/langchain-langgraph/index/StateGraph

8. **OpenAI.** Function Calling 指南——o3/o4-mini Prompting Guide（2025）。
   - https://help.openai.com/en/articles/8555517-function-calling-in-the-openai-api
   - https://developers.openai.com/cookbook/examples/o-series/o3o4-mini_prompting_guide

9. **Google.** Agent Development Kit（ADK）官方文档。
   - https://google.github.io/adk-docs/

10. **Anthropic.** Model Context Protocol（MCP）规范，v2025-11-25。
    - https://modelcontextprotocol.io/specification

11. **Google.** Agent-to-Agent（A2A）协议规范，v0.3。
    - https://google.github.io/A2A/
    - https://github.com/google-a2a/A2A

---

*本报告仅基于一手资料。每一条论断均可追溯至第 7 节中列出的原始文献。未使用任何博客聚合器、教程网站或二次摘要。*
