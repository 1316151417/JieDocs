# 第 6 章 agent 包：执行内核

> 本章回答：`agentLoop` 这个 200 行级别的函数如何撑起整个产品；`Agent` 类在循环之上加了什么；事件系统的精确顺序；错误为什么不抛异常。这是全书最"本质"的一章——读懂它，其他 agent 框架的循环你也能一眼看穿。
>
> 主要文件：`packages/agent/src/agent-loop.ts`（857 行）、`agent.ts`（607 行）、`types.ts`（463 行）。`packages/agent/README.md` 的 Message Flow / Event Flow 两节是权威规格说明，值得配合阅读。

## 6.1 三层 API：同一个循环的三种消费方式

这个包对外提供同一循环的三个层次，先分清再往下读：

| 层 | 形态 | 特点 | 谁用 |
|---|---|---|---|
| `agentLoop(prompts, context, config, signal)` | 返回 `EventStream<AgentEvent, AgentMessage[]>`（async iterable） | **观察性**：事件只 push 进流，不等消费者 | 一次性脚本、调试 |
| `runAgentLoop(...)` + `emit` 回调 | `await emit(event)` | **消费者可反压生产者**：emit 是 await 的，消费者没处理完，循环不走下一步 | `Agent` 类 |
| `Agent` 类 | 有状态封装 | 持有 transcript、串行通知订阅者、steering/followUp 队列、运行生命周期 | AgentSession |

`EventStream`（`ai/src/utils/event-stream.ts`）本身是个教科书级手写 async iterable：FIFO 队列 + 等待者队列 + finalResultPromise。而 `Agent` 选择回调层的原因只有一个：**它需要把 `await listener(event)` 变成屏障**（下文 6.3）。

## 6.2 Agent 类：状态、队列、生命周期

`Agent` 的字段一览（`agent.ts` 约 L189 起）：

- `_state: MutableAgentState`：messages、tools、isStreaming、streamingMessage、pendingToolCalls、errorMessage。注意 `systemPrompt` 是 **getter**——从 transcript 的 system 消息回放得到，不是独立字段（"transcript 即真相"在内核层的体现）；
- `listeners: Set`：订阅者，**按注册顺序串行 await**；
- `steeringQueue / followUpQueue`：两条 `PendingMessageQueue`，各有 QueueMode（all / one-at-a-time）；
- `convertToLlm`：AgentMessage[] → LLM Message[] 的唯一翻译边界；
- `transformContext`：每次请求前可改写上下文；
- `streamFunction: StreamFn`：模型调用抽象（第 8 章）；
- 钩子：`beforeToolCall / afterToolCall / shouldStopAfterTurn / prepareNextTurn(WithContext)`，运行中可热替换；
- `activeRun`：当前运行的 promise + AbortController。

关键方法行为：

- `prompt(input)`：接受 string / 单条消息 / 消息数组；**运行中调用直接抛错**（提示改 steer/followUp）；
- `steer(msg)` / `followUp(msg)`：只入队不触发；
- `continue()`：从当前 transcript 续跑。最后一条是 assistant 时先 drain steering、再 drain followUp，都空则抛错；
- `abort()`：中止当前 run（没有 `interrupt()` 这个名字，中断就是 abort）；
- `waitForIdle()`：resolve 于 agent_end 的全部 listener 结算之后；
- `reset()`：保留"回放后的 system 基线"，清空其余。

`processEvents(event)` 是 Agent 传给循环的 emit 回调，它做两件事：**先归约状态**（message_end 时 push 进 state.messages；tool_execution_start/end 增删 pendingToolCalls），**再串行 await 每个 listener**。这就是"message_end 是工具 preflight 前的 barrier"的实现——保证扩展在工具开跑前已经看到完整消息（持久化也已发生）。

## 6.3 agentLoop 主流程

`runAgentLoop` → `runLoop`（`agent-loop.ts` 约 L162 起）。以下为带注释的骨架：

