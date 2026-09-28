# Coding Agent 架构串讲：把 Node 知识连成一张网（终章）

> 前面十六章把 TS 类型、事件循环、fs、stream、child_process 一块块拆开讲。本章把它们装回一台完整的机器：从你按下回车，到 token 逐个上屏，到 bash 子进程跑测试，到 Ctrl+C 优雅停下——每一环都落在前面某章讲过的能力上。读完本章，你应该能拿着这张分层图直接走进任何一个开源 Coding Agent 的源码目录，十分钟内定位到 agent loop。

## 16.1 总架构图【必须掌握】

```text
CLI（stdin/stdout、参数、信号）           ← 15-cli
 ↓
Session（会话状态、消息历史）              ← TS 类型（01）
 ↓
Agent Loop（while 循环：LLM ↔ 工具）      ← 04 async
 ↓
LLM Client（SSE 流式响应）                ← 07 stream / 08 buffer
 ↓
Tool Call 分发
 ├── read   → fs.readFile                 ← 05
 ├── write  → fs.writeFile                ← 05
 ├── bash   → child_process.spawn         ← 09
 └── browser→ 子进程/协议客户端
 ↓
Event（tool_call / tool_result / message）← 06 EventEmitter
 ↓
Stream / async iterator（事件流）         ← 07
 ↓
TUI（终端渲染、按键处理）                  ← 15
packages 组织：npm workspaces monorepo    ← 12
```

纵向是数据流：一次用户输入自上而下走一遍，图上每一行对应一段代码。横向的标注（← 05 等）是这一层主要消耗的知识出处（指本套教材对应章节文件）。分层不是为了好看——层与层之间只通过"事件"或"await 返回值"衔接，所以任何一层都能单独替换：换 TUI 不动 loop，换模型客户端不动工具，headless 模式直接砍掉最下面两层。最后一行的 monorepo 不是一层，而是这套分层的物理载体：每层一个 package。

## 16.2 逐层走读：每层用什么能力、为什么选它

### 16.2.1 CLI 层：stdin raw mode + stdout 流式渲染（见 15-cli.md）

```ts
if (process.stdin.isTTY) process.stdin.setRawMode(true);     // 按键级输入，绕过行缓冲
process.stdin.on("data", (buf: Buffer) => keys.handle(buf)); // 06：标准流是 EventEmitter
process.stdout.write(delta);                                 // 07：增量渲染 = 往流里 write
```

- 用什么：`process.argv` 解析命令行参数、`process.env` 读 API key、`process.on("SIGINT")` 接信号、`stdin.setRawMode(true)` + `stdout.write`。
- 为什么选它：终端是字符设备，Node 的标准流天然是 Stream + EventEmitter 的合体。raw mode 让每次按键不等回车就到达进程，这是 TUI 能做"输入框、焦点、快捷键"的前提；渲染侧不需要图形库，逐段 `write` 转义序列就是全部。
- 关键陷阱：raw mode 下 Ctrl+C 不再自动产生 SIGINT（终端行规程被关掉了），字节 `\x03` 变成普通 data 事件，TUI 必须自己识别并决定是"打断 agent"还是"取消输入"。

### 16.2.2 Session 层：TS 类型就是会话状态文档（见 01-typescript-essential.md）

```ts
type Message =
  | { role: "user"; content: string }
  | { role: "assistant"; content: string; toolCalls: ToolCall[] }
  | { role: "tool"; toolCallId: string; content: string };
```

这一层没有任何运行时代码——它就是一个 `messages: Message[]` 数组加配套类型。但读源码时它最重要：判别 union（`role` 字段）+ switch 收窄，就是整个会话状态机的文档。记住 01 章的结论：运行时类型全部擦除，这些标注只帮你和编译器，不约束线上数据（所以边界处常配 zod，见 01）。

Session 还有第二个职责：持久化与恢复。"关掉终端明天继续"的功能，实现通常就是 JSONL 追加写——每条消息一行，天然可增量、可 tail、坏一行不毁全文件：

```ts
await appendFile(sessionFile, JSON.stringify(msg) + "\n");   // 05：fs/promises 追加写
// 恢复 = 逐行 JSON.parse + zod 校验（01），重建 messages 数组
```

