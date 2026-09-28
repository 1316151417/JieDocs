# 第 2 章 一次请求的完整旅程

> 本章是全书的地图。我们用一个具体任务——**用户输入"读取 README.md 并总结这个项目"**——从终端按键开始，追到磁盘上的会话文件，把每一站的职责、输入输出、状态变化走一遍。细节在后续章节展开，这里只需要建立"整条链在脑子里能放电影"的能力。

## 2.1 全链路总览

先看整体。图中每一行右侧标注负责它的代码位置：

```
用户按键 "读取 README.md 并总结"
   │
   ▼
[1] Editor 组件收集输入，Enter 提交                tui/src/components/editor.ts
   │
   ▼
[2] InteractiveMode.onSubmit 处理特殊输入           coding-agent/src/modes/interactive/
    （斜杠命令 / !bash / 压缩期间排队 / steering）      interactive-mode.ts
   │  普通消息
   ▼
[3] 主循环 getUserInput() 交出文本                  同上（run() 的 while 循环）
   │
   ▼
[4] session.prompt(text) —— 应用层管线              coding-agent/src/core/agent-session.ts
    ├─ 扩展命令检查（/ 开头）
    ├─ 扩展 input 钩子（可改写/吞掉输入）
    ├─ skill / 模板展开
    ├─ 鉴权检查、预压缩检查
    ├─ before_agent_start 扩展钩子
    └─ system prompt / 工具集 diff 落位
   │
   ▼
[5] agent.prompt(messages) —— 内核启动运行           agent/src/agent.ts
    （把消息入队、runWithLifecycle、发 agent_start）
   │
   ▼
[6] agentLoop —— 循环体                             agent/src/agent-loop.ts
    │
    │  ┌──────────────── 一个 turn（回合）────────────────┐
    │  │ [6a] transformContext → convertToLlm：            │
    │  │      AgentMessage[] → LLM Message[]               │
    │  │ [6b] streamFn(model, context) ──────────────┐     │
    │  │      （ai 层：构建厂商请求、发 HTTP、          │
    │  │       把厂商 SSE 流翻译成统一事件流）          │
    │  │ [6c] 消费事件流：message_start/update/end     │
    │  │      assistant 消息入 transcript              │
    │  │ [6d] 解析 content 里的 toolCall 块             │
    │  │ [6e] 工具执行：preflight（校验/扩展拦截）       │
    │  │      → Promise.all 并发执行 → toolResult 消息   │
    │  │ [6f] turn_end                                 │
    │  └──────────────────────────────────────────────────┘
    │      ↑ 有工具调用（或 steering 到货）则回到 6a
    │      ↓ 无工具调用且队列空 → agent_end
   │
   ▼
[7] 每个事件沿途回传                                agent → AgentSession → UI
    ├─ AgentSession._handleAgentEvent：
    │    扩展钩子 → session 监听器 → 持久化（appendFileSync）
    └─ InteractiveMode.handleEvent：
         message_update → 流式 Markdown 渲染
         tool_execution_* → 工具组件 + diff 预览
   │
   ▼
[8] 落盘与收尾                                     coding-agent/src/core/session-manager.ts
    （每条 message_end 追加一行 JSONL；
     agent 结束后检查是否需要自动压缩 / 重试）
```

下面逐站展开。

## 2.2 第一站：界面层只做两件事

`packages/tui` 的 `Editor` 组件负责编辑和提交，它对业务一无所知。提交后进入 `InteractiveMode` 的 submit 处理链（`interactive-mode.ts` 的 `setupEditorSubmitHandler`），这里做的全是**分流**：

| 输入形态 | 去向 |
|---|---|
| `/xxx` 内置命令（`/model`、`/settings`…约 20 个） | 本地执行，不进模型 |
| `/扩展命令` | 交给扩展 handler |
| `!cmd` / `!!cmd` | 直接本地执行 bash（后者结果不进上下文） |
| agent 正在流式输出时 | `session.prompt(text, { streamingBehavior: "steer" })` 入 steering 队列 |
| 压缩进行中 | 本地队列暂存，压缩结束后重投 |
| 普通空闲消息 | 主循环 → `session.prompt(text)` |

