# Pi 源码解析教程

一套针对本仓库（pi monorepo，本地版本 `0.85.1`）的中文源码学习教程。目标读者：**已经写过 agent 项目、想看懂一个工业级 agent 代码库是如何组织的工程师**。不解释"什么是工具调用 / 什么是流式输出"这类基础概念，重点回答：**这套概念在一个十万行级的项目里，落地成了什么样的结构，以及为什么是这样。**

## 全书主线

整个教程围绕一条主线展开，建议先读第 2 章建立全景：

> 用户输入一句"读取 README.md 并总结" → 界面层提交 → 应用层加工 → 执行内核循环 → 模型层请求 → 工具真正执行 → 结果回到对话 → 再次请求模型 → 最终回答 → 落盘并渲染。

读完第 2 章，你应该能独立回答三个问题：

1. **谁持有消息状态？**（transcript，贯穿四层的一等公民）
2. **谁真正执行工具？**（agent 内核，不是模型）
3. **什么条件会再次请求模型？**（工具调用未终结 + steering 队列非空）

后续所有章节都是对这条主线上某一站的展开。

## 章节目录

### 第一部分：全景（先建立地图）

| 章节 | 内容 | 关键源码 |
|---|---|---|
| [第 1 章 项目全景与分层架构](01-architecture.md) | monorepo 包清单、依赖图、分层思想、四条设计主线 | 根 `README.md`、各包 `package.json` |
| [第 2 章 一次请求的完整旅程](02-request-lifecycle.md) | 全链路总览：从输入到落盘的完整追踪 | 串联全部核心文件 |

### 第二部分：核心执行链（教程主体，按依赖顺序读）

| 章节 | 内容 | 关键源码 |
|---|---|---|
| [第 3 章 入口与启动流程](03-startup.md) | `main()` 时序、手写 CLI 解析、三种运行模式、交互模式初始化 | `coding-agent/src/main.ts` |
| [第 4 章 SDK 与会话组装](04-sdk-assembly.md) | `createAgentSession()` 组合根、Services/Session/Runtime 三层拆分、配置体系 | `coding-agent/src/core/sdk.ts` |
| [第 5 章 AgentSession：应用编排层](05-agent-session.md) | `prompt()` 管线、steering/followUp 双队列、事件转发 | `coding-agent/src/core/agent-session.ts` |
| [第 6 章 agent 包：执行内核](06-agent-core.md) | `Agent` 状态机、`agentLoop` 循环、事件系统、错误哲学 | `agent/src/agent.ts`、`agent/src/agent-loop.ts` |
| [第 7 章 工具执行系统](07-tools.md) | `AgentTool` 接口、8 个内置工具的实现细节、并发与截断策略、权限模型 | `coding-agent/src/core/tools/` |
| [第 8 章 ai 包：模型统一层](08-ai-layer.md) | 统一消息/事件模型、provider 适配器、流式归一化、鉴权、缓存与计费 | `ai/src/types.ts`、`ai/src/api/` |

### 第三部分：数据与上下文（状态的归宿）

| 章节 | 内容 | 关键源码 |
|---|---|---|
| [第 9 章 会话持久化与分支](09-sessions.md) | JSONL 树形会话、fork/tree、崩溃恢复、resume 重建 | `coding-agent/src/core/session-manager.ts` |
| [第 10 章 上下文工程](10-context.md) | system prompt 分节组装、AGENTS.md 注入、compaction 压缩算法 | `coding-agent/src/core/system-prompt.ts`、`core/compaction/` |

### 第四部分：生态与界面

| 章节 | 内容 | 关键源码 |
|---|---|---|
| [第 11 章 扩展生态](11-extensions.md) | 扩展事件全景、工具拦截实现审批、skills、斜杠命令、子代理 | `coding-agent/src/core/extensions/` |
| [第 12 章 tui 包：终端界面](12-tui.md) | `render(width)` 协议、差分渲染、Editor、自动补全、IME 支持 | `tui/src/` |

### 第五部分：工程与进阶

| 章节 | 内容 | 关键源码 |
|---|---|---|
| [第 13 章 测试体系](13-testing.md) | `test.sh` 隔离机制、faux provider、harness 驱动完整循环、回归组织 | `coding-agent/test/suite/` |
| [第 14 章 进阶方向与架构启示](14-advanced.md) | chord / durable / protocol-client-server、实验架构、可借鉴的设计清单 | `packages/chord` 等 |

## 阅读路线

- **快速路线（半天）**：第 1、2、6 章。理解分层 + 主线 + 内核循环，就能定位大部分代码。
- **标准路线（2-3 天）**：按顺序读完 1-10 章，配合打开源码对照。
- **完整路线**：全部章节。第 11-14 章可以按兴趣挑读。

无论走哪条路线，都建议配合两个不花钱的运行入口（在 `packages/coding-agent` 目录下）：

```bash
# 不调用模型的示例：技能加载、上下文文件发现
npx tsx --tsconfig ../../tsconfig.json examples/sdk/04-skills.ts
npx tsx --tsconfig ../../tsconfig.json examples/sdk/07-context-files.ts

# 会调用模型、产生 API 费用的最小示例
npx tsx --tsconfig ../../tsconfig.json examples/sdk/01-minimal.ts
```

以及从源码启动完整程序：仓库根目录 `./pi-test.sh`。

## 本教程的约定

- 源码路径一律相对仓库根目录书写，如 `packages/agent/src/agent.ts`。
- 行号基于撰写时的快照（`0.85.1`，commit `36b60d2e8` 附近），仅作定位辅助；**函数名 + 文件名是更可靠的锚点**，代码演进后请以它们为准。
- 引用的代码片段为讲解做过删减，以真实源码为准。
- 每章末尾附「本章问题」，建议先自己回答再进入下一章。

## 阅读前置：五个反复出现的概念

这些词在全书高频出现，先在此统一解释：

1. **transcript（对话记录）**：按序排列的全部消息（system/user/assistant/toolResult…）。pi 的一个核心决定是：系统提示词和工具声明**不是独立配置，而是 transcript 里的 system 消息**——按序回放即得到当前状态。第 6、10 章展开。
2. **steering / followUp**：agent 运行中用户再输入的两条去向。steering 在当前回合的工具批次之间注入（"边跑边改指令"）；followUp 等agent 完全停止后才投递（"排下一个任务"）。第 5、6 章展开。
3. **streamFn**：调用模型的函数抽象。agent 内核不认识 Anthropic/OpenAI，只认识 `StreamFn`；ai 包是它的实现。第 6、8 章展开。
4. **扩展（extension）**：运行时注入的 JS 模块，通过事件钩子（`tool_call`、`before_agent_start`…）参与一切。pi 没有内置工具审批，审批就是用扩展实现的。第 7、11 章展开。
5. **compaction（压缩）**：上下文接近窗口上限时，把旧对话总结成摘要、只保留近期消息的机制。第 10 章展开。
