# 第 5 章 AgentSession：应用编排层

> 本章回答：`session.prompt()` 从一段文本到内核运行之间到底发生了什么；运行中再输入（steering/followUp）的精确语义；事件如何在三层之间流动；运行结束后有哪些自动收尾。`agent-session.ts` 有 3600+ 行，本章给你一张按需进入的地图。

## 5.1 这个类管什么、不管什么

`AgentSession`（`coding-agent/src/core/agent-session.ts`，文件头注释自我定位为 modes 之下的业务核心）的职责边界：

**管**：prompt 管线（命令/模板/钩子）、steering 与 followUp 的应用层记账、system prompt 组装与差分、工具注册表与允许名单、自动压缩与自动重试、事件翻译与广播、模型/thinking 档位变更、会话树导航（navigateTree）、bash 直执行（`!` 命令）、自定义消息注入。

**不管**：循环本体与工具执行（那是 `Agent`/`agentLoop` 的）、模型 HTTP（那是 ai 层的）、任何渲染（那是 modes 的）、会话文件切换（那是 runtime 的）。

## 5.2 prompt() 管线逐步

`prompt(text, options)`（约 L1250 起）。按执行顺序：

```
输入 text
 │
 1├─ 以 "/" 开头？→ _tryExecuteExtensionCommand：
 │     解析 命令名+args，ExtensionRunner.getCommand() 查到即执行并返回
 │     （流式中也立即执行；找不到则继续，可能是模板/skill）
 │
 2├─ 手动压缩进行中？→ 抛错（互斥）
 │
 3├─ 扩展 input 钩子（_runInputHandlers）：
 │     handler 返回 {action:"handled"} → 吞掉输入，prompt 结束
 │     返回 {action:"transform"} → 链式替换 text/images
 │     ★ 此钩子在模板展开之前
 │
 4├─ skill / 模板展开：
 │     /skill:name args → <skill name=... location=...>SKILL.md 正文</skill> 块
 │     自定义模板：$1..$n、$@、$ARGUMENTS 位置参数替换
 │
 5├─ 正在流式输出？→ 必须带 streamingBehavior，否则抛错：
 │     "followUp" → _queueFollowUp：推镜像队列 + agent.followUp(msg)
 │     "steer"    → _queueSteer：  推镜像队列 + agent.steer(msg)
 │     然后返回（本轮 prompt 到此为止，消息已入队）
 │
 6├─ 冲刷挂起消息（pending bash / custom 消息）
 │
 7├─ 鉴权 preflight：无模型 / 无鉴权 → 抛带修复指引的错误
 │
 8├─ 预压缩检查：上一条 assistant 存在 → _checkCompaction(只压不续)
 │
 9├─ 组装 messages：user 消息(text+images) + pendingNextTurnMessages
 │     （sendCustomMessage(deliverAs:"nextTurn") 排队的上下文消息）
 │
10├─ 扩展 before_agent_start 钩子：
 │     handler 可返回 {message}（转 custom 消息随本轮注入）
 │                或 {systemPrompt}（本轮强制提示词）
 │     之后融合工具选择（handler 改过 selectedTools 则用之）
 │
11├─ _preparePromptAndToolLoadout：
 │     diffSystemPromptSections() 对比"模型已见"与"当前应有"，
 │     生成一条增量 system 消息 unshift 到队首
 │     （forceSystemPrompt 则走请求期投影，不污染 transcript）
 │
12└─ _runAgentPrompt(messages)：
      _isAgentRunActive = true
      await agent.prompt(messages)          ← 进入第 6 章的内核
      while (await _handlePostAgentRun())    // 返回 true 则 agent.continue()
      finally：清本轮配置、冲刷挂起消息、_emitAgentSettled()
```

第 11 步是第 1 章"transcript 即真相"主线的落地处：改工具/改技能不打断对话、不发全量新提示词，只发**按节名的补丁消息**。第 10 章会把 system prompt 的分节结构讲全。

## 5.3 steering / followUp：双队列的精确语义

这是 pi 交互手感的核心，值得花一节讲透。

### 两条队列，两个注入时机

在 `agent` 内核里（第 6 章），`PendingMessageQueue` 有 steering 和 followUp 两条（各自的 QueueMode 可配置为 `"all"` 或 `"one-at-a-time"`）：

```
agent 运行中，时间线：
  turn 1: assistant 回答 + 工具批 A
  ───────────────────────────────
  ← steering 在这里注入：工具批 A 结束后、下一轮 LLM 调用前，
     作为 user 消息插入。模型带着新指令继续当前任务。
  ───────────────────────────────
  turn 2: assistant 继续 + 工具批 B
  ───────────────────────────────
  …
  agent_end（任务结束）
  ───────────────────────────────
  ← followUp 在这里投递：agent 完全停止后才作为新一轮 prompt。
     等价于"排下一个任务"。
```

### 应用层的镜像队列

`AgentSession` 自己还维护 `_steeringMessages` / `_followUpMessages` 两个数组，**仅用于 UI 展示**。同步机制朴素但有效：`_handleAgentEvent` 看到 `message_start` 且 role=user 时，按文本匹配从镜像数组移除并发 `queue_update` 事件。UI 的 pending 区就靠它显示"待发送队列"，Esc 键还能把整队消息**恢复回编辑器**重新编辑（interactive-mode 的 `restoreQueuedMessagesToEditor`）。

### 压缩期间的第三条队列

