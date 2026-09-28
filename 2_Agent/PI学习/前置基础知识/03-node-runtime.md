# Node.js Runtime：单线程为什么能扛 I/O

你已有的参照系：JVM 跑 Java，CPython 跑 Python。Node.js 的一句话版本：**V8 执行 JS，libuv 提供事件循环与线程池，核心模块提供 fs/http/stream 等标准库**。本章只建立两样东西：runtime 的结构模型，以及一个判断力——看到一段代码，立刻知道它会不会卡住整个进程。microtask 调度顺序、await 语义这些执行细节是第 04 章的事。

## 3.1 Node.js 到底是什么

用 Java 的层次感定位，Node.js 是三样东西的组合：

- **V8**：JS 引擎，解析、JIT、GC 都在里面，Chrome 同款，Node 把它搬出了浏览器。
- **libuv**：C 语言库，提供 Event Loop、线程池、跨平台 OS 抽象（Linux epoll / macOS kqueue / Windows IOCP）。
- **核心模块**：fs / http / stream / crypto / dns / child_process……一个偏 I/O 的超大标准库，相当于不带 Spring 的 JDK。

```
你的 JS 代码
    ↓
Node.js（核心模块: fs / http / stream / ...）
    ↓        ↘
V8（执行 JS）   libuv（Event Loop + 线程池）
    ↓              ↓
        OS（syscall）
```

读源码时这层区分的实际意义：`import { readFile } from "node:fs/promises"` 引入的是 runtime API——不是 JS 语言特性，也不是 npm 包。带 `node:` 前缀的 import 必然指向核心模块；全局对象 `process`、类型 `NodeJS.Timeout` 同样来自 Node 而非语言。V8 与 libuv 的内部实现【暂时跳过】，读源码只需要它们的外部行为。

还有两件小事把这层图固定下来：

- 你安装的"Node.js"是单个可执行文件 `node`，内嵌 V8 与 libuv；`node app.js` 启动的进程本身就是 runtime，没有额外的"虚拟机进程"。
- 语言与 runtime 分开记：`let` / 闭包 / class 这些语言特性在 Chrome 和 Node 通用；`fs`、`process` 这些 API 是 runtime 提供的，不通用——浏览器代码与 Node 代码不能无条件互跑。npm 装的包（含 TS 编译产物）全部落在"你的 JS 代码"那一层，要碰 OS 只能经由核心模块。

## 3.2 "单线程"的准确含义【必须掌握】

准确表述：**任意时刻，只有一个线程在执行你的 JS 代码。**

拆成三层才不误解：

- 你的 JS：单线程，不存在两段 JS 并行执行。所以 JS 层没有 `synchronized`、没有并发容器；但共享可变状态仍会在 await 边界交错（第 04 章），不是完全没有并发问题。
- I/O 本身：不占 JS 线程。网络 I/O 发起非阻塞 syscall 交给 OS，完成后 OS 通知 libuv；没有非阻塞 syscall 可用的操作（磁盘 fs / crypto / dns 解析），交给 libuv 线程池（默认 4 线程）。
- worker_threads / cluster：确实能开多线程/多进程执行 JS，【暂时跳过】，主流 Coding Agent 源码里极少遇到。

用一段最小实验读出"单线程"（它也是 3.5 节阻塞实验的雏形）：

```ts
setTimeout(() => console.log("timer 回调"), 0); // 注册"尽快执行"的回调
const start = Date.now();
while (Date.now() - start < 2000) {
  // 纯 CPU 空转 2 秒
}
// "timer 回调"约 2 秒后才打印：唯一的 JS 线程被 while 占着，回调排不上队
```

不需要懂任何调度细节就能得出结论：回调排队等线程空闲，等不到就都等不到。反过来说，只要没有长同步段，"单线程"对 I/O 并发就不是瓶颈。

同一道题：1000 个并发连接，各等一个 100ms 的网络响应——

