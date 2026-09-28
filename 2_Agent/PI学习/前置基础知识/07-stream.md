# Stream：流式处理的心脏（重点章）

读 AI Coding Agent 的源码，你会在两条线上反复撞见 Stream：

- 向内：LLM API 的响应是 SSE 字节流，token 一段一段到达；
- 向外：终端渲染逐字符输出，bash 工具的子进程输出逐块收集。

Java 里你用过 `InputStream`/`BufferedReader`，Python 里用过 generator 惰性产出。Node Stream 解决的是同类问题，但模型是异步事件驱动 + 管道组合，且内置背压。本章建立的心智模型覆盖后面所有章节：HTTP 服务、终端渲染、子进程、日志管线。

## 7.1 Stream 为什么存在【必须掌握】

一句话：解决"数据大于内存 / 生产与消费速率不同"的问题。拆开是三件事：

| 动机 | 不用流的后果 | 流的做法 |
|---|---|---|
| 内存 | 3GB 日志 `readFile` 一次性载入，堆直接爆 | 一次只持有 64KB 级别的 chunk |
| 时间 | 等整个响应生成完才有第一个字 | 生产一块处理一块，首字节延迟毫秒级 |
| 组合 | 解压/解析/过滤全挤在同一个循环里 | 管道拼接，每段独立、可复用、可测试 |

对应你熟悉的东西：`BufferedReader.readLine()` 逐行读解决的是内存问题；Reactive Streams（Project Reactor / RxJava）解决的是时间 + 组合问题。Node Stream 两者都管，只是没有算子糖，组合靠 pipe。

一个具体 trace：把 3GB 的构建日志发给一个转码服务。非流式做法是 `readFile` 3GB 进堆（大概率 OOM），转码完再一次性发；流式做法是读 64KB、发 64KB，两头同时推进，内存峰值几十 KB，且第一毫秒数据就已经在链路上。三个动机（内存/时间/组合）在这一条链路里同时兑现。

## 7.2 统一心智模型：逐步到达的数据天然是流【必须掌握】

下面五样东西，在 Node 里全是流，没有例外：

| 场景 | 为什么天然是流 |
|---|---|
| LLM Streaming | token 由模型逐个生成、经网络逐段到达，天然"一块一块" |
| Terminal 渲染 | 打字机效果 = 收到一段渲染一段 |
| HTTP 响应 | chunked transfer encoding 就是"边生成边发"的传输层表达 |
| 大文件复制 | 3GB 文件不可能也不需要整体进内存 |
| 子进程 stdout | `git diff` 的输出由另一个进程逐步产生 |

```
生产端（慢/快） →  [chunk][chunk][chunk]  → 消费端（快/慢）
```

这张图是本章唯一的"总图"。注意方向上的速率差：LLM 生成慢、终端渲染快；磁盘读得快、网络写得慢。流的存在让两端不必同步——中间靠 chunk 缓冲 + 背压（见 7.7）协调。

## 7.3 四种流【必须掌握】

```
   Readable ──────► Transform ──────► Writable
   （源头）        （边流边加工）      （归宿）

   Duplex：读写两端同体的双向通道（两端独立，不是 Transform）
```

| 类型 | 一句定位 | 真实对应物 |
|---|---|---|
| Readable | 数据的源头 | `fs.createReadStream`、LLM token 流、`process.stdin` |
| Writable | 数据的归宿 | HTTP 响应、`process.stdout`、`fs.createWriteStream` |
| Duplex | 可读可写、两端独立 | WebSocket、子进程 stdio（stdin 可写 + stdout 可读） |
| Transform | 读进来的加工后写出，一进一出 | gzip、逐行切分、SSE 解析器 |

记忆锚点：Transform 是"读和写同一件事的两面"（输入决定输出），Duplex 是"两条独立的通道绑在一个对象上"（WebSocket 收发互不决定）。

