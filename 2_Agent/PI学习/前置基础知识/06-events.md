# EventEmitter：Node 的事件模型

> EventEmitter 是 Node 内置的进程内发布/订阅原语，也是半个标准库的基类——stream、HTTP server、子进程、标准流全是它的子类。对写 Agent 的你，它是"生命周期事件"的标准载体：agent loop 发事件，TUI 订阅渲染。本章核心只有一个心智模型：emit 是同步函数调用，不是发消息。

## 6.1 解决什么问题

一个对象想在"某事发生时"通知任意多个关心者，而不想把它们写死在自己的代码里。Java 里你会用 Swing Listener、Guava EventBus 或 Spring 事件；Node 把这个模式做成了标准库基类。

心智模型：内部就是一张 map，没有更多魔法，下面所有行为都能从它推出来：

```text
EventEmitter 内部（心智模型）
  listeners = { "message": [fnA, fnB], "tool_call": [fnC] }

  on("message", fnA)   → listeners["message"].push(fnA)
  emit("message", δ)   → for (fn of listeners["message"]) fn(δ)   ← 同步逐个调用
  off("message", fnA)  → 从数组里 splice 掉
```

### API 基本面【必须掌握】

```ts
import { EventEmitter } from "node:events";

const bus = new EventEmitter();

bus.on("tool_call", (name: string, args: unknown) => {   // listener 就是普通函数
  console.log("call:", name, args);
});

bus.once("agent_end", () => console.log("done"));        // 触发一次后自动移除

bus.emit("tool_call", "read", { path: "a.ts" });         // true：有人听
bus.emit("nobody_listens");                              // false：无人听，安静返回
```

| 方法 | 作用 | 近似对应 |
|---|---|---|
| `on(event, fn)` | 注册 listener，同一事件可注册多个 | addActionListener / subscribe |
| `once(event, fn)` | 触发一次后自动移除 | — |
| `emit(event, ...args)` | 同步调用全部 listener，返回是否存在 | fire / publish（但同步） |
| `off(event, fn)` | 移除某一次注册（别名 removeListener） | removeActionListener |

四个要点：

- listener 是普通函数。this 一句话：普通函数里 this 指向 emitter 本身，箭头函数捕获外层——源码里几乎全是箭头函数，通常无感。
- `emit` 返回 boolean 表示有没有 listener；没人听不报错，事件直接消失。
- 事件名是任意字符串，参数是任意个位置参数，**没有类型约束**。Java 会为每种事件定义 `XxxListener` 接口；Node 靠约定，TS 里用"接口 + 重载声明"补类型（见 6.7 的骨架）。
- 同一事件的多个 listener 全部执行，没有去重。

## 6.2 emit 是同步调用【必须掌握——与 Kafka 的分水岭】

```ts
console.log("1");
bus.emit("x");          // 所有 listener 按注册顺序同步执行完，才轮到下一行
console.log("2");
// 输出恒为：1 → (各 listener 的输出) → 2
```

```text
emit("x", payload)
  ├─ listener A（第 1 个注册）  ← 抛错？B、C 不再执行，异常沿 emit 调用栈向上
  ├─ listener B                ← 耗时 3s？整条线程卡 3s
  └─ listener C
emit 返回 true，主流程继续
```

三条推论，读源码与写代码都受用：

- listener 抛错会打断本次 emit 的后续 listener，异常沿调用栈向上（谁 emit 谁接住）。
- 慢 listener 阻塞整个线程（事件循环），没有线程池兜底。
- 执行顺序 = 注册顺序，可靠且可预测。

所以 EventEmitter 的准确定义是：**进程内同步函数调用分发**。它不是消息队列——没有异步、没有持久化、没有重试、没有消费确认、没有跨进程、没有背压。emit 的全部成本就是 N 次函数调用。

## 6.3 类比校准表：哪些直觉能用，哪些会害你