**关键认识**：界面层的全部复杂性在于"输入分流"和"排队语义"，而不在执行。执行永远只有一条路：`session.prompt()`。

## 2.3 第二站：session.prompt() 的加工厂

`AgentSession.prompt()`（`agent-session.ts` 约 L1250 起）是应用层管线。对本例的普通文本消息，它会依次：

1. 检查是否是扩展命令（本例不是，跳过）；
2. 跑扩展 `input` 钩子（可 transform 或 handled）；
3. 展开 skill / prompt 模板（本例无）；
4. 检查模型与鉴权（`hasConfiguredAuth()`）；
5. 检查上一条 assistant 消息是否触发压缩阈值（本例是新会话，跳过）；
6. 组装 user 消息（文本 + 可选图片 + 排队的 custom 消息）；
7. 触发扩展 `before_agent_start` 钩子；
8. 用 `diffSystemPromptSections()` 对比"模型已见的 system prompt"和"当前应有的"，必要时生成一条**增量 system 消息**（本例首条，生成完整首条 system 消息）；
9. 调 `_runAgentPrompt()` → `agent.prompt(messages)`。

此时系统提示词里已经发生了三件重要的事（第 10 章展开）：

- AGENTS.md（如果存在）被读入，作为 `<project_instructions>` 节注入；
- 每个启用工具的名称 + 一句话说明进入 `<tools>` 节；
- 当前工作目录进入 `<cwd>` 节。

## 2.4 第三站：内核循环的两次模型请求

`Agent.prompt()` 只是入队并启动运行；真正干活的是 `agentLoop`（`agent/src/agent-loop.ts`）。本例会产生**两次**模型请求：

**第一次请求**：上下文 = [system（含工具声明）, user（"读取 README.md 并总结"）]。

`streamFn` 把它发给模型（DeepSeek/OpenAI/Anthropic 任一），流式返回。归一化事件流大约是：

```
start → text_start → text_delta("我先看一下 README") → text_end
      → toolcall_start → toolcall_delta(参数 JSON 增量) → toolcall_end
      → done(reason: "toolUse", message: 完整 AssistantMessage)
```

内核把最终 AssistantMessage 追加进 transcript，发现其 `content` 含一个 `toolCall`（name: `"read"`，arguments: `{path: "README.md"}`），于是进入工具执行。

**工具执行**（第 7 章展开）：

1. `tool_execution_start` 事件发出；
2. preflight：typebox 校验参数 → `beforeToolCall` 钩子（这里串到扩展的 `tool_call` 事件，本例没有扩展拦截）；
3. 调 `readTool.execute(toolCallId, {path: "README.md"}, signal, onUpdate)`——真正读文件的是这里，**不是模型**；
4. 返回 `{ content: [{type:"text", text: 文件内容(截断后)}], isError: false }`；
5. 生成 `toolResult` 消息（`toolCallId` 关联），追加进 transcript，发 `turn_end`。

**第二次请求**：因为本 turn 有工具调用且 steering 队列为空但存在工具结果，循环继续。此时上下文变成：

```
[system, user, assistant(toolCall: read), toolResult(README.md 内容)]
```

模型这次不再请求工具，输出总结文本，`stopReason: "stop"`。没有 toolCall → 内层循环条件不满足 → steering/followUp 队列都空 → `agent_end`。

**循环终止条件一览**（第 6 章详细讲）：

- 无工具调用且两条队列都空（正常结束）；
- `stopReason` 为 `error` / `aborted`（异常短路）；
- 工具批全部 `terminate: true`（主动终止）；
- `shouldStopAfterTurn` 钩子返回 true（优雅停，用于压缩前刹车）；
- 注意：**没有 maxTurns 上限**。

