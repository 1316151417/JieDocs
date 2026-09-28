# 异步编程：Promise、async/await 与取消

读 Coding Agent 源码，90% 的控制流是三个原语的组合：等待（await）、并行（组合子）、取消（AbortSignal）。本章把这三件事一次讲透。带着 Java/Python 的直觉进来没有问题，但有三处不等价必须提前立牌子：

1. Promise 是 **eager** 的：调用 async 函数即开始执行（Python coroutine 是惰性的）。
2. await 挂起的是**函数**，不是线程也不是进程。
3. 取消不在 Promise 里，在 **AbortSignal** 里。

错误处理的完整体系归第 14 章，本章涉及异常时只指路不展开。

## 4.1 callback 风格【看懂即可】

读 2015 年前后的老代码（以及至今未迁移的库）会遇到 error-first callback（nodeback）：回调是最后一个参数，第一个参数永远是 err，无错为 null。

```js
fs.readFile("config.json", (err, data) => {
  if (err) return console.error(err);
  console.log(data.length);
});
```

为什么要进化出 Promise：

- 缩进随每个步骤右移（回调地狱），步骤间共享状态只能靠闭包捕获。
- 错误处理分散在每个回调的 `if (err)` 里，没有统一的 catch 位置。
- "进行中的操作"无法当值返回、无法传递，也就无法组合（没有 all/race 这类算子）。

EventEmitter 风格的流（`on("data")`）同属这个时代，第 07 章单独讲。

## 4.2 Promise【必须掌握】

三种状态：`pending` → `fulfilled` / `rejected`（后两个合称 settled）。两条硬规则：

1. **一旦 settled 永不改变**：fulfilled 的值 / rejected 的原因定死，之后再调 resolve 是 no-op。
2. **executor 同步立即执行**：`new Promise(fn)` 的 fn 在构造那一刻就跑。这条是 JS 与 Python 差异的根源（见 4.2.2）。

```ts
const p = new Promise<number>((resolve, reject) => { // executor：立刻同步执行
  setTimeout(() => resolve(42), 100);                 // 100ms 后 settle，之后不可变
});
```

### 4.2.1 链式与传递

```ts
getUser(id)                      // Promise<User>
  .then((u) => u.name)           // 返回普通值 → 下一环以该值 fulfill
  .then((name) => search(name))  // 返回 Promise → 链等它 settle 再继续
  .then((res) => res.items)
  .catch((err) => log(err));     // 链上任一环抛出/拒绝都到这里（错误处理体系第 14 章）
```

三条规则：`.then` 每次返回**新的** Promise；回调返回普通值 → 下一环立即以该值 fulfill；返回 Promise → 下一环等它 settle。异常沿链向后传递直到最近的 `.catch`。效果上，链把"多步异步 + 统一错误出口"编码成了一个值——这正是回调给不了的。

### 4.2.2 对照 CompletableFuture

相似：都是未来值的容器，组合算子一一对应——`thenApply` ≈ `then`、`thenCompose` ≈ 返回 Promise 的 `then`、`allOf` ≈ `Promise.all`、`exceptionally` ≈ `catch`。

不等价（读代码时的实际差别）：

- CF 可以在任意线程上 `complete(value)` / `completeExceptionally(err)` 手工完成；Promise 只有 executor 里的 resolve/reject 一个入口，构造之后外界无法干预。
- CF 的 `supplyAsync(fn, pool)` / `thenApplyAsync` 隐含线程池选择，背后是一整套线程调度语义；Promise 世界没有线程概念，回调在哪跑不是 API 参数。
- CF 继承 `Future.cancel`，能把 future 标记为取消（底层任务照跑）；**Promise 连 cancel 接口都没有**——这个缺口是 AbortController 存在的原因（4.8 节）。

### 4.2.3 对照 Python asyncio

- Python 的 coroutine 对象是**惰性**的：`foo()` 只创建对象，一行代码都不执行，必须 `await` 或 `create_task` 才跑。
- Promise 与 async 函数是 **eager** 的：调用即开始执行函数体，直到第一个让出点。
- 实际后果：JS 里 `llmCall()` 写了没 await，请求已经发出去了（fire-and-forget 的根源，4.4 节）；Python 里同样的裸调用什么都没发生。
- asyncio 的 `Task.cancel()` 能向协程注入 `CancelledError`，取消是一等公民；JS 在 Promise 层没有等价物，AbortSignal 是后来的统一补丁。