| 生态 | 做法 | 成本 |
|---|---|---|
| Java（传统一请求一线程） | 1000 个线程各自阻塞在 socket read | MB 级栈内存 × 1000 + 上下文切换；靠线程池、WebFlux、虚拟线程缓解 |
| Python asyncio | 单线程事件循环，await 让出 | 与 Node 同型 |
| Node | 单线程事件循环 | 与 asyncio 同型，但 async 是语言内建语法 |

虚拟线程补一句定位：Loom 把"阻塞一个廉价线程"的成本降到接近回调，Java 可以不改编程模型就逼近 Node/asyncio 的资源曲线；Node 则从语法层把"用阻塞写 I/O"这条路基本堵死（只剩 Sync API 这几个后门）。殊途同归，但两边代码长相完全不同。

最需要记住的类比与边界：**Node 的模型最接近 Python asyncio**。不等价处：Python 里"用不用 asyncio"是每个项目的选择，同步代码可以一直同步下去；JS 里 async 是传染性语法——底层一个函数 async 化，整条调用链只能跟着 async（这也是 Agent 源码里 `async` 满天飞的直接原因）。

## 3.3 为什么适合 I/O 密集，不适合重 CPU

I/O 密集：每个挂起的连接只是内存里一个待唤醒的回调，等待不占线程。一万个连接在等 I/O，JS 线程照常服务新请求。一次并发的两次文件读大致如此：

```
JS 线程:   [注册读A] [注册读B] [处理其他请求...] ...... [A的回调] [B的回调]
libuv/OS:             [======读A======]  [==读B==]        （两者并行进行）
```

算一笔账看出量级差：10k 个挂起连接，线程模型是 10k × MB 级栈预留加调度器压力，回调模型是 10k 个闭包对象、几 MB 内存。Kafka 消费者、网关、BFF 这类"大部分时间在等下游"的服务，Node 用极低资源持有同样的并发——这就是"扛 I/O"的算术含义。

重 CPU：一段同步 JS 计算（比如对 50MB 文本做 diff）执行期间，唯一的 JS 线程被占住，Event Loop 停转——**所有**连接的回调都排不上队，健康检查一起死。对比三个生态的出路：

- Java：丢线程池（`ExecutorService` / parallelStream）或拆服务。
- Python：丢进程池（multiprocessing）绕开 GIL。
- Node：丢 worker_threads 或子进程；但 Coding Agent 更常见的工程手法是控制粒度——分块 diff、分批 parse，让 Event Loop 在间隙里能转身。

## 3.4 Event Loop 核心模型【必须掌握】

心智模型一句话：**一个循环 + 若干阶段 + 若干队列。**

```
JS Thread（唯一）
   ↓  循环取任务执行到完成
Event Loop（libuv）
   ↓  待 I/O 完成的回调、timers、microtasks
OS / libuv（异步执行 I/O，完成后把回调排入队列）
```

运转过程四步：

1. JS 线程执行当前这批同步代码。遇到异步 I/O 调用（`fetch`、`fs.readFile`），Node 把实际 I/O 交给 OS 或 libuv，注册"完成后执行哪个回调"，然后**立刻返回**继续往下跑。
2. 同步代码执行完，JS 线程空闲，Event Loop 开始转：检查哪些 I/O 完成了、哪些 timer 到点了、microtask 队列里有什么，取出回调执行。
3. 每个回调执行到完成；回调里可能又注册新的异步 I/O。周而复始。
4. 所有队列空了、也没有任何待完成的 I/O/timer，进程退出。（"CLI 脚本没跑完就退出了"十有八九在这一步，第 15 章。）

第 4 步里的"待完成事件"包括：未触达的 timer、未完成的 I/O、打开的 server socket、活跃的子进程。CLI 常见 bug 是忘了关某个句柄，进程就退不出去——系统排查在第 15 章。

关键推论：并发的粒度是**回调**，不是语句。一个回调执行中间不会被别的 JS 打断；交错只发生在回调边界（精确规则第 04 章）。

把循环本身写成概念伪码（只表达结构；阶段与顺序细节属于第 04 章）：

```
while (还有活着的 timer / 挂起的 I/O / 事件监听) {
  取出就绪任务：到期的 timer、完成的 I/O、队列里的回调
  逐个执行到完成（执行中可能注册新的异步 I/O）
}
没有活了 → 进程退出
```

