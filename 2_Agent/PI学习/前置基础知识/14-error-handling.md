# 错误处理：throw、rejection 与进程级兜底

Java 给过你两重保障：checked exception 把"会抛什么"写进签名，线程模型给每个线程留了默认兜底。TS/JS 把这两样全拿走：异常全是 unchecked、签名不声明抛出、错误有两条传播通道（同步 throw 与异步 rejection）、进程级 handler 是最后一道防线。第 04 章反复推迟的错误问题在这里一次讲完，最后落到 agent 的错误分层——哪些错误该变成回传 LLM 的信息，哪些该 retry，哪些该让进程死。Python 工程师对"无 checked"不陌生，但两条通道与进程默认崩溃策略仍需专门立牌。

## 14.1 throw 与 try/catch/finally：全是 unchecked【必须掌握】

语法上 throw 任意值都合法（`throw "oops"`、`throw { code: 1 }`），但**约定永远 throw Error 实例**：message、stack、cause 全挂在 Error 上，throw 字符串会丢调用栈、catch 里也无法收窄类型。

try/catch/finally 的形状与 Java 相同，差异在 catch 没有类型参数——strict 模式下 `catch (err)` 推断为 `unknown`，必须收窄后才能用；不能写 `catch (e: IOException)` 这种声明：

```ts
function parseConfig(raw: string): Config {
  if (!raw) throw new ConfigError("empty config"); // throw Error 子类：约定
}

try {
  const cfg = parseConfig(raw);
} catch (err) {                    // err: unknown，无类型参数
  if (err instanceof ConfigError) logger.warn(err.message); // 收窄后使用
  throw err;                       // 不认识的错误原样上抛：处理不了就别吞
} finally {
  await tmpFile.delete();          // 清理语义与 Java 同
}
```

核心缺失：**没有 checked exception**。`function readConfig(path: string): Promise<Config>` 完全看不出会抛 ENOENT 还是 JSON 解析错误——函数类型与抛出行为无关。Java 里 `throws IOException` 是 API 契约的一部分；TS 里这个契约不存在，读源码判断"会抛什么"只有三条路：看实现、看文档/JSDoc、看代码里定义了哪些自定义 Error 类。Python 同样无 checked，这半边经验可直接平移；代价是错误处理纪律完全靠约定与 lint，不靠编译器。

## 14.2 Error 对象与 cause 链【必须掌握】

Error 的三个核心属性：`message`（给人读的描述）、`name`（默认类名，可覆盖，见 14.5）、`stack`（创建时刻的调用栈字符串，非规范标准但全平台可用）。

包装错误的标准姿势是 cause 链（ES2022 起）：

```ts
try {
  return JSON.parse(await fs.readFile("agents.json", "utf8"));
} catch (err) {
  throw new Error("failed to load agent config", { cause: err });
  // 日志里能看到两层：包装层给上下文，cause 保留 ENOENT / SyntaxError 的现场与栈
}
```

对照 Java：`new RuntimeException("failed to load agent config", e)` 的 cause 完全同构——跨层边界包装时底层细节不能断链。JS 的 suppressed（try-with-resources 的对应物）几乎无人使用，知道存在即可，需要时再查。

一个日志坑：`JSON.stringify(err)` 输出 `{}`——message、stack、cause 都不是可枚举属性，一个字段都进不了 JSON，结构化日志要用序列化工具或手工取字段；`console.log(err)` 在新版 Node 会连 cause 一起打。

## 14.3 同步 throw 与异步 rejection：同一错误的两种形态【必须掌握】

规则一句话：**同步函数里的 throw 沿调用栈立刻上抛；async 函数里的 throw 变成所返回 Promise 的 rejection**。同一个 throw 关键字，两条通道。try/catch 只护得住两条路：当前调用栈内的同步 throw，以及 await 中的 rejection。

```ts
function readSync(path: string): Config {
  throw new Error(`bad config: ${path}`); // 形态一：沿调用栈立刻上抛
}
async function readAsync(path: string): Promise<Config> {
  throw new Error(`bad config: ${path}`); // 形态二：变成 Promise 的 rejection
}

try { readSync("a.json"); } catch (e) { /* 捕得到 */ }
try { readAsync("a.json"); } catch (e) { /* 捕不到：catch 块在 rejection 发生前已执行完 */ }
readAsync("a.json");                       // 忘了 await：rejection 飞走，落点在 14.4
```