这个落盘点就是 16.6 对照表里 LangGraph checkpointer 的手写对应物：没有框架托管，时机（每轮结束？每个事件？）由 loop 自己决定。

### 16.2.3 Agent Loop 层：一个 while 循环（见 04-async-programming.md）

循环体做三件事：把 `messages` 发给模型 → 若响应含 `toolCalls` 就执行并把结果 push 回 `messages` → 没有工具调用则返回。整个"编排引擎"就是一个 `while (true)`，靠 `await` 驱动（代码在 16.4）。用 LangGraph 的话说：你省掉了 graph executor，因为图退化成了一个自环——所有节点合并回一个循环体，`State` 就是 `messages`。为什么敢手写：循环本身不足 40 行；框架换来的 checkpoint、并行节点、human-in-the-loop 中断，在 CLI agent 场景要么不需要，要么一个 session 文件 + AbortController 就覆盖了（对照表见 16.6）。

### 16.2.4 LLM Client 层：async iterator 消费 SSE（见 07-stream.md、08-buffer-binary.md）

```ts
const res = await fetch(url, { signal, headers });      // undici：Node 内置 fetch
for await (const chunk of res.body!) {                  // Web ReadableStream，异步可迭代
  buffer += decoder.decode(chunk, { stream: true });    // 08：chunk 边界 ≠ 事件边界
  for (const ev of sseSplit(buffer)) yield ev;          // 按 SSE 协议切出完整事件
}
```

三个要点，每个都对应前面一章：

- `response.body` 是流：token 生成一个传一个，不必等全文（07 的核心价值：两端速率解耦）。
- chunk ≠ 消息：TCP 分段与 SSE 事件边界无关，一个 `data:` 事件可能劈在两个 chunk 里，必须自己 buffer 累积、按协议（空行分隔）切分（08）。streaming 模式的 UTF-8 多字节字符也可能被劈开，所以 `decode` 要带 `{ stream: true }`。
- 对上层暴露统一形态：client 把"HTTP + SSE 解析"包成 async iterator，agent loop 只 `for await`，不关心底下是 SSE、WebSocket 还是本地 mock（04 定义协议，07 提供落地）。
- 07 章的提醒在这里生效：Node 侧另有一套 `node:stream`，与 fetch 返回的 Web ReadableStream 接口不同，靠 `Readable.fromWeb()` 互转——client 源码里出现这个调用，就是在做两套流的桥接。

### 16.2.5 Tool 层：read/write 走 fs，bash 走 spawn（见 05、09）

```ts
// read/write 工具：fs/promises + path（05）
const abs = path.resolve(root, relPath);            // 相对路径 → 绝对路径，统一分隔符
const content = await readFile(abs, "utf8");        // Promise 风格，天然 async
await writeFile(abs, newContent, "utf8");

// bash 工具：spawn 流式收集 + 超时 + AbortSignal（09）
const timeout = AbortSignal.timeout(30_000);        // 04：到点自动 abort
const child = spawn(cmd, args, { cwd, signal: AbortSignal.any([userSignal, timeout]) });
let out = "";
child.stdout.on("data", (c: Buffer) => { out += c; emitter.emit("tool_output", c); }); // 实时上屏
```

为什么 read 不用流：文件内容要整体进 prompt，`readFile` 一步到位；为什么 bash 必须流式：命令输出可能无穷（`npm run dev`），且子进程 stdout 管道缓冲区有限，不持续读会把子进程写端堵死（09 的经典卡死场景）。取消与超时全部走 `AbortSignal`：传给 `spawn` 的 `signal` 会在 abort 时自动 kill 子进程；`AbortSignal.any` 把"用户取消"和"超时"两路信号并联——这是 04 章 AbortController 知识的标准应用姿势。

### 16.2.6 事件层：两种风格，各有取舍（见 06-events.md）

风格 A——同步 emitter 直连：

```ts
agent.events.emit("message", delta);    // TUI 的渲染函数在当前调用栈里立即执行
```

风格 B——异步事件队列 / async generator：

```ts
async function* run(prompt: string, signal: AbortSignal) {
  /* ... */ yield { type: "message", delta };      // 事件入队，消费者自己取节奏
}
for await (const ev of agent.run(prompt, signal)) tui.handle(ev);
```

