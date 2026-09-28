# 第 1 章 项目全景与分层架构

> 本章回答：这个仓库里有哪些包、谁依赖谁、整体上分几层、有哪几条贯穿全库的设计主线。读完你应该能拿着任何一个文件路径，说出它属于哪一层、职责是什么。

## 1.1 pi 是什么

pi 是一个**终端里的 AI 编程助手**（类似 Claude Code / Codex CLI），同时把底层能力拆成了若干可独立复用的 npm 包。它不是"一个大应用"，而是一个 **monorepo：多个包组成的产品族**，用 npm workspaces 管理，全部 ESM + TypeScript，要求 Node >= 22.19。

真实可执行的产品只有一个：`packages/coding-agent`（命令 `pi`）。其余包都是它的依赖库或下一代架构的实验场。

## 1.2 包清单与依赖图

以下是全部包及相互依赖关系（读各包 `package.json` 的 `dependencies` 汇总）：

```
                    ┌─────────────┐   ┌───────────┐
                    │  telemetry  │   │   chord   │   ← 底座（互不依赖，也不依赖其他 pi 包）
                    └──────┬──────┘   └────┬──────┘
                           │               │
                    ┌──────┴──────┐        │
                    │     ai      │        │      统一模型层：40+ provider、流式归一化
                    └──────┬──────┘        │
                    ┌──────┴──────┐        │
                    │    agent    ├────────┘      执行内核：Agent 循环、工具执行、harness
                    └──────┬──────┘
              ┌────────────┼────────────┐
              │            │            │
       ┌──────┴─────┐ ┌────┴─────┐ ┌────┴─────┐
       │  durable   │ │ protocol │ │  server  │     下一代线：持久运行时 / 进程间协议
       └────────────┘ └────┬─────┘ └──────────┘
              ┌────────────┤
              │            │
       ┌──────┴─────┐ ┌────┴─────┐
       │   client   │ │ coding-agent │ ← 顶层产品（依赖 chord + agent + ai + tui）
       └────────────┘ └───────────┘

  独立包：tui（终端 UI 框架，只依赖 marked 和 get-east-asian-width）
          evals（评测）、session-backends/sqlite-node（SQLite 会话后端）
```

分层从下到上：

| 层 | 包 | 一句话职责 |
|---|---|---|
| 底座 | `chord` | 应用组合运行时：服务、复制状态、RPC、插件（standalone，不依赖任何 pi 包） |
| 底座 | `telemetry` | vendor-neutral 遥测契约（span/event），默认 NOOP |
| 基础库 | `tui` | 自研终端 UI 框架：组件树 + 差分渲染 |
| 模型层 | `ai` | 统一多家 LLM API：统一消息/事件模型、鉴权、计费、缓存 |
| 执行层 | `agent` | 有状态 agent 内核：循环、工具执行、事件流、steering 队列 |
| 数据层 | `durable` | 持久会话/任务/文档运行时（下一代，实验中） |
| 服务层 | `protocol` / `client` / `server` | 进程间通信：路由信封 + CBOR 分帧 / 客户端 / 本地服务器（实验中） |
| 产品层 | `coding-agent` | `pi` 命令本身：CLI、交互界面、会话管理、扩展系统、内置工具 |

根 `package.json` 的 `build` 脚本顺序完全印证这个拓扑：chord → tui → telemetry → ai → durable → agent → sqlite-backend → protocol → client → server → coding-agent。

**注意两个"意外"**：

- `chord` 和 `tui` 是完全独立的通用库，不含任何 pi 业务概念。作者刻意让它们可以脱离本仓库使用。
- `durable` / `protocol` / `client` / `server` 属于**下一代架构实验线**，与当前 `pi` 主线（coding-agent + agent + ai）并行存在，仅在 `PI_EXPERIMENTAL=1` 时启用。初学阶段可以完全忽略，第 14 章再讲。

## 1.3 主线架构：四层执行链

把依赖图里"当前产品实际用到的部分"抽出来，就是贯穿本书的主线：

```
┌──────────────────────────────────────────────────────────────┐
│ coding-agent（产品层）                                         │
│  main.ts → InteractiveMode / print-mode / rpc-mode            │
│    └─ AgentSession（应用编排：命令、模板、扩展、压缩、重试）        │
│         └─ AgentSessionRuntime（会话整体替换的宿主容器）           │
├──────────────────────────────────────────────────────────────┤
│ agent（执行内核）                                              │
│  Agent（状态 + 事件 + 队列）                                    │
│    └─ agentLoop（模型调用 → 工具执行 → 再调用 → …）               │
├──────────────────────────────────────────────────────────────┤
│ ai（模型层）                                                    │
│  Models/Provider → API 适配器（anthropic / openai / …）          │
│  统一 AssistantMessageEvent 流 + Usage + 鉴权                   │
├──────────────────────────────────────────────────────────────┤
│ tui（界面）—— 独立旁路：只消费事件，不参与执行决策                   │
└──────────────────────────────────────────────────────────────┘
```

每一层只依赖下一层的抽象：

- `AgentSession` 不直接发 HTTP 请求，它构造 `Agent` 并传入 `streamFn`；
- `Agent` / `agentLoop` 不认识任何厂商，只消费 `AssistantMessageEventStream`；
- 各 API 适配器负责把厂商私有格式翻译成统一事件；
- TUI 什么业务都不做，只订阅 session 事件渲染（交互模式 6600+ 行的 `interactive-mode.ts` 文件头注释写明："Handles TUI rendering and user interaction, delegating business logic to AgentSession"）。