第三行的 catch 捕不到任何东西：`readAsync("a.json")` 只是创建了一个 rejected Promise，没有人 await 它、也没有 `.catch`——这个 rejection **不会就地爆炸，而是飞走**，直到进程级兜底（14.4）才现身。对照 Java：RuntimeException 不管同步异步都沿栈上抛（Future 的异常要 `get()` 时才包装成 ExecutionException 交给调用方）；JS 的分界线是"此刻是否在 await 中"。

顺带接上第 06/07 章的第三条通道：EventEmitter 的 `'error'` 事件无人监听会立刻崩进程，Stream 错误经 `pipeline` 抛给回调/Promise。读源码时把三条通道分开认：同步栈、rejection、error 事件。

## 14.4 unhandledRejection 与 uncaughtException：进程级兜底【必须掌握】

两个事实先立住：

- 现代 Node（15+）对未处理 rejection 的默认行为是**崩溃退出**，不是旧版的打印警告。带着"未 catch 的 rejection 只会刷屏"的旧印象读代码会误判严重性。
- `process.on("unhandledRejection")` 与 `process.on("uncaughtException")` 是最后防线，只做记录与退出，不是控制流的一部分。

```ts
process.on("unhandledRejection", (reason: unknown) => {
  log.fatal({ err: reason }, "unhandled rejection");
  process.exitCode = 1; // 让事件循环排空后退出（exitCode 与 exit 的区别见第 15 章）
});

process.on("uncaughtException", (err: Error) => {
  log.fatal({ err }, "uncaught exception; state unreliable, exiting");
  process.exit(1); // 这里必须硬退：异常可能打断了任意两行代码，不知道什么不变量已被破坏
});
```

uncaughtException 之后进程状态不可信——这点与 JVM 有实质差别：`Thread.setDefaultUncaughtExceptionHandler` 处理完，其他线程照常服务，JVM 活着；Node 只有一个 JS 线程，异常发生意味着"所有请求的公共执行流"断在半截，没有"其他线程"接管，正确动作是记录后尽快退出。

预防优先于兜底：每个 fire-and-forget 调用点挂 `.catch`（第 04 章）。兜底 handler 是保险丝——日志里频繁出现 unhandledRejection 本身就是 bug 信号，不是正常运维噪声。

## 14.5 自定义 Error 与 instanceof 的双实例陷阱【必须掌握】

```ts
class ToolError extends Error {
  readonly tool: string;
  constructor(tool: string, message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "ToolError"; // 字符串判据：instanceof 之外的第二条路（见下）
    this.tool = tool;
  }
}

try {
  await runTool(call);
} catch (err) {
  if (err instanceof ToolError) return toolResult(err); // 常规用法：收窄 + 分支
  throw err;
}
```

老代码里常见的 `Object.setPrototypeOf(this, ToolError.prototype)`，是编译 target 低于 ES2022 时 extends 的 prototype 链被破坏、instanceof 失效的历史修补，认得即可；现代 target 下不需要。

真正的坑是**双实例陷阱**：monorepo 里同一个包出现两个版本、或一个包同时存在 ESM 与 CJS 双格式副本（dual package），内存里就会有同一个 Error 类的两份。一边 throw 的实例用另一边的类做 instanceof 结果是 false——错误被当成"未知错误"走错分支。Java 的近亲：两个类加载器加载同名类，`instanceof` 与强转都失败，`ClassCastException` 的经典成因跨了运行时来到 JS。

所以很多库不用 instanceof 做判据，改用字符串字段：Node 自家的 fs 错误从来用 `error.code` 判别（从不用类），AbortError 用 `error.name`。读源码看到 `err.code === "..."` / `err.name === "..."`，第一反应就是"作者在防双实例"。

## 14.6 error.code 与常见错误形态【看懂即可】

Node 系统错误自带结构化字段：`code`（ENOENT / EACCES / EBUSY…）、`errno`、`syscall`、`path`。判 code，永远别匹配 message 文案（不稳定、可能本地化）。高频形态速查：

| 形态 | 判据 | 来源与含义 |
|---|---|---|
| ENOENT | `err.code === "ENOENT"` | 文件不存在；spawn 找不到可执行文件（第 09 章 `on("error")`） |
| EACCES / EPERM | `err.code` | 权限拒绝 |
| AbortError | `err.name === "AbortError"` | `AbortController.abort()` 后 fetch / SDK / 子进程 signal 的 rejection（第 04 章） |
| TimeoutError | `err.name === "TimeoutError"` | `AbortSignal.timeout` 触发的取消原因 |
| HTTP 429 / 5xx | 响应 status（多数 SDK 包成带 status 的错误类） | 限流 / 上游故障：可重试 |
| HTTP 400 / 401 | 响应 status | 请求本身错：重试无意义 |