```
declareToolChanges():
   对比 context.tools 与 transcript 已声明的工具，
   有差异则在 prompt 前插入/合并一条带 toolsAdded/toolsRemoved 的 system 消息
   （模型由此知道工具集变化；也是 transcript 即真相的又一处体现）

agent_start → turn_start → 为每条 prompt 消息发 message_start/end

pendingMessages = await getSteeringMessages()   // 开头先捡 steering

while (true) {                                  // 外层：为 followUp 续命
  while (hasMoreToolCalls || pendingMessages.length > 0) {   // 内层：工具循环

    if (非首轮) {
      prepareNextTurn(lastCompletedTurn)        // 每轮前钩子：可换 model/上下文/档位
      若之前没捡到 steering，再 poll 一次        // 避免一轮塞两条（one-at-a-time 语义）
    }
    turn_start
    注入 prepared + pending 消息（start/end 事件，push 进上下文）

    ── 调用模型 ──
    transformContext(messages)                  // 可选改写（AgentMessage 域）
    convertToLlm(messages)                      // 必须（LLM Message 域）
    streamFunction(model, transcriptContext)    // 见第 8 章
    消费事件流：
      start   → partial 入上下文，发 message_start
      9 种 delta → 替换末位 partial，发 message_update
      done|error → response.result() 取最终 AssistantMessage，
                   替换末位，发 message_end

    if (stopReason 是 "error" | "aborted") {
      turn_end(空 toolResults) → agent_end → return    // 异常短路
    }

    toolCalls = assistant.content 里 type==="toolCall" 的块
    if (toolCalls.length > 0) {
      if (stopReason === "length") {
        // 输出被 maxTokens 截断：整批工具调用判为不可信，不执行。
        // （流式 JSON salvage 可能拼出"合法但不完整"的参数）
        每个 toolCall → 错误工具结果（提示模型重发）
      } else {
        executeToolCalls:                          // 见 6.4
          config.toolExecution === "sequential"
            或任一目标工具 executionMode==="sequential" → 整批顺序
          否则 → 并行
      }
      hasMoreToolCalls = !batch.terminate          // 全部结果 terminate 才提前停
      toolResult 消息按源顺序入上下文，发 start/end
    }

    turn_end { message, toolResults }

    if (await shouldStopAfterTurn()) { agent_end; return }  // 优雅停（压缩前刹车）

    pendingMessages = await getSteeringMessages()  // 回合间隙再捡 steering
  }                                                // 无工具调用且无 steering → 出内层

  followUps = await getFollowUpMessages()
  if (followUps 非空) { pendingMessages = followUps; continue 外层 }
  break
}
agent_end { messages: 本次 run 新增的全部消息 }
```

**终止条件汇总**（刻意没有 maxTurns）：

1. 无工具调用且两条队列空；
2. `stopReason === "error" | "aborted"` 短路；
3. 工具批全部 `terminate: true`；
4. `shouldStopAfterTurn` 返回 true。

`skipInitialSteeringPoll` 是个精致的并发细节：`continue()` 自己先 drain 了 steering 再进循环，循环开头的 poll 必须跳过，否则同一消息被消费两次——用闭包标志位解决。

## 6.4 工具执行：顺序 preflight，并行执行，两种顺序解耦

这是本包最微妙的部分。并行模式（默认）的执行分三段：

```
第一段：preflight 逐个顺序进行
  对每个 toolCall：
    tool_execution_start
    prepareToolCall:
      查工具（不存在 → "Tool X not found" 错误结果）
      prepareArguments（兼容 shim，第 7 章的 edit 用到）
      validateToolArguments（typebox 校验，失败转错误结果）
      beforeToolCall 钩子（{block:true} → 拦截，就地生成错误结果）
      signal.aborted 检查（多处）
    immediate 场景（找不到/校验失败/被拦截）→ 就地 finalize

第二段：执行体收集为 thunk 数组，Promise.all 并发跑
  executePreparedToolCall:
    tool.execute(toolCallId, params, signal, onUpdate)
    onUpdate → tool_execution_update 事件（流式进度，如 bash 输出）
    ★ 异常被 catch，转成 isError:true 的错误结果——不向上抛

第三段：收尾顺序与源顺序对齐
  tool_execution_end 按完成顺序即时发出（Promise.all 内）
  但 toolResult 消息事件与 turn_end.toolResults 按 assistant 里的原始顺序补发
```

**两条顺序解耦**（完成序 vs 源序）是事件模型的关键不变量：UI 里工具完成有先有后（真实感），但 transcript 里结果永远与调用对齐（重放正确性）。

`finalizeExecutedToolCall` 里的 `afterToolCall` 钩子做**字段级覆盖**（content/details/usage/isError/terminate，无深合并），钩子自身异常也转错误结果。

`terminate` 语义：仅当批内**全部** finalize 的结果都 terminate 才提前停——单工具说"停"不算数。

## 6.5 事件系统：9 种变体与一轮完整序列

```
agent_start
turn_start
message_start / message_end        （user/assistant/toolResult/system 都发）
message_update                     （仅 assistant 流式期间，携带原生事件）
tool_execution_start
tool_execution_update
tool_execution_end
turn_end { message, toolResults }
agent_end { messages: 本次新增 }
```