对照 Java 心智：Event Loop 像单线程版 `ScheduledExecutorService` + `Selector`（epoll）的合体，libuv 线程池只对 fs/crypto/dns 这类没有非阻塞 syscall 的操作开放。这个类比帮你定位它，但别延伸——调大 libuv 线程池不会提高你的 JS 并发度，JS 永远单线程。

一个实用推论：Node 里"并发度"没有旋钮——没有 maxThreads、没有 corePoolSize。你唯一要管理的量是"同时挂起的任务数"（比如并发 tool 数上限），那是业务层的信号量，不是线程池参数。

## 3.5 哪些代码会阻塞 Event Loop【必须掌握】

看到以下代码特征要有条件反射：它卡的是全局，不是这一次调用。

- 同步 fs：`fs.readFileSync` / `readdirSync` / `existsSync`。
- 大 `JSON.parse` / `JSON.stringify`：同步且不可增量，几十 MB 的会话历史是重灾区。
- CPU 循环：加密、diff、AST 解析、模板渲染写成同步 JS。
- 正则回溯：catastrophic backtracking，一个坏正则能挂死进程，而且看起来"什么都没干"。
- 大数组同步 sort / 深拷贝（`structuredClone`）：与 JSON.parse 同类的隐藏 CPU 点。

```ts
// agent 启动时加载会话历史
const raw = fs.readFileSync("session.json", "utf8"); // 执行期间全部并发请求冻结
const history = JSON.parse(raw);                     // 再冻一次
```

判断口径：**同步的才阻塞，异步的会让出**——不是"有没有 await"。名字带 `Sync` 的 API 和纯 CPU 计算占住唯一 JS 线程；一个不 await 的异步调用（fire-and-forget）反而让出线程，其语义第 04 章展开。

正则回溯单独说，因为它最隐蔽——代码里只是一行 `test`：

```ts
// 输入稍长就指数级回溯，足以卡住进程数秒甚至更久
const pattern = /^(a+)+$/;
pattern.test("a".repeat(30) + "b");
```

读源码时的工作习惯：看到 Sync 调用先判断数据量级——启动时读一次配置的 `readFileSync` 无伤大雅，读会话历史、依赖树的同步调用就是隐患。阻不阻塞是事实判断，要不要改是量级判断。排查手段一句话：`perf_hooks.monitorEventLoopDelay` 可以监控循环卡顿，知道存在即可，需要时再查。

## 3.6 与 JVM 的对照表

| 维度 | JVM | Node.js |
|---|---|---|
| 执行引擎 | HotSpot，C1/C2 分层 JIT | V8，Ignition 解释器 + TurboFan 优化编译，同样有去优化 |
| GC | G1/ZGC 多种可选、大量可调参数 | V8 分代 + 增量标记，几乎不可调 |
| 并发单元 | 线程（趋势是虚拟线程） | 回调/续体，单线程调度 |
| 内存上限 | 堆可到 TB 级 | 默认堆约 4GB（可调，很少人调） |
| 吃满多核 | 单进程多线程 | 单线程单核，多核靠 cluster / 多进程 |
| 冷启动 | 类加载 + JIT 预热明显 | 毫秒级启动，对 CLI 友好 |

"Node ≈ 带超大标准库的单线程 JVM + 内置事件循环"这个类比：

- 成立的部分：runtime / 引擎 / 标准库的层次感，JIT，GC，"一次编写到处跑"。
- 不成立的部分：JVM 上随手 `new Thread`，Node 没有轻量等价物（worker_threads 通信走序列化，重得多）；JVM 的并发原语（synchronized、并发包、线程池）在 Node 没有对应物——你需要的是队列和状态机，不是锁。性能调优的焦点也不同：JVM 查 GC 停顿 / 锁竞争，Node 九成查"谁阻塞了 Event Loop"。

## 3.7 npm 不是 Node 的一部分

一句话边界：Node 是 runtime，npm 是独立的包管理器——独立项目、独立版本节奏。类比 JVM 与 Maven：总是一起用，但不是一回事。package.json / node_modules / 依赖解析的全部细节在第 00 / 10 章。