读源码时的判断方法：看构造函数和用途而非类型名。`new Transform({...})`、内部 `push` 加工结果的是 Transform；`spawn()` 返回对象上的 `stdin`/`stdout` 各自是独立单流向流（合起来才是 Duplex 语义）；`net.Socket`（TCP 连接）是教科书 Duplex。另外，四种流全部继承自 EventEmitter——所有流都能 `on("error")`，这是它们行为一致性的来源。

## 7.4 chunk：流的基本单位【必须掌握】

chunk 是流的一次搬运量。默认是 Buffer（字节），不保证任何语义边界：

- 一个 chunk 可能是半行、半个 UTF-8 多字节字符、半帧 SSE 报文；
- 按"行"或"帧"处理必须自己拼接残余（见 7.8 的 Transform 示例），或用 `string_decoder` 处理跨 chunk 的多字节字符；
- 文件流默认 64KB 左右一块（`highWaterMark`，知道即可）。

### objectMode：让 chunk 变成任意对象

默认 chunk 是字节，但管线里更常见的形态是"对象流"：LLM 事件流、日志解析管线。开 `objectMode` 后 chunk 可以是对象/字符串/数字，跳过序列化：

```ts
import { Readable, Transform } from "node:stream";

// 每个 chunk 是一个事件对象，不是 Buffer
const events = Readable.from([
  { type: "text_delta", text: "hello" },
  { type: "text_delta", text: " world" },
  { type: "message_stop" },
]);

const toText = new Transform({
  writableObjectMode: true, // 输入端收对象
  transform(ev: { type: string; text?: string }, _enc, cb) {
    if (ev.type === "text_delta") this.push(ev.text);
    cb();
  },
});

for await (const s of events.pipe(toText)) process.stdout.write(String(s));
```

`writableObjectMode` / `readableObjectMode` 分别控制两端，Transform 两端可以一端对象一端字节——SSE 解析器正是如此：字节进、对象出。

## 7.5 消费流的两种方式【必须掌握】

### 方式一：事件式（老风格）

```ts
import { createReadStream } from "node:fs";

const rs = createReadStream("app.log");
const lines: string[] = [];
rs.on("data", (chunk: Buffer) => lines.push(...chunk.toString().split("\n")));
rs.on("end", () => console.log("done"));
rs.on("error", (err) => console.error(err));
```

一旦监听 `"data"`，流进入 flowing mode：数据主动推给回调，不等你。这是 2014 年的风格，问题在于暂停/恢复、错误、资源清理全靠手工，容易泄漏。读老代码、写底层库时会见到；业务代码不用。

低频事件一句话带过：`"readable"`（有数据可拉，paused mode 的拉取入口）、`"close"`（底层资源关闭）、`"finish"`（Writable 全部写完并 flush）、`writable.end()`（写完并关闭，对应 Java 的 `close`，但异步）。`setEncoding("utf8")` 可以让 chunk 直接以 string 出现，但边界问题依旧存在。

### 方式二：迭代式（现代首选）

```ts
import { createReadStream } from "node:fs";

// 1) 读文件：内存里永远只有 64KB
let bytes = 0;
for await (const chunk of createReadStream("app.log")) {
  bytes += (chunk as Buffer).length;
}

// 2) 消费 LLM token 流（SDK 的 stream 对象同样是 async iterable）
const stream = await client.messages.create({ stream: true });
for await (const event of stream) {
  if (event.type === "content_block_delta") process.stdout.write(event.delta.text);
}
```

`for await` 为什么能直接用于流？因为 `Readable` 实现了 `Symbol.asyncIterator`（第 04 章讲过 async iterator 协议）。这行代码背后 Node 替你做了三件事：

1. 自动管理 paused/flowing 状态：你消费得动就继续推，消费不动就暂停；
2. 自动背压：循环体里的 `await` 没返回前不会再取下一个 chunk；
3. 流结束（`end`）时循环正常退出，出错时在 `await` 处抛异常，天然适配 try/catch。

对照 Java：这相当于 `BufferedReader.lines()` 的流式语义，但循环体里可以 `await` 任意异步操作而不会卡死事件循环。对照 Python：相当于 `async for chunk in aiter`，但标准库的流全部实现了它。