| | A：emitter 直连 | B：事件队列 / async generator |
|---|---|---|
| 实现成本 | 低，一个 EventEmitter | 略高，要维护队列或生成器 |
| 消费者 | 多订阅者各挂 `on`，增删自由 | 天然单消费者，多消费者要自己广播 |
| 执行时机 | emit 即同步执行，慢渲染直接阻塞 loop | 排队消费，loop 与 UI 节奏解耦 |
| 跨进程 | 不行（进程内函数调用） | 队列可序列化走 IPC |
| 类型 | 要手写"接口 + 重载"补类型 | `yield` 的类型就是事件类型，TS 自动推导 |

一句话取舍：进程内、UI 轻量，用 A（真实项目的主流）；要跨进程、要事件回放、要严格控制消费顺序，用 B。两者常混用：对进程内订阅者（日志、遥测）用 emitter，对 TUI 或外部进程用事件队列。无论哪种，本质都是 06 章那句话：这是函数调用级别的分发，不是消息中间件。

### 16.2.7 事件流消费层：Stream / async iterator（见 07-stream.md）

事件产出后怎么到 UI，标准形态就是 `for await`。TUI 侧拿到 delta 后 `stdout.write`，渲染远快于 LLM 生成，通常没有背压问题；但输出到慢终端（ssh 到高延迟会话）时 `write` 会返回 false，此时需要暂停消费或丢弃中间帧——真实项目里常见"节流渲染"：delta 先攒进缓冲，定时器每 30ms 刷一次屏，这就是 07 章流的速率协调在 UI 层的翻版。

### 16.2.8 TUI 层：状态机 + 转义序列（见 15-cli.md）

渲染 = 组件状态机 + `stdout.write`（清屏、移动光标、重画差异部分）；输入 = raw mode 下逐字节解析转义序列（方向键、Ctrl 组合键）。看源码时把它当黑盒：只关心它订阅哪些事件、暴露哪些方法（`appendStream`、`pushLine`、`showError`），不先抠渲染细节。

### 16.2.9 packages 分层：依赖只能向下（见 12-monorepo-workspace.md）

```text
packages/ai                        packages/tui
模型客户端：fetch + SSE 解析        渲染组件：不知道 agent 存在，
+ 消息类型（无 UI、无 fs 依赖）    只被 coding-agent 依赖
    ↑                                 ↑
packages/agent                      │
agent loop + tools：依赖 ai，       │
只产出事件（不认识终端）            │
    ↑                                 │
    └───── packages/coding-agent ─────┘
        CLI 入口 + 装配：依赖 agent 与 tui，订阅事件驱动渲染
```

箭头是 import 方向：`agent` 不 import `tui`，所以它能在单测、headless 脚本、HTTP 服务里复用——这正是 16.2.6 事件解耦在包结构上的投影。workspaces 让四个包共享根 node_modules，互相引用走 package name 而不是相对路径（12 章）。读源码时先确认这个方向没有被违反（比如 agent 里出现 `import ... from "../tui"` 就是坏味道）。

### 16.2.10 一页映射总表

把 16.2.1~16.2.9 收成一张表，读真实项目时当索引用：

| 层 | 用的能力 | 出处 | 为什么是它 |
|---|---|---|---|
| CLI | argv / env / 信号 / stdin raw mode | 15 | 终端是字节流设备，标准流天然 Stream + EventEmitter |
| Session | 判别 union 类型 + JSONL 落盘 | 01 / 05 | 类型即状态机文档；追加写可增量恢复 |
| Agent Loop | while + await | 04 | 单线程串行推进，控制流就是普通代码 |
| LLM Client | fetch + Web Stream + for await | 07 / 08 | token 逐步到达；chunk 与事件边界分离靠 buffer 累积 |
| read/write | fs/promises + path | 05 | 整文件进 prompt，不需要流 |
| bash | spawn + AbortSignal + 超时 | 09 | 输出可能无穷，管道必须持续读否则堵死子进程 |
| 事件 | EventEmitter / async generator | 06 / 07 | loop 与 UI 解耦的两种风格，可混用 |
| 事件流消费 | for await + 节流渲染 | 07 | 渲染与生成的速率协调 |
| TUI | stdout.write + 按键解析 | 15 | 渲染即写字节，输入即逐字节读 |
| packages | workspaces 向下分层 | 12 | agent 不认识终端，才可被 headless/测试复用 |