| 你熟悉的东西 | 结论 | 差异 |
|---|---|---|
| Swing / AWT Listener | 部分类比 | 同步回调一致；那边有事件派发线程，这边在调用者线程执行 |
| Guava EventBus | 部分类比 | 同步分发相似；@Subscribe 方法签名 vs 事件名字符串 + 位置参数 |
| Spring ApplicationEvent | 部分类比 | publishEvent 默认同步执行 listener，可配 executor 变异步；EventEmitter 没有这层开关 |
| Kafka / RabbitMQ | 不应类比 | 跨进程、异步、持久化、重试 / 确认——EventEmitter 一概没有 |
| Python 回调列表 / PyDispatcher | 部分类比 | 同为进程内同步回调 |
| asyncio | 无直接对应 | listener 是同步函数，emit 不会 await 它 |

读源码口诀：看到 `emit`，脑子里展开成"for 循环逐个调用注册的函数"，而不是"发了一条消息"。

## 6.4 'error' 事件的特殊性【必须掌握】

```ts
const rs = createReadStream("missing.log");
rs.on("data", (c) => process.stdout.write(c));
// 少了 on("error", ...)：文件打不开时流会 emit("error")，无人监听
// → Node 把它当未捕获异常，进程直接崩（非 0 退出码）

rs.on("error", (err) => console.error(err));   // 所以源码里 error listener 几乎必挂
```

这是 `'error'` 这个事件名独有的行为：其他事件无人听只是返回 false，error 无人听就是崩溃。错误怎么接、往哪传，体系归第 14 章；本章记住"看到 error listener 缺席要警觉"即可。

## 6.5 max listeners 与事件泄漏【看懂即可】

- 同一事件默认超过 10 个 listener，stderr 打印 `MaxListenersExceededWarning`——只是警告，功能照常。它是**泄漏提示器**：长生命周期对象上反复 on 而不 off，闭包连着大对象不放，靠这条警告发现。
- `removeAllListeners(event?)` 一次清空，常见于会话结束与测试 teardown。
- 看到 `setMaxListeners(n)`，说明附近要么真需要很多 listener，要么在压泄漏警告——值得多看一眼。

## 6.6 为什么 Node 生态全是事件模型【必须掌握】

标准流、net/http server、child process、stream 全部继承 EventEmitter。判别法一句话：**一个东西能 `.on(...)`，它就是 EventEmitter 系**。最常遇到的是 stream（Stream 是 EventEmitter 的子类，`stream.on("data")` 就是本章这套机制——流本身的细节归第 07 章）：

```ts
process.stdin.on("data", (chunk) => {...});     // 标准输入
server.on("connection", (socket) => {...});     // TCP / HTTP
child.on("exit", (code) => {...});              // 子进程退出
stream.on("data", (chunk) => {...});            // 流数据
```

### 与异步的桥接【看懂即可】

`events.on(emitter, "event")` 返回 async iterator，可以 `for await` 消费事件——这是第 04 章异步迭代器最常见的落点，与流的关系在第 07 章展开：

```ts
import { on } from "node:events";
for await (const [line] of on(rl, "line")) { handle(line); }
```

## 6.7 结合 Agent：生命周期事件解耦 UI 与主流程

Coding Agent 的标准设计：agent loop 只管推进并 emit 事件；TUI 订阅事件做渲染；主流程函数照常 return 最终结果，不订阅的调用方（单测、脚本）也能用。

类型化事件骨架（TS 补类型的标准写法——接口 + 重载声明）：

```ts
import { EventEmitter } from "node:events";

export interface AgentEvents {
  agent_start: (sessionId: string) => void;
  message: (delta: string) => void;                      // LLM 流式增量
  tool_call: (name: string, args: Record<string, unknown>) => void;
  tool_result: (name: string, output: string) => void;
  agent_end: (reason: "done" | "error" | "aborted") => void;
  error: (err: Error) => void;
}

export interface AgentEmitter extends EventEmitter {
  on<K extends keyof AgentEvents>(event: K, listener: AgentEvents[K]): this;
  emit<K extends keyof AgentEvents>(
    event: K,
    ...args: Parameters<AgentEvents[K]>
  ): boolean;
}

export class Agent {
  readonly events = new EventEmitter() as AgentEmitter;

  async run(prompt: string): Promise<string> {
    this.events.emit("agent_start", this.sessionId);
    // ... agent loop：每收到一段模型输出
    this.events.emit("message", delta);
    // 每次执行工具前后
    this.events.emit("tool_call", "read", args);
    const output = await this.runTool("read", args);
    this.events.emit("tool_result", "read", output);

    this.events.emit("agent_end", "done");
    return finalText;              // 主流程照常直返结果，不经事件
  }
}
```