压缩进行中（`isCompacting`）连 steer 都进不去，交互模式维护本地 `compactionQueuedMessages` 暂存，压缩结束后按原语义（steer/followUp）重投。这体现出分层的价值：内核不必知道压缩，应用层用本地队列补齐语义。

### 公开 API 与内部约束

`session.steer(text)` / `session.followUp(text)` 走与 prompt 相同的 input 钩子和模板展开，但**禁止排队扩展命令**（命令必须立即执行，排队执行没有意义）。`agent` 层的 `prompt()` 在运行中会直接抛错并提示改用 steer/followUp——错误消息即 API 文档。

## 5.4 事件转发：单一订阅点与固定顺序

AgentSession 构造函数里**唯一一次**订阅底层 Agent：

```ts
this.agent.subscribe(this._handleAgentEvent);
// 注释：Always subscribe to agent events for internal handling
// (session persistence, extensions, auto-compaction, retry logic)
```

`_handleAgentEvent`（约 L659 起）对每个事件按四步走，**顺序是本章最重要的知识点**：

```
① steering/followUp 镜像队列出队（仅 message_start 且 user）
② 先给扩展：把 AgentEvent 逐类翻译成扩展事件并 emit
     ★ message_end 特殊：扩展可以返回"替换消息"，
       经 _replaceMessageInPlace() 原地覆写——保证 agent state、
       后续事件、监听器、持久化四者看到同一个对象
③ 再给 session 监听器：this._emit(event)
     ★ agent_end 被改写为带 willRetry 标记（供 UI 决定是否显示"重试中"）
④ 最后持久化：message_end → sessionManager.appendMessage 一行 JSONL
     turn_end → 冲刷 pending custom 消息
     （turn_end 是"assistant+工具结果都已入树"的第一个安全插入点，
       避免自定义消息卡在 toolCall 与 toolResult 之间被 provider 拒绝重放）
```

为什么是这个顺序：**扩展可能改写消息，UI 和磁盘必须拿到改写后的版本**；持久化放最后，保证写盘的就是最终态。

### AgentSessionEvent：应用层新增的事件

在内核 9 种 AgentEvent 之外，session 层新增：`agent_settled`、`queue_update`、`compaction_start/end`、`entry_appended`、`session_info_changed`、`thinking_level_changed`、`auto_retry_start/end`、`bash_execution_update` 等。UI 订阅的就是这一层（`session.subscribe`），对内核事件无感知。

`agent_settled` 与 `agent_end` 的区别值得记：`agent_end` 是内核循环结束的事件；`agent_settled` 还要等所有 listener（含扩展）结算完，`waitForIdle()` 基于它实现。

## 5.5 运行后处理：_handlePostAgentRun

`agent.prompt()` 返回后并不代表完事，`_handlePostAgentRun()` 循环检查三件事：

1. **可重试错误**：最后一条 assistant `stopReason === "error"` 且 retry 设置开启 → `_prepareRetry()` 指数退避（`baseDelayMs * 2^n`，上限 maxRetries=3 默认），发 `auto_retry_start/end`，失败消息从上下文移除后重试；
2. **需要压缩**：`_checkCompaction()` 判定溢出或超阈值 → 可能压缩后 continue（详见第 10 章）；
3. **队列新增**：agent 运行期间（扩展的 agent_end handler 里）又排了 followUp → `agent.continue()` 续跑。

返回 true 就继续循环。这把"重试/压缩/续跑"三种续命场景统一成一个后处理循环，避免了它们散落在事件回调里。

### 每回合刷新：prepareNextTurn 钩子

除了 run 结束后的检查，还有**回合粒度**的前置刷新：`_installAgentNextTurnRefresh()` 接管内核的 `prepareNextTurnWithContext` 钩子，每次向 LLM 发请求前：① 命中压缩阈值则先压缩再发；② 重建 system prompt options 并做差分。保证"模型看到的 system prompt 与 `session.systemPrompt` getter 一致"——把一致性检查点放在每次请求前，而不是每次配置变更后。

## 5.6 其余高频成员速查

| 成员 | 作用 |
|---|---|
| `abort()` | abortRetry + abortCompaction + abortBranchSummary + agent.abort() + waitForIdle() |
| `setModel()` / `cycleModel()` | 换模型（先 checkAuth 校验）、Ctrl+P 循环切换；每次变更落 `model_change` entry + 发 `model_select` 扩展事件 |
| `setThinkingLevel()` | 钳制到模型能力、变更才落盘 |
| `compact()` | 手动 `/compact`（第 10 章） |
| `navigateTree()` | 会话树导航（第 9 章） |
| `executeBash()` | `!` 命令直执行（走扩展 `user_bash` 钩子后本地 spawn） |
| `sendCustomMessage()` | 扩展/宿主向对话注入消息，`deliverAs` 可选立即/下一回合 |
| `setActiveTools()` / `getActiveToolNames()` | 运行时改工具集（与 settings UI、`ctx.setActiveTools` 共用路径） |
| `getContextUsage()` | 上下文占用估算（第 10 章 10.4） |
| `getSessionStats()` | 遍历全部 entry（含被压缩历史）的累计 token/费用 |

## 5.7 本章问题

1. 为什么扩展的 `message_end` 改写必须"原地覆写"同一个对象，而不是返回新对象替换？（提示：四处的引用一致性）
2. steering 消息从用户按下回车到被模型看见，中间最长会间隔多少个阶段？分别在哪个队列里等待？
3. `_handlePostAgentRun` 返回布尔而不是递归调用自己，这个形状有什么好处？（对照：把三件事写成三个事件回调的方案）

下一章：`agent.prompt()` 之后的内核世界。