## 2.5 第四站：事件回传与持久化（与执行并发进行）

上面描述是"执行视角"；与之并发的还有一条**事件视角**。AgentSession 在构造时唯一一次订阅底层 Agent（`agent.subscribe(this._handleAgentEvent)`），此后每个事件按固定顺序流动：

```
agentLoop 发事件
  → Agent.processEvents：更新自身状态（messages/pendingToolCalls）→ 串行 await 每个 listener
  → AgentSession._handleAgentEvent：
      ① steering/followUp 镜像队列出队（message_start(user) 时）
      ② 先给扩展（emitMessageEnd 甚至可以替换消息内容，原地覆写）
      ③ 再给 session 监听器（UI 在这里渲染）
      ④ 最后持久化：appendMessage / appendCustomMessageEntry → appendFileSync 一行 JSONL
  → InteractiveMode.handleEvent：
      message_update → AssistantMessageComponent 更新 Markdown
      tool_execution_start → 建 ToolExecutionComponent
      message_end(assistant, content 含 toolCall) → edit 工具此刻就能算 diff 预览
      agent_end → 收尾、更新 footer 的 token 统计
```

顺序是刻意设计的：**扩展先于 UI、持久化最后**——保证扩展改写过的消息才是 UI 显示和磁盘存储的版本。这就是为什么说"UI 只是又一个订阅者"。

## 2.6 第五站：落盘之后

`agent_end` 之后 `AgentSession` 还有三件收尾（`_handlePostAgentRun`）：

1. **可重试错误？** 上一条 assistant `stopReason === "error"` 且重试开启 → 指数退避自动重试（`auto_retry_start/end` 事件）；
2. **需要压缩？** 上下文 token 超过 `contextWindow - reserveTokens` → 触发自动压缩（第 10 章）；
3. **队列有新消息？** agent 运行期间（扩展的 agent_end handler 里）又排了 followUp → `agent.continue()` 续跑。

最后，终端右下角的 footer 更新：累计 token（↑输入 ↓输出 R 缓存读 W 缓存写）、费用估算、上下文占用百分比。退出时 pi 打印 `pi --session <id>`，下次可以精确恢复。

## 2.7 用三个问题检验理解

**Q1：谁持有消息状态？**
transcript 持有，但有三份"视图"：`Agent.state.messages`（工作副本）、`SessionManager` 的 entry 树（持久层，带 parentId）、UI 的组件树（渲染层）。三者靠事件流保持一致，持久化在事件链最后写盘。

**Q2：谁真正执行工具？**
agent 内核的 `agentLoop`，在收到模型"想调用 read"的消息后，由本地代码执行。模型只产出"调用意图"（toolCall 块），执行、结果格式化、错误转 `isError` 全在程序侧。

**Q3：什么条件会再次请求模型？**
上一轮 assistant 消息含 toolCall（工具结果需要被模型看到），或 steering 队列非空（用户中途插话），或 followUp 队列非空（新任务）。三者都不满足时循环终止。

## 2.8 动手验证

不动手这条链还是抽象的。两个建议：

1. 打开 `packages/coding-agent/examples/sdk/01-minimal.ts`（30 行以内），对照本章找到 [4][5] 两站对应的 `session.prompt()`；
2. 在 `packages/agent/test/agent-loop.test.ts` 里找一个带 `toolCall` 的用例，看 faux 响应如何让循环跑两轮——这是第 13 章 faux provider 的预演。

## 2.9 本章问题

1. 用户在模型流式输出时又输入了一段话，这段话会经过哪些站？和空闲时输入有何不同？
2. 为什么"扩展改写消息"必须发生在"UI 渲染"和"持久化"之前？如果顺序反过来会出现什么不一致？
3. 本例中磁盘上的会话文件最终有几行 entry？分别是什么类型？（答案在第 9 章，但你现在应该能推理出来：header + user + assistant + toolResult + assistant。）

下一章往回走一步：这一切开始之前，`pi` 命令是如何启动的。