## 4.3 `await foo()` 到底发生了什么【必须掌握】

最小代码，编号对应下面的 trace：

```ts
async function run() {
  console.log("1 同步段");
  const res = await fetch("https://api.example.com/v1/messages"); // ①
  console.log("3 恢复后");
  return res.status;
}

run();
console.log("2 调用方继续");
```

逐步 trace：

1. `run()` 被调用，函数体**同步**执行，打印 "1 同步段"。
2. 到 ①：先求值 `fetch(...)`——向 OS 发出非阻塞请求（不占 JS 线程），立刻返回一个 pending 的 Promise。
3. `await` 让出：`run` 在 ① 处挂起，并**立刻**向调用方返回一个 pending Promise。控制权回到 `run()` 之后，打印 "2 调用方继续"。
4. 主线程没有别的同步代码了，Event Loop 转起来；此期间别的任务（其他请求的回调）穿插执行。
5. 响应到达：OS 通知 libuv → fetch 内部 resolve 那个 Promise → ① 之后的代码作为 microtask 入队。
6. JS 线程执行该 microtask：从 ① 处恢复，`res` 绑定响应对象，打印 "3 恢复后"，跑完函数体。

```
JS 线程      Event Loop               OS / libuv
  | run() 同步段
  | fetch() 注册 I/O ----------------->  发出请求（非阻塞）
  | await 挂起 run，控制权返回调用方
  | 执行其他任务 ...                     （响应在路上）
  |             <----------------------  响应到达（事件）
  |             resolve(promise)
  | microtask：从 await 处恢复 run
  | run 后续同步段
```

三个精确结论：

- **await 挂起的是这个 async 函数**：不阻塞线程（线程回 Event Loop 干别的），也不阻塞进程（其他请求照常处理）。
- await 右边不是 Promise 会被包成 Promise（`await 42` 合法），所以老代码 `await` 一个 thenable 也能跑。
- **await 边界是并发交错点**：恢复执行时，函数外部的共享状态可能已被其他任务改过——这是 JS 里真正需要小心的"竞态"，对应 Java 里"释放锁到重新拿锁之间的间隙"。

## 4.4 async 函数【必须掌握】

四个事实：

1. **返回 Promise**：`async function f(): Promise<number>`，函数体 `return 42` → 调用方拿到 fulfilled(42)；函数体抛异常 → rejected Promise。
2. **async 不等于开线程**：整个函数在唯一 JS 线程上分段执行，段与段之间穿插别的任务。
3. **未 catch 的 rejection**：async 函数的异常变成 rejected Promise，没人接就走到 `unhandledRejection`，Node 默认直接崩进程（处理策略第 14 章）。
4. ESM 的任何模块（不限于入口文件）都支持 top-level await（CommonJS 不支持），所以源码顶层随处可见 await。

### 4.4.1 fire-and-forget：调用不 await

```ts
// 日志上报 / 缓存预热：启动后台任务，既不等待也不让调用方等
void logger.flush(); // void 是给读者和 lint 的信号：故意不 await
```

因为 Promise 是 eager 的，这行执行时任务**已经在跑了**。对照 Python：

- JS `logger.flush()` ≈ Python `asyncio.create_task(logger.flush())`（已提交执行）
- Python 裸调用 `logger.flush()` 只得到 coroutine 对象、什么都不做 ≈ JS 没有这个形态

坑：rejection 无人接住。要么 `.catch(log)`，要么依赖项目统一兜底（第 14 章）。读源码看到裸调 async 函数，第一反应应该是"它的错误去哪了"。

## 4.5 组合子：all / allSettled / race / any

| 组合子 | 语义 | 最近对应物 |
|---|---|---|
| `Promise.all` | 全部 fulfilled 才 fulfill；任一 reject 立刻整体 reject（fail-fast） | `CompletableFuture.allOf` / `asyncio.gather` |
| `Promise.allSettled` | 等全部 settle，收集各自成败 | `gather(return_exceptions=True)` |
| `Promise.race` | 第一个 settle 的胜出（无论成败） | 无直接对应 |
| `Promise.any` | 第一个 fulfilled 胜出；全败才 reject（AggregateError） | 无直接对应 |

```ts
// all：要么全要，要么整体失败。并行取"必需"数据
const [user, orders] = await Promise.all([getUser(id), getOrders(id)]);
```