一句话结论：新代码一律 `for await`，事件式只在读老源码和处理 `stderr` 这类"伴生流"时出现。

| | 事件式 `on("data")` | 迭代式 `for await` |
|---|---|---|
| 状态管理 | 手工（flowing 抢占） | 自动（迭代协议接管） |
| 背压 | 忘了 `pause()` 就失效 | 循环体 await 即天然反压 |
| 错误 | 单独 `on("error")`，漏了就未捕获异常 | try/catch 包住循环即可 |
| 适合场景 | 伴生流（如 stderr）、老源码 | 一切新代码 |

## 7.6 pipe 与 pipeline【必须掌握】

`readable.pipe(writable)` 把两个流接起来：Readable 的 chunk 自动 `write` 进 Writable，返回 Writable 自身，可以链式接：

```ts
import { createReadStream, createWriteStream } from "node:fs";
import { createGzip } from "node:zlib";

// 大文件 gzip：三个流拼一条管线，全程只占几十 KB 内存
createReadStream("app.log")
  .pipe(createGzip())        // Transform 做中间站
  .pipe(createWriteStream("app.log.gz"));
```

pipe 内部不只是转发，还自动做背压。机制（概念级）：

```
Readable ──pipe──> Writable
   ↑____暂停读____| write() 返回 false（Writable 内部缓冲区到水位线）
```

1. pipe 循环里每个 chunk 调 `writable.write(chunk)`；
2. Writable 内部缓冲区超过水位线时 `write()` 返回 `false`；
3. pipe 收到 `false` 就暂停 Readable（不再读源头）；
4. Writable 排空后触发 `"drain"` 事件，pipe 恢复读。

错误处理一句话：`pipe` 不传播错误——中间某段出错，其他段挂着不关；`stream.pipeline()` 会把整条管线一起清理并把错误抛给回调/Promise（细节第 14 章）。新代码用 pipeline：

```ts
import { pipeline } from "node:stream/promises";
import { createReadStream, createWriteStream } from "node:fs";
import { createGzip } from "node:zlib";

try {
  await pipeline(
    createReadStream("app.log"),
    createGzip(),
    createWriteStream("app.log.gz"),
  ); // 全部写完（触发了 "finish"）才 resolve
} catch (err) {
  // 任意一段出错：整条管线销毁，这里拿到第一个错误
}
```

## 7.7 backpressure：概念级理解【必须掌握】

为什么不能"读得快写得慢不管它"？因为 Writable 的 `write()` 永远同步返回、从不拒绝：没人刹车的话，来不及写出的数据全部堆在 Writable 的内部缓冲区里，3GB 文件就是把 3GB 堆进内存。背压就是这条刹车链：`write() === false` → 暂停读 → `"drain"` 恢复。

一条 trace 看清两种写法的差别（磁盘 500MB/s，网络 5MB/s）：

```
手工循环（无背压）:
  disk → [chunk] → ws.write(chunk) 返回 false，但循环不停
  → 99% 的数据堆在 Writable 缓冲区 → 堆内存涨到 GB 级

pipe / for await（有背压）:
  ws.write(chunk) 返回 false → Readable 暂停读磁盘
  → "drain" 后恢复 → 内存稳定在水位线附近
```

反过来看 `for await`：循环体里 `await` 的微任务没 resolve，迭代器就不取下一个 chunk，Readable 就停在 paused——背压沿调用链反向传导。在 agent 里这意味着：终端渲染慢，压力会一路传回 HTTP 响应流，SDK 甚至会因此暂停向服务端 confirm（取决于协议），而不是无脑缓冲。

与已知体系对照（这是本章最重要的类比，注意"相似但不等价"）：