## 16.3 请求生命周期 trace【必须掌握】

场景：用户输入"修复这个 bug"，模型决定先跑 `npm test`，看到失败后改文件，再跑一次通过，输出总结。中途假设用户在测试运行时按下 Ctrl+C。逐步标注 Node 能力：

1. **按键到提交**。raw mode 下每次按键触发一次 `stdin` 的 `data` 事件（06），TUI 逐字节解析、拼出输入行；回车字节触发 submit 回调（15）。
2. **启动 agent**。CLI 层把 prompt 追加进 `session.messages`，`new AbortController()` 创建取消通道，调 `agent.run(messages, controller.signal)`（04）。
3. **进入循环第一轮**。agent loop 的 `while` 迭代开始：把整个 `messages` 交给 LLM client（04 async）。
4. **发请求**。client 用 fetch 发 HTTP，`signal` 传入请求；`response.body` 是 Web ReadableStream（07）。
5. **token 逐步到达**。网络每送来一段，`for await` 迭代出一个 chunk；buffer 累积、按 SSE 协议切出事件，yield 出 text delta（08 + 07）。
6. **增量渲染**。loop 内 `emit("message", delta)`（06），TUI 的 listener 同步执行，`stdout.write(delta)` 立即上屏——用户看到 token 逐个出现（15）。
7. **模型发起工具调用**。本轮流结束，assistant 消息里带 `toolCalls: [{ name: "bash", args: { cmd: "npm test" } }]`；loop `emit("tool_call")`，TUI 画出工具块。
8. **spawn 子进程**。dispatch 到 bash 工具：`spawn("bash", ["-c", "npm test"], { signal, cwd })`（09）。
9. **流式收集输出**。测试输出的每一行从 `child.stdout`（Readable）到达，边追加到结果缓冲边 `emit("tool_output")` 让 TUI 实时滚动显示；`close` 事件拿到退出码（09 + 07）。
10. **结果回传**。退出码 + 输出包成 `role: "tool"` 消息 push 回 `messages`，回到第 3 步——模型看到失败，下一轮发起 write 修改文件，再一轮 bash 复测。
11. **正常结束**。某一轮模型不再要工具：loop 退出 `while`，`emit("agent_end", "done")`，`run()` 的 Promise resolve 最终文本，TUI 渲染收尾。
12. **Ctrl+C 取消路径**（与上面并行的一条线）：

```text
用户按 Ctrl+C（raw mode 下是字节 \x03）
 → TUI 识别 \x03 → controller.abort()                 （04 AbortController）
    │ signal 一次性广播给所有持有者：
    ├─► fetch 请求中断 → client 的 for await 抛 AbortError
    ├─► spawn 收到 signal → 自动 kill 子进程            （09）
    └─► loop 捕获 aborted → emit("agent_end", "aborted")
 → messages 数组保留（已完成的轮次不丢），用户可继续对话
```

注意取消链的关键设计：`AbortSignal` 从 CLI 层创建后一路向下传递（fetch、spawn、每个工具的 run 参数），中间没有任何一层需要"反向调用"上层——这是 04 章取消模型相对于 Java interrupt 标志位的核心优势：信号是广播的，接不接、怎么接是每一层自己的事。

trace 里三个最容易看漏的点：

- 第 6 步的渲染发生在 agent loop 的调用栈里（emit 同步执行），所以"边生成边显示"不需要任何线程或队列——单线程内 for await 的每次让出正好给了渲染时机。
- 第 9 步若不持续读 `child.stdout`，npm test 的输出会塞满管道缓冲区（通常 64KB）并把子进程写端堵死——表现为"测试莫名卡住"，是 09 章第一陷阱。
- 第 12 步的 abort 之后，已完成轮次的 `messages` 完整保留，这是"取消后还能继续对话"的全部实现——没有快照、没有恢复逻辑，就是数组还在。

完整时序图（对应上面 1–11 步）：