一轮带工具调用的完整序列（与 README 的 Event Flow 逐条对应）：

```
agent_start
  turn_start
    message_start/end (user prompt)
    message_start (assistant) → message_update × N → message_end
    tool_execution_start → [tool_execution_update × N] → tool_execution_end
    message_start/end (toolResult)            ← 每个工具一份，按源顺序
  turn_end { message, toolResults }
  （下一轮 turn_start …）
agent_end { messages }
```

两个易错点：

- 并行模式下 `tool_execution_end` 按完成序、toolResult 消息按源序，两者交错是正常的；
- `agent_end` 是最后一个**事件**，但 idle 要等被 await 的 agent_end listener 全部结算（`waitForIdle` 的语义）。

## 6.6 错误哲学：错误是数据，不是异常

三个层次各有约定，串成一条"UI 永远看到闭合生命周期"的链：

1. **模型层（StreamFn 契约）**：`streamFn` **不抛异常**。请求失败编码为流里的 `error` 事件 + 带 `stopReason: "error" | "aborted"`、附 partial 内容的 AssistantMessage（第 8 章）。
2. **工具层**：`tool.execute` 失败靠 **throw**；内核 catch 后转 `isError: true` 的工具结果——模型能看到错误并自行调整（重试、换路径、道歉）。
3. **循环层**：`Agent.handleRunFailure` 兜底——循环本身抛异常时，合成一条 `stopReason: "aborted" | "error"` 的 assistant 消息，手动补发 `message_start → message_end → turn_end → agent_end`，保证订阅者收到完整闭合的事件序列。

另一个实战细节是 `stopReason === "length"` 的防御：输出被 token 上限截断时，流式 JSON 解析可能"拼出"语法合法但内容不完整的工具参数。pi 的选择是整批不执行、全部标记失败让模型重发——宁可多一轮，不执行半截命令。

## 6.7 消息模型速览

类型定义大多在 `ai/src/types.ts`（第 8 章详讲），此处只列内核视角的要点：

- `Message = SystemMessage | UserMessage | AssistantMessage | ToolResultMessage`；
- SystemMessage 可携带 `sections`（命名段落，null 为删除）、`toolsAdded/toolsRemoved`——它是"配置变更"的载体；
- AssistantMessage 的 `content` 是 `(TextContent | ThinkingContent | ToolCall)[]` 数组，thinking 与文本、多工具调用可交错；`stopReason` 七种；`usage` 挂在这条消息上；
- `AgentMessage = Message | 自定义消息`：通过 **declaration merging** 向空接口 `CustomAgentMessages` 注入新 role（coding-agent 注入了 bashExecution/custom/branchSummary/compactionSummary 四种），`convertToLlm` 是它们进入 LLM 请求的唯一通道（通常翻译为 user 消息或被过滤）；
- `Tool` 接口：`name / description / parameters(typebox schema) / execute / label(UI) / prepareArguments(兼容 shim) / executionMode(per-tool 顺序覆盖)`。**没有 render 字段**——渲染靠 details + 事件流（第 7 章）。

## 6.8 值得带走的三个设计

1. **双层循环 + 双队列**：外层为 followUp 续命、内层为工具调用续命，steering 在回合间隙注入——"用户随时插话"不是事后补丁，而是循环结构里的一等公民。
2. **emit 可 await**：回调式 API 平时不如生成器优雅，但 `await emit()` 天然给了消费者反压与屏障能力（Agent 的 message_end barrier、AgentSession 的扩展改写都依赖它）。选择回调层作为有状态封装的底座，是这个包最好的决定。
3. **transcript 即配置**：system prompt 与工具声明全部由消息链回放，变更即追加消息。它让 resume/分支/压缩共用同一套重放逻辑，代价是必须发明 diff 补丁——一个约束换来三类功能的一致性。

## 6.9 本章问题

1. 如果给你 `agentLoop` 的生成器版本写一个最小消费者（for await 打印事件），它和 `Agent` 类的行为差异在哪个具体场景暴露？（提示：工具 preflight 时机）
2. steering 的 QueueMode 是 one-at-a-time 时，用户连发两条插话，第二条什么时候被模型看到？把 6.3 的骨架当伪代码走一遍。
3. `stopReason === "length"` 时不执行工具而是全部报错，权衡了什么？如果改成"尽力执行已完整的参数"，要额外保证什么？

下一章：镜头推近到 `tool.execute` 内部——8 个内置工具的实现。