fail-fast 注意：reject 时**其余 Promise 并不会被取消**，只是结果被丢弃——all 的 reject 只意味着"我不等了"。

```ts
// allSettled：并行执行 tool calls，一个失败不连坐
const results = await Promise.allSettled([runTool(callSearch), runTool(callBash)]);
const outputs = results.map((r) =>
  r.status === "fulfilled" ? r.value : toolError(r.reason), // 失败转成错误消息回给模型
);
```

这是 Parallel Tool Calls 的标准写法：单个 tool 挂了，其余结果照常交给模型（错误细节第 14 章）。

```ts
// race：谁先 settle 用谁 → 超时的经典实现
const res = await Promise.race([
  callLLM(input),
  new Promise((_, reject) => setTimeout(() => reject(new Error("timeout")), 30_000)),
]);
```

注意：超时赢了之后 `callLLM` 仍在跑（没被取消），timer 也还挂着。生产代码更多用 `AbortSignal.timeout`（4.8 节），它把"超时"和"取消"合成一步。

```ts
// any：多镜像源，取最快成功的那个
const pkg = await Promise.any([
  fetchRegistry(`https://registry.npmjs.org/${name}`),
  fetchRegistry(`https://mirror.example.com/${name}`),
]);
```

## 4.6 microtask【必须掌握】

队列概念：`.then` 回调、`await` 续体、`queueMicrotask(fn)` 进的都是同一个 microtask 队列。规则一句话：**当前同步代码全部执行完之后、Event Loop 的下一个宏任务之前，把 microtask 队列清空（执行中产生的新 microtask 也在本轮清完）。**

```ts
console.log("1");
Promise.resolve().then(() => console.log("3"));
setTimeout(() => console.log("4"));
console.log("2");
// 固定输出：1 → 2 → 3 → 4（microtask 永远先于下一个宏任务）
```

读源码意义有两条。其一：`.then` 回调"几乎立刻，但一定在当前栈清空之后"。更要紧的是反面：**await 边界两侧之间可能插入了任意多个其他任务的执行**——跨 await 读写共享状态，必须当作"中间发生过任何事"来防御。

### 4.6.1 nextTick / setImmediate / setTimeout 的顺序【看懂即可】

```js
setTimeout(() => console.log("timeout"));
setImmediate(() => console.log("immediate"));
Promise.resolve().then(() => console.log("promise"));
process.nextTick(() => console.log("nextTick"));
console.log("sync");
// 固定：sync → nextTick → promise
// 不定：timeout 与 immediate 谁先（阶段顺序问题，知道存在即可，需要时再查）
```

`process.nextTick` 是 Node 特有的最高优先级微任务（排在 Promise then 之前）；`setImmediate` 是宏任务。规范级顺序细节【暂时跳过】。

## 4.7 timer：返回对象与 unref()【看懂即可】

`setTimeout` / `setInterval` 返回 `NodeJS.Timeout` 对象（浏览器里是 number id，别混）。它有 `unref()`：声明"这个 timer 不阻止进程退出"。

```ts
const heartbeat = setInterval(() => ping(), 10_000);
heartbeat.unref(); // 心跳不能成为进程活着的理由
```

CLI 里给兜底超时/心跳加 unref 很常见——否则一个被遗忘的 setInterval 能让进程永远挂着。进程退出时机的系统分析在第 15 章。

## 4.8 async iterator 与 for await...of【必须掌握】

解决的问题：**"取下一个元素"本身是异步的**。同步 for-of 假设 `next()` 立刻返回；token 流、文件块、子进程输出行都做不到。协议本体：

```ts
interface AsyncIterator<T> {
  next(): Promise<{ value: T; done: boolean }>;
}
interface AsyncIterable<T> {
  [Symbol.asyncIterator](): AsyncIterator<T>;
}
```

手写一个最小实现（去掉全部语法糖，3 次产出后结束）：

```ts
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function ticker(): AsyncIterable<string> {
  let i = 0;
  return {
    [Symbol.asyncIterator]() {
      return {
        async next() {
          if (i >= 3) return { value: undefined, done: true };
          await sleep(100); // 模拟异步生产：拿下一格要等
          return { value: `token-${i++}`, done: false };
        },
      };
    },
  };
}