fetch 的一个语义陷阱：非 2xx **不抛异常**，必须手动检查响应，否则静默把错误页当成功数据用：

```ts
const res = await fetch(url, { signal });
if (!res.ok) throw new ApiError(res.status, await res.text()); // 对照 requests.raise_for_status
```

超时错误的形态归入取消类：`AbortSignal.timeout` 触发的 rejection 名为 TimeoutError，与用户主动 abort 的 AbortError 同族——第 04 章的结论是靠 `signal.aborted` 区分来源，而不是硬编码 name 分支。

## 14.7 Promise.all 与 allSettled：异步错误的组合【必须掌握】

两个组合子的语义、示例与 Java/Python 对照（allOf / gather(return_exceptions=True)）见第 04 章，这里只补错误处理侧的两个细节：

- all 的 fail-fast 只是"不等了"：其余任务**不会被取消**，还在后台继续跑。要真正止损，把同一个 AbortSignal 传给所有分支（第 04 章）。
- allSettled 的 `r.reason` 在类型系统里是 `any`——错误分类不能靠类型收窄，回到 14.5 的判据（`name` / `code` 字段）做。"失败转错误消息回给模型、不连坐"的完整写法即第 04 章的 Parallel Tool Calls 示例。

## 14.8 Agent 的错误分层【必须掌握】

先给分层图，四条来源各自的路数：

```
Ctrl+C / 超时  ──→ AbortError ──────────→ 停止当前 turn：不重试、不当 crash，安静收尾
LLM API        ──→ 429/5xx/断流 ───────→ 分类：可重试（退避重试）/ 不可重试（上抛）
Tool 执行      ──→ 任何失败 ──────────→ 转成 tool_result（is_error）回传 LLM，模型自行调整
子进程         ──→ ENOENT/非零退出/信号 ─→ 同上：作为业务信息回传，不中断进程
最后防线       ──→ unhandledRejection/uncaughtException ─→ 记录 + 退出（14.4）
```

一条总原则：**离模型越近的错误越要"变成信息"，离基础设施越近的错误越要"变成故障"**。bash 跑挂了是 agent 的正常业务流——模型看到报错会自己改命令；API key 失效、内存耗尽是基础设施故障，重试与"转告模型"都无意义，该 crash 让守护层报警。

**Tool error：错误即信息**。工具失败不让进程 crash、也不向上 throw，而是把错误文本作为 tool result 返回，让模型下一轮自行调整（测试失败→改代码；命令不存在→换命令）：

```ts
async function runToolSafe(call: ToolCall): Promise<ToolResult> {
  try {
    const r = await runBash(call.input.command);        // 第 09 章的 bash 骨架
    return { type: "tool_result", tool_use_id: call.id, content: r.stdout };
  } catch (err) {
    return {
      type: "tool_result",
      tool_use_id: call.id,
      is_error: true,                                   // 标记失败，内容仍是错误文本
      content: `error: ${err instanceof Error ? err.message : String(err)}`,
    }; // 不 throw：模型看得到失败原因，agent 进程继续活着
  }
}
```

**LLM / API error：按可重试性分类**。429（限流，尊重 retry-after，指数退避）、5xx / 超时 / 连接重置 / 断流（可重试，流式场景要能从半截输出恢复）；400 / 401 / 上下文超长（不可重试——重试只是再烧一次同样的失败）。SDK 包装的异常类各异，但 status 判据是稳定的。

**subprocess error：三种形态**（全部第 09 章）：spawn 本身失败（`on("error")`，`err.code === "ENOENT"`，命令不存在——回传模型让它换命令）；非零退出（`code !== 0`，业务信息，不是异常）；被信号杀死（`code === null` + signal，超时/取消的下游表现）。

**timeout / cancellation：识别与传播**。AbortError（及 TimeoutError）识别后**向上传播而不是消化**：取消意味着用户改变了意图，重试逻辑必须让路——对取消类错误做退避重试是最典型的反面模式。

把四条合成一个分类骨架（真实 agent 主循环的分派核心）：

```ts
type ErrKind = "retryable" | "fatal" | "aborted" | "tool";

function classify(err: unknown): ErrKind {
  if (err instanceof Error && err.name === "AbortError") return "aborted";
  if (err instanceof ApiError) {
    if (err.status === 429 || err.status >= 500) return "retryable";
    return "fatal";                     // 400/401：重试无意义
  }
  if (err instanceof ToolError) return "tool";
  return "fatal";                       // 未知错误按最坏情况处理
}

// 主循环里的分派
switch (classify(err)) {
  case "retryable": return retryWithBackoff(task); // 退避后重试
  case "aborted":   return;                         // 取消：安静退出当前 turn
  case "tool":      return toolErrorResult(err);    // 转文本回传 LLM
  default:          throw err;                      // fatal：交给 14.4 兜底记录后退出
}
```