| 体系 | 背压形态 | 与 Node 的差异 |
|---|---|---|
| Java InputStream | 无背压概念。读不到就阻塞，阻塞本身就是节流 | 同步阻塞换来的隐式节流；经典坑是子进程 stdout 管道缓冲区满、父进程不读导致子进程卡死（第 09 章会再遇到） |
| Reactive Streams（Reactor/RxJava） | 语义相同：下游 `request(n)` 信号量拉取 | 机制不同：显式的 demand 计数契约（`Subscription.request`）；Node 用 `write() 返回 false + drain` 表达同一件事 |
| Python file-like/generator | 无标准背压，`read()` 阻塞或 `yield` 挂起 | asyncio 里靠队列/信号量自己搭 |

Node stream 的整体模型是"消费者拉取为主、事件推动为辅"的混合：paused mode 下 `read()` 拉取，flowing mode 下事件推送，二者按消费方式自动切换。切换与内部状态机的实现细节【暂时跳过】，概念层面知道"消费速度自动反压生产速度"即可。

## 7.8 Transform：手写一个（源码高频形态）【必须掌握】

源码里最常见的特征是 `new Transform({ transform(chunk, enc, callback) {...} })`。契约：每个 chunk 进 `transform`，加工完用 `this.push()` 往下推（可推 0 到多个），调 `callback()` 表示"这个 chunk 处理完了"。手写一个把字节流切成行：

```ts
import { Transform } from "node:stream";

function createLineSplitter() {
  let tail = ""; // 上一个 chunk 末尾的不完整行
  return new Transform({
    readableObjectMode: true, // 往下游传 string 行，不是 Buffer
    transform(chunk: Buffer, _enc, cb) {
      tail += chunk.toString("utf8");
      const lines = tail.split("\n");
      tail = lines.pop() ?? ""; // 最后一段可能不完整，留到下个 chunk
      for (const line of lines) this.push(line);
      cb();
    },
    final(cb) {
      if (tail) this.push(tail); // 流结束时冲出残余
      cb();
    },
  });
}

for await (const line of createReadStream("app.log").pipe(createLineSplitter())) {
  if (line.includes("ERROR")) console.log(line);
}
```

两个要点：跨 chunk 拼接（换行符可能落在 chunk 中间）与 `final` 冲尾（流结束时没有换行符的最后一行）。所有"按行/按帧"的解析器——包括 SSE 解析器——都是这个形状。

## 7.9 自定义 Readable【看懂即可】

两种写法，读源码能认出即可：

```ts
import { Readable } from "node:stream";

// 写法一：Readable.from，把（同步或异步）可迭代对象变成流
const tokenStream = Readable.from(["const ", "x ", "= ", "42;"]);

// 写法二：手写 read()——被需要数据时回调，push 数据或 null（结束）
const replay = new Readable({
  read() {
    for (const t of ["const ", "x ", "= ", "42;"]) this.push(t);
    this.push(null); // null = 流结束
  },
});
```

`Readable.from` 内部就是写法二的封装。测试里"把 mock 数组喂给消费流的代码"靠它；另外 `Readable.fromWeb(res.body)` 用于把 fetch 的 Web ReadableStream 转成 Node 流（两套标准 API 的桥，见 7.10）。

还要认得第三种形态：async generator。它是"自产流"的最短写法，而且 `pipeline()` 和 `for await` 都直接接受 async iterable，不要求真是 Readable：

```ts
// 把轮询 LLM 的重试逻辑包成"流"：调用方用 for await 消费，毫无区别
async function* pollJob(jobId: string): AsyncGenerator<JobEvent> {
  while (true) {
    const ev = await getEvent(jobId);
    if (!ev) break;
    yield ev; // 每次调用 next() 才会走到这里——惰性 + 天然背压
  }
}

for await (const ev of pollJob("job_42")) render(ev);
```

读源码时会看到 LLM SDK、agent 内核大量用 async generator 而不是裸 Readable——语义上是同一种东西（异步 chunk 序列），实现更轻。判断标准：消费端代码长什么样（`for await`），而不是生产端是什么类型。

## 7.10 对照表：Node Stream vs 你已熟悉的东西