```text
用户            TUI(CLI)              Agent Loop           LLM Client           bash 子进程
 │ 按键/回车      │                      │                    │                    │
 ├──────────────►│ stdin data 事件       │                    │                    │
 │               │ submit("修复bug")     │                    │                    │
 │               ├─────────────────────►│ while(true) 轮 1   │                    │
 │               │                      ├─── stream(messages, signal) ──►         │
 │               │                      │                    │ fetch → SSE 连接   │
 │               │                      │                    │◄── chunk ──(网络)  │
 │               │                      │◄─ for await delta ─┤                    │
 │               │◄─ emit("message",δ) ─┤                    │                    │
 │◄──────────────┤ stdout.write(δ)      │                    │                    │
 │               │                      │ 本轮含 toolCall: bash                    │
 │               │◄─ emit("tool_call") ─┤                    │                    │
 │               │                      ├── spawn(signal) ──┼───────────────────►│ npm test
 │               │                      │◄─ for await stdout ┼◄── chunk ──────────┤
 │               │◄─ emit("tool_output")┤                    │                    │
 │               │                      │ push tool result；while 轮 2、3……        │
 │◄──────────────┤ 最终回答 + agent_end ┤ return 文本        │                    │
```

## 16.4 最小 agent loop 骨架【必须掌握】

真实开源项目的形态浓缩版（约 40 行），综合了 01、04、05、07、09、14 六章：

```ts
import { readFile, writeFile } from "node:fs/promises";   // 05：工具的文件能力
import { spawn } from "node:child_process";               // 09：bash 工具
import path from "node:path";                             // 05：路径拼接

interface LLMClient {                                     // 01：类型即协议文档
  stream(msgs: Message[], opt: { signal: AbortSignal }): AsyncIterable<StreamEvent>;
}
interface Tool {
  run(args: Record<string, unknown>, signal: AbortSignal): Promise<string>;
}

export async function agentLoop(
  client: LLMClient, tools: Map<string, Tool>,
  messages: Message[], signal: AbortSignal,                // 04：取消通道贯穿所有 await
): Promise<string> {
  while (true) {                                           // agent loop 本体（对照 LangGraph 的自环图）
    const assistant: Message = { role: "assistant", content: "", toolCalls: [] };
    try {
      for await (const ev of client.stream(messages, { signal })) {   // 07：for await 消费 SSE 事件流
        if (ev.type === "text") assistant.content += ev.text;
        else if (ev.type === "tool_call") assistant.toolCalls.push(ev.call);
      }
    } catch (err) {
      if (signal.aborted) return "";                       // 04：取消不是错误，安静退出
      throw err;                                           // 14：网络/协议错误向上抛给调用方
    }
    messages.push(assistant);

    if (assistant.toolCalls.length === 0) return assistant.content;   // 无工具调用 → 收敛

    for (const call of assistant.toolCalls) {              // 工具分发（串行，顺序可预测）
      const tool = tools.get(call.name);
      let output: string;
      try {
        output = tool
          ? await tool.run(call.args, signal)              // signal 传进每个工具：fs 无感，spawn 自动 kill
          : `unknown tool: ${call.name}`;
      } catch (err) {                                      // 14：工具失败转为 tool result，不炸 loop
        output = `error: ${err instanceof Error ? err.message : String(err)}`;
      }
      messages.push({ role: "tool", toolCallId: call.id, content: output });
    }
  }
}
```

逐段对照它综合了哪些章：

| 代码位置 | 综合的知识 |
|---|---|
| `Message` / `StreamEvent` / `Tool` 接口 | 01：判别 union + interface，读源码时的状态机文档 |
| `while (true)` + `await` | 04：async 函数与事件循环，单线程串行推进 |
| `signal` 参数从函数签名贯到每个 await | 04：AbortController 广播式取消（16.3 第 12 步） |
| `for await ... of client.stream(...)` | 07：LLM client 暴露 async iterator，消费 SSE 解析后的事件 |
| `readFile` / `writeFile` / `path.resolve`（工具实现里） | 05：fs/promises + path，read/write 工具的全部 |
| `spawn`（bash 工具实现里） | 09：流式输出、退出码、signal 自动 kill |
| `catch` 分支的两条路 | 14：取消≠错误；工具错误降级为 tool result，模型自己读栈 |

## 16.5 打开一个真实 Coding Agent 项目先看什么【必须掌握】