骨架的每一支对应分层图的一条路。真实项目的复杂度在于分类粒度（多加几类）与重试策略（退避上限、抖动、预算），不在结构本身。

## 本章只记住这 5 件事

1. 全是 unchecked：签名不声明抛出；判断会抛什么只能看实现、文档、自定义 Error 类的定义。
2. 永远 throw Error 实例；包装错误用 `new Error("ctx", { cause: err })`，与 Java 的 cause 链同构。
3. 同一个 throw 两种形态：async 函数里变 rejection；忘 await 的 rejection 不就地爆炸而是飞走，落到 unhandledRejection——现代 Node 默认崩溃退出。
4. uncaughtException 后进程状态不可信，记录后硬退；两个 process 级 handler 是保险丝，不是控制流。
5. instanceof 有双实例陷阱（双版本依赖 / dual package），库因此用 `err.code` / `err.name` 字符串判据——类加载器隔离问题的跨运行时近亲。
6. all 是 fail-fast（≈ allOf），allSettled 收集全部成败（≈ gather return_exceptions）；并行 tool 用后者。
7. Agent 分层总原则：tool 失败转 tool_result 回传模型（错误即信息），API 故障按可重试性分类，AbortError 识别后向上传播、绝不重试。

## 源码识别

- 看到 `new Error("...", { cause: err })` → 跨层包装错误，原始现场保留在 cause 链上。
- 看到 `catch (err)` + `instanceof XxxError` 收窄 → 自定义错误分支；顺带看该类是否还设置了 name/code 判据。
- 看到 `err.code === "ENOENT"` / `err.name === "AbortError"` → 字符串判据，防双实例或跨运行时形态差异。
- 看到 `process.on("unhandledRejection" / "uncaughtException")` → 进程级最后防线，只应记录并退出。
- 看到 `Promise.allSettled` + `toolError(r.reason)` → 容错并行，错误转消息回模型（第 04 章 agent loop 的接法）。
- 看到 `is_error: true` 的 tool_result → 错误被当作业务信息交给 LLM，而不是让进程 crash。
- 看到 `if (!res.ok)` → fetch 非 2xx 不抛异常的手动检查（对照 raise_for_status）。
- 看到 `err.status === 429` / 重试退避逻辑 → 可重试 / 不可重试的分类边界。
- 看到 `Object.setPrototypeOf(this, X.prototype)` → 旧 target 下自定义 Error 的 instanceof 修补。

## Java/Python 工程师常见误区

- 错误认知："函数签名能看出会抛什么（checked 直觉）" → TS/JS 全 unchecked，函数类型与抛出行为无关，文档和实现才是信息源。
- 错误认知："throw 字符串 / 字面量更轻量" → 丢调用栈、丢 cause、无法收窄；永远 throw Error 实例。
- 错误认知："try/catch 能兜住块里发起的异步调用" → 不在 await 中的 rejection 不受该 try 保护，会直接飞走。
- 错误认知："unhandledRejection 挂个 handler 打日志就能继续跑" → 打完日志该退就退（默认行为本来就是崩）；它常态出现本身是 bug。
- 错误认知："instanceof 是错误判别的正规姿势" → 双实例陷阱下不可靠，库惯用 code / name；自己写库时两条判据都留。
- 错误认知："工具抛错应该向上 throw 中断 agent" → agent 语义相反：失败细节是模型下一轮的输入，包进 tool_result 回传。

## 是否值得深入

- cause 链与错误包装规范：当前阶段：建议掌握 —— 分层项目里每层都在用。
- 同步 throw / rejection / error 事件三通道的辨析：当前阶段：建议掌握 —— 读异步代码判"错误去了哪"的基本功。
- AbortError 识别与取消传播：当前阶段：建议掌握 —— agent 打断功能的核心路径（第 04 / 15 章接续）。
- Agent 错误分层骨架：当前阶段：建议掌握 —— 改任何 agent 主循环前先对着分层图定位。
- AggregateError / Promise.any 的错误聚合：当前阶段：不需要深入 —— 低频，知道存在即可。
- Error.captureStackTrace / prepareStackTrace 等栈操控：当前阶段：不需要深入 —— 写诊断工具时再查。
- DOMException 体系全貌：当前阶段：看懂即可 —— AbortError / TimeoutError 两个判据够用。