for await (const t of ticker()) console.log(t); // 每 100ms 一行，共 3 行
```

`for await...of` 的循环体写起来与同步 for-of 相同，但每次迭代之间让出线程。语法糖一句话带过：`async function* gen() { yield await produce(); }` 是编译器替你实现上述协议的 async generator，消费方式同样是 for await...of。

为什么是必须掌握：第 07 章的 Node Stream、各家 LLM SDK 的流式响应（`for await (const event of stream)`）都是这个协议的实现者。异步生产的数据序列——元素何时到达不确定——天然就该用"next 是 Promise"来表达；协议立在这里，后面所有的"流"只是它的实例。

## 4.9 AbortController / AbortSignal【必须掌握】

为什么需要：Promise 的设计里没有取消——一旦创建必然走向 settle，也没有外部入口改写结果。但 Agent 场景充满"用户按了 Esc，请求别发了 / 断掉"的需求。解法是**协作式取消**：调用方发信号，被调用方在合适的点检查信号、自行停止，并以异常报告"我被取消了"。

两个角色：AbortController 是遥控器（调 `abort()`），AbortSignal 是信号本身（传给被取消方）。一次 abort 触发 signal 上的 `'abort'` 事件，所有持有者各自清理——它成为通用取消抽象的原因就在这：fetch、Stream（第 07 章）、child_process、各家 LLM SDK、几乎所有现代库都接受 `signal` 参数，取消得以沿调用链传播。

```ts
// LLM 请求：外部取消 + 超时
const controller = new AbortController();     // 遥控器：Ctrl+C 处调 controller.abort()
const timeout = AbortSignal.timeout(30_000);  // Node 17.3+：到点自动 abort 的 signal
const signal = AbortSignal.any([controller.signal, timeout]); // Node 20+：任一触发即取消

signal.addEventListener("abort", () => {
  // 取消发生时的清理：记日志、断上游连接、释放缓冲
}, { once: true });