| 维度 | Node Stream | Java InputStream/OutputStream | Reactive Streams | Python file-like/generator |
|---|---|---|---|---|
| 语义 | 异步 chunk 序列 | 同步阻塞 pull | 异步 push + 背压信号 | 同步迭代 |
| 背压 | `write()` false / drain | 无（靠阻塞隐式节流） | `request(n)` 信号量 | 无标准背压 |
| 组合 | pipe / pipeline | 手写循环 copy | map/flatMap 等算子 | 手写 for / yield |
| 错误传播 | pipeline 传播，pipe 不 | 异常抛出 | onError 信号 | 异常抛出 |

HTTP chunked transfer encoding 一句话：它是传输层对"边生成边发"的编码表达，Node 把它直接暴露成 `res` 上的流，所以服务端"流式响应"在代码里就是往一个 Writable 里 write。

另外注意 Node 里有两套流 API：`node:stream`（本章）与 Web 标准 `ReadableStream`（fetch body、`TransformStream`）。语义同源，接口不同，靠 `Readable.fromWeb()` / `Readable.toWeb()` 互转。读源码时先分清是哪套。

## 7.11 高频陷阱【必须掌握】

1. `on("data")` 与 `for await` 不要混用。`"data"` 监听会把流切到 flowing mode，数据直接推给回调；async iterator 也在内部等数据。两者同时存在就是抢数据：迭代器拿到空数据、丢 chunk、或行为不可预测。一条流只用一种消费方式：

```ts
// 反面教材：看起来各取所需，实际输出随机丢 chunk
rs.on("data", (c) => count += c.length);
for await (const c of rs) process.stdout.write(c); // 拿到的可能只剩部分
```
2. 未消费的流会卡在内存。`createReadStream` 建了不读也不销毁 → 文件句柄滞留；fetch 的 body 不读完/不取消 → 连接无法回池。见到"创建后按条件才读"的代码要留意 `destroy()`。
3. 手写 `write` 循环必须处理 drain。`write()` 返回 `false` 后继续写 = 背压失效、内存膨胀。正确写法：

```ts
import { once } from "node:events";
if (!ws.write(chunk)) await once(ws, "drain"); // 等排空再写下一个
```

4. `process.stdout` 也是 Writable。这是 CLI 流式渲染的根基：agent 往终端打 token 就是往这个 Writable 写。注意当 stdout 接管道/文件时它是异步的，写入不完全同步落盘，EPIPE 错误要处理。

## 7.12 在 Coding Agent 中：token 流 → SSE 解析 → 终端渲染

真实的渲染层骨架（开源 coding agent 的通用形状）：

```ts
import { Transform, Writable } from "node:stream";
import { pipeline } from "node:stream/promises";

type StreamEvent = { type: string; delta?: { text?: string } };

// Transform：SSE 字节进，事件对象出（objectMode 只开读端）
class SSEParser extends Transform {
  private buf = "";
  constructor() {
    super({ readableObjectMode: true });
  }
  override _transform(chunk: Buffer, _enc: string, cb: () => void) {
    this.buf += chunk.toString("utf8");
    let i: number;
    while ((i = this.buf.indexOf("\n\n")) >= 0) { // SSE 事件以空行分帧
      const frame = this.buf.slice(0, i);
      this.buf = this.buf.slice(i + 2);
      const line = frame.split("\n").find((l) => l.startsWith("data: "));
      if (line) this.push(JSON.parse(line.slice(6))); // 事件对象往下推
    }
    cb();
  }
}

// Writable：终端逐段渲染（对象进、字节出 → writableObjectMode）
const renderer = new Writable({
  writableObjectMode: true,
  write(ev: StreamEvent, _enc, cb) {
    if (ev.type === "content_block_delta") process.stdout.write(ev.delta?.text ?? "");
    cb();
  },
});

// 组装：HTTP 响应体(Readable) → SSEParser(Transform) → renderer(Writable)
const res = await client.post("/v1/messages", { stream: true });
await pipeline(Readable.fromWeb(res.body), new SSEParser(), renderer);
```