消费端（TUI）：

```ts
const agent = new Agent();
agent.events.on("message", (d) => tui.appendStream(d));
agent.events.on("tool_call", (name) => tui.pushLine(`-> ${name}`));
agent.events.on("error", (e) => tui.showError(e));

const answer = await agent.run("重构这个模块");   // 渲染归事件，结果归返回值
```

```text
        agent loop（只管推进，不认识 TUI）
   emit("message", δ)   ──┬─► TUI：渲染流式文本
   emit("tool_call", …) ──┼─► 日志模块：落盘
   emit("agent_end", …) ──┴─► 遥测：计数
        │
        ▼
   return finalText ─────────► 调用方 await 拿结果（不订阅也能用）
```

这套解耦的价值：agent loop 对 UI 零依赖——单测只断言事件序列，不用起终端；新增消费者（日志、遥测、headless 模式）不动主流程。这正是 Coding Agent 把 LLM 流式过程与终端渲染解耦的方式。注意 6.2 的推论在这里生效：emit 是同步的，TUI 的渲染函数在 agent loop 的执行栈里跑——渲染必须快，重活（落盘、网络）要异步化。

## 本章只记住这 5 件事

1. EventEmitter = 进程内一对多同步回调分发：on 注册、emit 触发、off 移除，内部就是一张 `map<string, fn[]>`。
2. emit 是同步的：listener 按注册顺序执行完才继续；抛错打断后续，慢 listener 阻塞线程。
3. 它不是 Kafka / EventBus：没有异步、持久化、重试、跨进程——emit 的成本就是 N 次函数调用。
4. `emit("error")` 无人监听 = 进程崩溃，所以源码里 `on("error", ...)` 几乎必挂。
5. 能 `.on` 的对象就是 EventEmitter 系：stream、server、stdin、child process 全是。
6. Agent 用它解耦：loop 发生命周期事件，TUI 订阅渲染，最终结果照常 return。

## 源码识别

- 看到 `extends EventEmitter` → 这个类对外发事件，找它的 emit 调用点就是全部事件源
- 看到 `xxx.on("data", ...)` → 流式读数据，机制本章、流细节第 07 章
- 看到 `on("error", ...)` → 保命 listener，防止 error 事件炸进程
- 看到 `emit("message" / "tool_call" / ...)` → agent 生命周期事件源，UI 靠它更新
- 看到 `new EventEmitter() as TypedEmitter` / 接口重载 → TS 类型化事件声明
- 看到 `for await (... of on(emitter, "x"))` → 事件转异步迭代器消费
- 看到 `setMaxListeners(n)` → 在压制泄漏警告，附近可能有事件泄漏
- 看到 `removeAllListeners()` → 会话结束 / 测试 teardown / 对象重置

## Java/Python 工程师常见误区

- 错误认知：emit 相当于 Kafka 的 send，异步投递给消费者 → 实际：同步函数调用，emit 返回时 listener 已全部执行完。
- 错误认知：listener 可以是 async 函数，EventEmitter 会等它 → 实际：返回的 promise 被无视，其中的 rejection 变成 unhandledRejection。
- 错误认知：无人监听的事件会被缓存或重放 → 实际：当场丢弃，emit 返回 false。
- 错误认知：error 无人监听只是丢一条日志 → 实际：进程以非 0 退出。
- 错误认知：多个 listener 并行执行或有优先级 → 实际：注册顺序、串行、无优先级。
- 错误认知：EventEmitter 有背压或慢消费者隔离 → 实际：零隔离，一个慢 listener 卡住所有后续。

## 是否值得深入

- on / once / emit / off 与同步语义：当前阶段：建议掌握——读任何 Node 源码的基础词汇。
- 类型化 EventEmitter 骨架：当前阶段：建议掌握——Agent 项目里到处是这个模式。
- captureRejections（async listener 的错误接驳）：当前阶段：不需要深入——低频开关，读到再查。
- listener 内部数据结构与 newListener 等钩子事件：当前阶段：不需要深入——对读源码无增益。