有序清单，每步附"通常会看到的代码特征"。目标：30 分钟内建立修改地图。

1. **根 package.json——判断工具链与结构**。看 `workspaces`（有则是 monorepo，进 12 章的模式）、`scripts`（`check` 用 `tsc --noEmit` 还是 biome/eslint；`dev` 用 tsx 即时转译还是先 build）、`packageManager`。特征：`"workspaces": ["packages/*"]`、`"dev": "tsx packages/cli/src/main.ts"`。
2. **找 bin——定位 CLI 入口**。看各包 package.json 的 `"bin": { "pi": "dist/cli.js" }`，顺着文件名找到入口源文件。特征：bin 指向的文件顶层 `import ... from "./main.js"`，且附近常有 shebang `#!/usr/bin/env node`。
3. **读入口文件——argv / env / 信号三件套**。看它怎么解析 `process.argv`（自写 parse 还是 commander/yargs）、读哪些 `process.env`（API key、base URL）、注册了哪些 `process.on("SIGINT"/"SIGTERM"/"exit")`。特征：一个 `main()` 函数 + 顶层的信号注册 + `AbortController` 的创建点——取消链的源头在这里。
4. **搜 agent loop——全项目最核心的 40 行**。全局搜 `while`、`for await`、`toolCall` 三个关键词的交集，通常落在 packages/agent 的单文件里。特征：`while (true)`、`messages.push`、`for await (const ev of ...)`、按 `role` 或 `type` 的 switch。
5. **看 tools 目录——fs/spawn 的映射表**。每个工具一个文件，签名统一为 `(args, signal) => Promise<string>`。特征：read/write 里 `fs/promises` + `path.resolve`；bash 里 `spawn` + `child.stdout.on("data")` + 超时常量；结尾都有输出截断（防止爆 context）。
6. **看事件如何到 UI**。从 loop 里的 `emit(`（或 `yield`）反向搜：谁 `on("message"`、谁 `for await` 消费。特征：TUI 包里一组 `agent.events.on(...)` 订阅，或一个把事件序列化后写 stdout / IPC channel 的桥接函数。

看完这六步，你应该能回答三个问题：入口在哪、循环在哪、事件怎么变成屏幕上的字。之后任何修改都能定位到具体层。

## 16.6 架构变体【看懂即可】

- **同步 emitter 直连 vs 事件队列 / async generator**：取舍已在 16.2.6 展开。一句话：前者是"函数调用伪装的事件"，后者是"真正的队列语义"——需要回放、跨进程、严格顺序时选后者。
- **独立 TUI 进程：fork + IPC**（衔接 09 章）：把 TUI 拆成子进程，agent 主进程通过 IPC channel（`process.on("message")`）发送序列化事件。动机：TUI 崩溃不拖垮会话、一个 agent 可多客户端附着、渲染进程可独立重启。代价：事件必须可序列化（Buffer 走 structuredClone 要转码）、延迟多一跳。看到 `fork(` 或 `child.send(` 就是在用这个形态。
- **LangGraph 经验如何映射**：你熟悉的 `StateGraph` 在这里退化成自环——对照表：

| LangGraph 概念 | 手写 loop 对应物 | 差异一句话 |
|---|---|---|
| 节点（node） | loop 内的分支（工具调用 vs 结束） | 无显式图结构，控制流就是代码 |
| State（channel） | `messages` 数组 | reducer 变成显式 `push` |
| 条件边（conditional edge） | `if (toolCalls.length === 0) return` | 一样，只是写法 |
| checkpointer | session 文件 + `messages` 持久化 | 要自己写落盘时机 |
| interrupt / Command | AbortController + 恢复时读 session | 无框架托管的中断点 |

取舍：需要多 agent 编排、复杂的图拓扑、时间旅行调试时 LangGraph 值得；单 agent + 工具循环时，手写 loop 少一层抽象、栈可读、错误路径直观——这也是多数开源 Coding Agent 的选择。

## 本章只记住这 5 件事