读 import 时快速分层：`node:` 前缀 → 核心模块；裸包名 → npm 包；`@scope/name` 或相对/绝对路径 → npm 包或仓库内部模块。分不清层，后面读依赖关系会乱。

## 本章只记住这 5 件事

1. Node = V8（执行 JS）+ libuv（Event Loop + 线程池 + OS 抽象）+ 核心模块（fs/http/stream…）。
2. "单线程"只约束你的 JS；I/O 在 OS（非阻塞 syscall）和 libuv 线程池（fs/crypto/dns）上跑，不占 JS 线程。
3. Node 的并发模型最接近 Python asyncio，但 async 是内建的传染性语法，不是可选库。
4. Event Loop = 一个循环 + 若干阶段 + 若干队列；同步代码和每个回调都执行到完成，队列全空即进程退出。
5. 同步 fs、大 JSON.parse、CPU 循环、正则回溯——这四类卡的是整个进程，不是单次调用。
6. CLI "没跑完就退出 / 退不出去"的答案都在进程生命周期（第 15 章）。
7. Event Loop 像单线程的 ScheduledExecutorService + Selector 合体——类比帮助定位，不能延伸到线程调参。

## 源码识别

- 看到 `node:` 前缀的 import（`node:fs/promises`）→ 想到 Node 核心模块，不是 npm 包。
- 看到 `readFileSync` / `xxxSync` → 想到同步阻塞，Event Loop 热点。
- 看到 `new Worker(...)` / `cluster` → 想到多线程/多进程，暂时跳过不影响读主线。
- 看到 `process.on("SIGINT" / "exit")` → 想到进程生命周期管理（第 15 章）。
- 看到 `setImmediate` / `process.nextTick` → 想到调度原语，语义第 04 章。
- 看到 `child_process` / `spawn` → 想到起子进程跑外部命令，Coding Agent 执行 shell 的标配。
- 看到类型 `NodeJS.Timeout`、全局 `process` → 想到来自 Node runtime，不是语言内置。
- 看到 `structuredClone` / 大数组 `sort` → 想到同步 CPU 型阻塞候选。
- 看到 `perf_hooks` / `monitorEventLoopDelay` → 想到 Event Loop 卡顿的监控埋点。

## Java/Python 工程师常见误区

- 错误认知："Node 单线程，所以 I/O 也是串行的" → 实际：I/O 在 OS/线程池上并行，串行的只是 JS 执行。
- 错误认知："CPU 密集丢给线程池就行" → 实际：libuv 线程池只服务 fs/crypto/dns 等 C 层任务，跑不了你的 JS；JS 层没有随手可用的线程池。
- 错误认知："async 函数会在线程池里执行" → 实际：async 只是可挂起恢复的函数，全程同一个 JS 线程（第 04 章）。
- 错误认知："CompletableFuture 经验可以平移到 Promise" → 实际：形状相似，但 Promise 不能手动 complete、不能 cancel（第 04 章）。
- 错误认知："性能问题先查 GC" → 实际：Node 性能问题九成是"谁阻塞了 Event Loop"，GC 基本不可调也基本不用调。
- 错误认知："Node 只能用一个核，是能力缺陷" → 实际：单进程单核是默认形态；吃多核靠 cluster / 多进程，是架构选择，不是能力缺失。

## 是否值得深入

- Event Loop 各阶段（timers/poll/check/close…）逐阶段规范：当前阶段：不需要深入 —— 排查调度顺序问题时再查文档。
- libuv 的 C 实现与 epoll/kqueue 细节：当前阶段：不需要深入 —— "OS 完成后通知"这层抽象足够读源码。
- worker_threads / cluster：当前阶段：不需要深入 —— 主流 Coding Agent 项目极少用，遇到再查。
- V8 JIT / GC 内部机制：当前阶段：不需要深入 —— 与读源码无关。
- npm 与 Node 的版本兼容矩阵：当前阶段：不需要深入 —— 记住二者是独立项目即可。
- "什么代码阻塞 Event Loop"的判断力：当前阶段：建议掌握 —— Node 性能问题的第一现场。