逐层对应：`Readable.fromWeb(res.body)` 解决"token 逐步到达"；`SSEParser` 是 7.8 的按帧切分 + objectMode；`renderer` 往 `process.stdout` 写。整条管线任何一段慢下来，背压会一路传回 HTTP 层——这就是 agent 终端打字机效果的全部原理。读懂这 30 行，等于读懂了渲染层。

## 本章只记住这 5 件事

1. 流解决"数据大于内存 / 生产消费速率不同"：内存、时间、组合三收益。
2. LLM token、终端、HTTP chunked、大文件、子进程 stdout 天然全是流，心智模型统一为 `生产端 → [chunk] → 消费端`。
3. 四种流：Readable 源、Writable 汇、Duplex 双向独立、Transform 边流边加工。
4. 消费首选 `for await`（Readable 实现了 async iterator，自动管 paused/flowing 与背压）；组装首选 `pipeline`（pipe 不传播错误）。
5. 背压 = `write()` 返回 false 时暂停读、drain 后恢复；对照 Reactor 的 `request(n)`，语义相同、机制不同。
6. `objectMode` 让 chunk 变对象，是 LLM 事件流和日志管线的常规形态。

## 源码识别

- 看到 `for await (const chunk of ...)` → 想到 Readable 实现了 async iterator，且消费循环自带背压。
- 看到 `new Transform({ transform(chunk, enc, cb) })` → 想到"字节/对象进、加工出"，跨 chunk 拼接要看 `tail` 变量。
- 看到 `pipeline(a, b, c)`（`node:stream/promises`）→ 想到多级流组装 + 统一错误传播。
- 看到 `objectMode: true` / `readableObjectMode` → 想到 chunk 是对象，多半是 LLM 事件或解析产物。
- 看到 `Readable.from(...)` → 想到把数组/async iterable 变流（测试 mock 高频）。
- 看到 `Readable.fromWeb(...)` → 想到 fetch body（Web 流）转 Node 流的桥。
- 看到 `on("data", ...)` → 想到老式 flowing mode，检查是否与迭代混用、是否处理了 error/end。
- 看到 `if (!ws.write(chunk)) await once(ws, "drain")` → 想到手写背压的正确姿势。
- 看到 `process.stdout.write(...)` → 想到终端渲染就是往 Writable 写，CLI 流式输出的根基。
- 看到 `highWaterMark` → 想到流的水位线，只在调优/截断逻辑里出现。

## Java/Python 工程师常见误区

- 错误认知："Stream 相当于 Java InputStream，读就行" → 实际是异步事件对象，有状态机（paused/flowing）和背压契约；用同步思维写会丢数据或爆内存。
- 错误认知："for await 只是 on('data') 的语法糖" → 实际是独立的消费协议，接管了状态管理与背压，与事件监听互斥，不是糖。
- 错误认知："pipe 之后错误会被外层 catch 到" → 实际 pipe 不传播错误，出错段之外的流不会被清理；要错误传播必须用 pipeline。
- 错误认知："chunk 边界有语义（一行/一条消息）" → 实际 chunk 只是字节块，边界任意；按行/帧处理必须自己拼接残余。
- 错误认知："背压是 Reactive 生态的概念，Node 没有" → 实际 Node stream 内置背压（write false / drain），只是没有 request(n) 这种显式信号。
- 错误认知："objectMode 是特殊场景" → 实际 agent/日志管线里对象流比字节流更常见，Transform 一端字节一端对象是标配。

## 是否值得深入

- 四种流与 for await 消费：当前阶段：建议掌握 —— 读任何 agent 源码的入场券。
- 手写 Transform（切行/切帧）：当前阶段：建议掌握 —— SSE 解析、输出过滤都是这个形状。
- pipe 与 pipeline 的背压机制（概念级）：当前阶段：建议掌握 —— 解释"为什么不会内存膨胀"全靠它。
- Web Streams 标准（ReadableStream/TransformStream）：当前阶段：不需要深入 —— 认得 fetch body 是它、会用 fromWeb 桥接即可。
- stream 内部实现（read/write 状态机、highWaterMark 调优）：当前阶段：不需要深入 —— 写流库的人才需要，读源码用不到。