这个"业务逻辑全部下沉到 SDK 层、界面只是又一个渲染器"的决策，使得同一个 `createAgentSession()` 既能驱动终端交互，也能驱动 `pi -p`（一次性输出）、`pi --mode json`（JSON 流）、`pi --mode rpc`（嵌入宿主）三种模式。

## 1.4 四条贯穿全库的设计主线

读任何一层之前，先记住这四条反复出现的设计决定。它们是理解大量"为什么这样写"的钥匙。

### 主线一：transcript 即真相（transcript as source of truth）

系统提示词、工具声明、模型选择——这些在其他框架里通常是"会话配置"的东西，在 pi 里全部是 **transcript 里的消息**：

- 首条 system 消息携带完整系统提示词和 `toolsAdded`（工具声明）；
- 运行中换工具/改提示词，不是改配置，而是追加一条带 `toolsAdded`/`toolsRemoved`/sections diff 的 **system 消息**；
- 按序回放 transcript，就能精确重建任意历史时刻的完整状态（`ai/src/utils/transcript.ts` 的 `getCurrentSystemMessage()` / `getCurrentTools()`）。

好处：resume、分支、压缩、回放都天然正确——它们都只是"沿 parentId 链回放消息"。代价：所有改动必须表达为"追加消息"，第 6、10 章会看到这带来的 diff 补丁机制。

### 主线二：事件驱动，错误也是事件

层与层之间通过事件流通信，而不是回调嵌套或共享可变状态：

- 模型层产出 `AssistantMessageEvent`（text_delta / toolcall_delta / done / error…）；
- 内核层把模型事件 + 工具执行翻译成 `AgentEvent`（9 种）；
- 应用层再扩展为 `AgentSessionEvent`，UI 只订阅这一种。

关键约定：**模型请求失败不抛异常**，错误被编码成流里的 `error` 事件和 `AssistantMessage.stopReason = "error" | "aborted"`。上层据此实现重试、UI 永远能看到闭合的消息生命周期（第 6 章 6.6 节）。

### 主线三：组合根 + 全量依赖注入

所有服务（SessionManager、SettingsManager、ResourceLoader、ModelRuntime…）都在 `createAgentSession()`（`coding-agent/src/core/sdk.ts`）这一个组合根里装配，且每个都可注入、每个都有内存实现（`inMemory()` / `InMemory*`）。这让整个应用可以完全脱离文件系统和网络测试（第 13 章）。

### 主线四：无沙箱的信任模型

pi **没有内置工具审批/权限模式**（没有 Claude Code 式的 default/acceptEdits/yolo）。`docs/security.md` 明说这是刻意的：进程内假沙箱"容易让人误解为安全边界"，真正的隔离应交给 OS/容器。实际存在的控制是：

- **工具启用名单**（`--tools` / `--exclude-tools` / settings）；
- **扩展拦截**（`tool_call` 事件可 block，第 11 章用它实现审批）;
- **项目信任**（防止 clone 一个仓库就被它注入 `.pi/extensions` 静默执行代码——这是唯一内置的"启动时审批"）。

这与大多数同类产品思路不同，值得作为设计对比素材（第 7 章 7.5 节）。

## 1.5 仓库物理结构速查

```
pi/
├── packages/
│   ├── coding-agent/         # 产品：pi 命令
│   │   ├── src/
│   │   │   ├── main.ts       # main() 编排
│   │   │   ├── cli/          # 参数解析、启动 UI
│   │   │   ├── core/         # ★ 编排核心（sdk/agent-session/session-manager/…）
│   │   │   ├── modes/        # interactive / print / rpc 三种模式
│   │   │   ├── tools/… core/tools/  # 内置工具实现
│   │   │   └── experimental/ # 下一代架构（client/server/mini）
│   │   ├── docs/             # 官方英文文档（sdk/session-format/compaction/…）
│   │   ├── examples/sdk/     # ★ 11 个 SDK 示例，最好的上手入口
│   │   └── test/suite/       # 行为测试 + 77 个 issue 回归
│   ├── agent/src/            # ★ Agent、agentLoop、harness/
│   ├── ai/src/               # ★ types、models、api/（适配器）、providers/、auth/
│   ├── tui/src/              # 组件、渲染器、editor、autocomplete
│   └── …
├── test.sh                   # 隔离环境跑全部测试（见第 13 章）
├── pi-test.sh                # 从源码启动 pi
├── AGENTS.md                 # 贡献者规约（也注入到模型的系统提示里）
└── CONTRIBUTING.md
```

标 ★ 的目录是本教程的主要活动区域。

另外两个实用入口：`packages/coding-agent/docs/` 下有官方英文文档（`sdk.md`、`session-format.md`、`compaction.md`、`extensions.md` 等），本教程大量交叉引用它们；`packages/agent/README.md` 是内核层最权威的行为规范（Message Flow / Event Flow 两节几乎是逐事件对应的规格说明）。

## 1.6 本章问题

1. `chord`、`tui` 与其他包的依赖关系有什么特殊之处？这说明了什么设计取向？
2. 为什么 `pi -p`、`pi --mode json`、交互模式可以共享同一套会话逻辑？这个共享点在哪个类？
3. "transcript 即真相"意味着运行中把 `read` 工具换成 `grep` 工具时，代码里发生了什么？（提示：不是修改配置）

下一章：把这套架构跑起来，完整走一遍一次请求的生命周期。