try {
  const res = await fetch("https://api.example.com/v1/messages", { signal });
  return await res.json();
} catch (err) {
  if (controller.signal.aborted) return cancelled(); // 用户主动取消
  if (timeout.aborted) throw new Error("llm timeout"); // 超时
  throw err; // 真错误，处理见第 14 章
}
```

四个要点：

- abort 后，等待中的 Promise 以 AbortError（DOMException）reject；`AbortSignal.timeout` 触发时 reason 是 TimeoutError——统一当"取消类异常"处理，不要对 name 做脆弱的硬编码分支（如上，用 `signal.aborted` 区分来源更稳）。
- 已 settle 的 Promise 不受 abort 影响；取消只在"还在等"的地方生效。
- abort 是通知不是打断：纯 JS 的长 CPU 循环收不到 abort 事件、不会被中断；能被取消的是真正挂在 I/O 上的操作，以及在检查点主动读 `signal.aborted` 的代码。
- `AbortSignal.timeout(ms)` 比手写 `race + setTimeout` 干净，还顺带取消了底层 I/O。

## 4.10 Agent 场景：原语怎么拼起来

四个高频场景，各自对应一个原语：

- **LLM Streaming**：`for await` 消费 token 流（async iterator）。
- **Tool Execution**：async 函数 + `allSettled` 并行，单 tool 失败转错误消息回模型。
- **Timeout**：`AbortSignal.timeout`（或手写 race）。
- **Cancellation**：一个顶层 AbortController，从 Ctrl+C 一路传到 fetch 与子进程。

agent loop 骨架（读真实 Coding Agent 源码前，先把这段刻进脑子）：

```ts
async function agentLoop(userMsg: string, signal: AbortSignal): Promise<string> {
  const messages: Message[] = [{ role: "user", content: userMsg }];
  while (true) {
    // 1. 调 LLM：外部取消 + 超时合并成一个 signal，沿调用链下传
    const stream = await callLLM(messages, {
      signal: AbortSignal.any([signal, AbortSignal.timeout(120_000)]),
    });

    // 2. 流式消费：每拿到一段就渲染（async iterator）
    let assistant = "";
    for await (const delta of stream) {
      assistant += delta.text;
      render(delta.text);
    }
    messages.push({ role: "assistant", content: assistant });

    // 3. 本轮要不要调 tool；没有 → 循环终止
    const calls = extractToolCalls(assistant);
    if (calls.length === 0) return assistant;

    // 4. 并行执行 tool：allSettled，失败不连坐
    const settled = await Promise.allSettled(calls.map((c) => runTool(c, signal)));
    messages.push(
      ...settled.map((r, i) =>
        r.status === "fulfilled"
          ? toolResult(calls[i], r.value)
          : toolError(calls[i], r.reason), // 错误如何回给模型：第 14 章
      ),
    );
    // 5. 回到 1：带着 tool 结果再问一轮
  }
}
```

骨架里四个原语各就各位：signal 负责取消链、for await 负责流、allSettled 负责并行容错、timeout 负责兜底。真实项目的复杂度，基本是往这四个位置上叠参数、叠重试。

## 本章只记住这 5 件事

1. Promise 是 eager 的：调用 async 函数即开始执行；Python coroutine 惰性，不 await 不跑。
2. await 挂起的是这个 async 函数——不阻塞线程、不阻塞进程；线程回 Event Loop。
3. 组合子选型：all = fail-fast 并行；allSettled = 收集全部成败（tool 并行标配）；race = 超时；any = 最先成功。
4. microtask（then 回调、await 续体）在当前同步代码之后、下一个宏任务之前清空；await 边界是并发交错点。
5. for await...of 消费 Symbol.asyncIterator，是第 07 章 Stream 与 LLM token 流的统一接口。
6. 取消的答案是 AbortSignal：fetch/流/子进程/SDK 都认它；abort 后以取消类异常 reject。
7. 不 await 的调用已经在跑（fire-and-forget），每个这样的调用点都要能回答"错误去哪了"。

## 源码识别

- 看到 `await` → 想到此处让出线程；await 之后的共享状态可能已被其他任务改过。
- 看到 `void foo()` / 裸调 async 函数 → 想到 fire-and-forget，检查错误是否有 `.catch` 兜底。
- 看到 `Promise.allSettled` → 想到容错并行（tool calls）；`Promise.all` → 想到 fail-fast（必需数据）。
- 看到 `for await (const x of y)` → 想到 y 是 async iterable：Stream / AsyncGenerator / SDK 流式响应。
- 看到 `AbortSignal.timeout(...)` → 想到超时内建化；`AbortSignal.any([...])` → 想到多取消源合并。
- 看到 `options.signal` 层层下传 → 想到取消沿调用链传播，去找最顶层的 controller。
- 看到 `signal.addEventListener("abort", ...)` → 想到取消时的资源清理。
- 看到 `process.nextTick` → 想到 Node 特有的最高优先级微任务。
- 看到 `.unref()` → 想到这个 timer 不阻止进程退出。
- 看到 `new Promise(...)` 手工构造 → 想到在桥接 callback API，或实现 race 型超时。

## Java/Python 工程师常见误区

- 错误认知："async 函数在线程池里执行" → 实际：唯一 JS 线程上分段执行，没有第二个线程。
- 错误认知："Promise 可以 cancel" → 实际：Promise 没有 cancel；取消靠 AbortSignal 协作传播，且只能取消"还在等 I/O"的部分。
- 错误认知："不 await 就不会执行（Python 直觉）" → 实际：JS 调用即执行到第一个 await，请求可能已经发出。
- 错误认知："Promise.all 等所有任务完成" → 实际：fail-fast，一个失败整体立刻 reject，且其余任务不会停；要等全部用 allSettled。
- 错误认知："race 结束后输的那边停了" → 实际：照常跑完，只是结果被丢弃；timer 型输家需要清理。
- 错误认知："未处理的 rejection 会被无声吞掉" → 实际：Node 默认以 unhandledRejection 终止进程（第 14 章）。

## 是否值得深入

- Promise/A+ 规范全文与 thenable 交互细节：当前阶段：不需要深入 —— 语义靠使用内化，规范需要时再查。
- nextTick / queueMicrotask 的优先级规范：当前阶段：不需要深入 —— 记住"nextTick 先于 then"即可。
- async/await 编译成状态机的机制：当前阶段：不需要深入 —— 会读语义就够。
- AbortController API 全集（reason / throwIfAborted / every…）：当前阶段：不需要深入 —— timeout / any / abort 事件覆盖九成场景。
- await 处 microtask 恢复的精确语义：当前阶段：建议掌握 —— 追代码执行顺序的基本功。
- async iterator 协议与手写实现：当前阶段：建议掌握 —— 第 07 章 Stream 与 LLM 流式输出的地基。