1. Coding Agent = 分层管道：CLI → Session → while loop → LLM 流 → 工具 → 事件 → TUI，每层恰好落在教材一章的知识上，层间只靠事件与 await 衔接。
2. LLM 流式 = async iterator：client 把 fetch + SSE 解析包成 `for await` 可消费的形态，chunk 与事件边界分离靠 buffer 累积（07 + 08）。
3. 工具映射固定：read/write → `fs/promises` + `path`；bash → `spawn` 流式收集 + `AbortSignal.any([用户取消, 超时])`。
4. 取消是广播不是调用：Ctrl+C → `controller.abort()` → signal 贯穿 fetch / spawn / 每个工具，中间层零反向依赖。
5. 事件层两种风格：同步 emitter 直连（简单、多订阅者）vs 事件队列 / async generator（可回放、跨进程、类型友好），真实项目混用。
6. monorepo 依赖只能向下：ai ← agent ← coding-agent，agent 不认识终端，事件解耦是包结构的前提。
7. LangGraph ≈ 自环图：node/State/条件边/checkpoint 分别映射到循环分支、messages、if-return、session 文件。

## 源码识别

- 看到 `while (true)` + `messages.push` + `for await` 三件套 → agent loop 本体，项目最核心的 40 行
- 看到 `for await (const chunk of res.body)` → SSE 流式消费，往下找 buffer 累积与事件切分
- 看到 `AbortSignal.any([...])` / `AbortSignal.timeout(...)` → 取消/超时的标准组合，追 signal 来源就能找到 CLI 入口
- 看到 `spawn(cmd, args, { signal })` + `child.stdout.on("data")` → bash 工具，流式收集 + 自动 kill
- 看到 `stdin.setRawMode(true)` → TUI 输入层启动，Ctrl+C 变成 `\x03` 字节要自己处理
- 看到 `emit("message" | "tool_call" | "tool_result")` → agent 生命周期事件源，UI 的全部输入
- 看到 `async function*` + `yield { type: ... }` → 事件队列风格，消费者用 for await 拉取
- 看到 `fork(` / `child.send({ type: ... })` → 独立 TUI 进程 + IPC 变体
- 看到 `import { ... } from "@scope/agent"`（packages 间按包名引用）→ workspaces 分层，对照依赖方向图
- 看到 package.json 的 `"bin"` → CLI 入口声明，顺藤摸 main 文件

## Java/Python 工程师常见误区

- 错误认知：agent loop 需要框架（LangGraph 式执行器）才"正确" → 实际：单 agent 场景就是 40 行 while 循环，框架的价值在图编排与 checkpoint，CLI agent 通常不需要。
- 错误认知：`emit("message", delta)` 是异步推送，UI 慢点没关系 → 实际：同步函数调用，TUI 渲染在 loop 的调用栈里执行，渲染必须快（06）。
- 错误认知：Ctrl+C 靠异常或中断标志逐层 catch 传播 → 实际：AbortSignal 广播，每层自己决定响应方式（fetch 抛错、spawn kill、loop 静默退出）。
- 错误认知：LLM 流式输出的每个 chunk 就是一个 token/事件 → 实际：chunk 只是 TCP 分段，事件边界要自己 buffer 后按 SSE 协议切（08 的经典应用）。
- 错误认知：bash 工具等命令跑完一次性拿输出就行 → 实际：stdout 管道缓冲区有限，不边读边消费会卡死子进程；长输出还要截断防爆 context（09）。
- 错误认知：monorepo 里跨包引用走相对路径 `../tui` → 实际：走 workspace 包名，且依赖方向必须向下，agent 反向 import UI 是架构坏味道。

## 是否值得深入

- 总架构图与生命周期 trace：当前阶段：建议掌握——任何 Coding Agent 源码的定位地图。
- 最小 agent loop 骨架：当前阶段：建议掌握——能默写它，等于能改任何一层的实现。
- SSE 协议细节与 Web Stream / Node Stream 互转：当前阶段：不需要深入——知道"chunk 要 buffer 后切事件"即可，改流式解析时再查 07/08。
- TUI 渲染实现（转义序列、差异重绘、组件状态机）：当前阶段：不需要深入——当黑盒用，只看它的事件订阅面。
- fork + IPC 多进程架构：当前阶段：看懂即可——单进程是主流，遇到多客户端需求再回 09。
- LangGraph 与手写 loop 的全量对照：当前阶段：不需要深入——核心映射表已给，编排需求出现时再展开。
