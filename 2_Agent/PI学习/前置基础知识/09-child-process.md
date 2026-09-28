# child_process：让 Agent 能跑命令（重点章）

LLM 只会生成文本。让文本变成"跑了测试、改了文件、提交了 commit"的，是 child_process。Coding Agent 的 bash 工具、git 集成、linter/test runner 调用、语言服务器宿主，底层全是这一章的内容。Java 的 `ProcessBuilder` 与它几乎同构，迁移成本低，但 Node 版的 stdout 天然是异步流——这直接改变了收集输出的代码形状。

## 9.1 为什么 Coding Agent 离不开 child_process【必须掌握】

Agent 主循环的每一步"执行工具"，大多数最终落到一次子进程调用：

```
Agent (Node)
  ↓ spawn("git", ["diff"])
git / npm / shell / compiler（子进程）
  ↓ stdout / stderr（流）
Agent 逐块读取 → 转成 tool result → 回传 LLM
```

一次典型的循环（真实报文形状）：

```json
// LLM 返回的 tool_use
{ "type": "tool_use", "name": "bash", "input": { "command": "npm test -- runInBand" } }
// agent 执行后回传的 tool_result
{ "type": "tool_result", "tool_use_id": "t1", "content": "exit code: 1\nFAIL src/foo.test.ts\n..." }
```

中间的"执行"就是本章：spawn 子进程 → 流式收集 → 等 close → 拿 exit code。除了 bash 工具，`git commit`、eslint、tsc、甚至长驻的语言服务器（一个活很久、用 stdin/stdout 双向说话的子进程），走的都是同一条路。

关键连接点：子进程的 `stdout`/`stderr` 是 Readable，`stdin` 是 Writable（第 07 章）。所以"收集子进程输出"不是新知识，就是消费流。

## 9.2 四个 API【必须掌握】

### spawn(command, args)：流式首选

参数是数组，不经过 shell，输出是流。大输出、实时输出、参数需要精确控制时的唯一选择：

```ts
import { spawn } from "node:child_process";

const child = spawn("git", ["diff", "--stat", "HEAD~1"]);
// child.stdout / child.stderr: Readable；child.stdin: Writable
for await (const chunk of child.stdout) process.stdout.write(chunk);
```

第三个流 `child.stdin` 同样常用——往子进程喂输入就是往 Writable 写：

```ts
const hash = spawn("git", ["hash-object", "-w", "--stdin"]);
hash.stdin.end(fileContent); // 写完记得 end，否则子进程一直等输入
let sha = "";
for await (const c of hash.stdout) sha += c.toString();
```

### exec(command, options, callback)：整条 shell 命令字符串

一条完整 shell 语法传进去，内部起 `/bin/sh -c`，全部输出缓冲成字符串后一次性给回调（或 promisify 后 await）。致命约束：`maxBuffer` 默认 1MB，超出直接杀掉子进程并返回错误——跑 `npm run build`、测试套件这种 MB 级输出会翻车：

```ts
import { exec } from "node:child_process";
import { promisify } from "node:util";
const execAsync = promisify(exec);

const { stdout } = await execAsync("cat package.json | jq .version && ls src");
console.log(stdout); // stdout/stderr 已经是完整字符串
```

### execFile：exec 但不走 shell

语义上等于 spawn + 替你收集输出成字符串（同样有 maxBuffer）。存在意义主要是给"执行一个确定的可执行文件"一个便捷 API。看到它读作"spawn 的收集版"。

### fork：spawn 的 Node 专用版【看懂即可】

专门 spawn 一个 Node 脚本，并额外建立 IPC 通道：父进程 `child.send(obj)` / `child.on("message", ...)`，子进程里对称地用 `process.on("message", ...)` / `process.send(...)`。Agent 的沙箱进程、插件宿主、worker 分层会用它。普通命令执行用不到。

### spawn vs exec 怎么选【必须掌握】

| 需求 | 选择 |
|---|---|
| 大输出 / 流式 / 参数精确控制 | spawn |
| 需要 shell 语法（管道、`&&`、glob、`$VAR`） | exec 或 `spawn(cmd, { shell: true })` |
| 短命令、要完整字符串结果 | exec / execFile |

```ts
// 场景 A：跑测试，输出几 MB，要流式——spawn
const t = spawn("npm", ["test", "--", "--reporter", "dot"]);
for await (const c of t.stdout) renderChunk(c);

// 场景 B：要 shell 语法——exec（或 spawn + shell: true）
const { stdout: version } = await execAsync("node -v | tr -d v");
```

安全一句话：拼 shell 字符串有注入面（`; rm -rf ~` 就是一条合法 shell 语句），参数数组没有。当命令来自 LLM 生成或用户输入时，这个区别不是风格问题而是安全边界；真实 agent 会对命令做白名单/解析后再决定参数形态。

## 9.3 stdio 配置【必须掌握】

`spawn` 的 `options.stdio` 决定子进程三个标准流接到哪里，数组按 `[stdin, stdout, stderr]`：

| 值 | 含义 | 典型用途 |
|---|---|---|
| `"pipe"`（默认） | 父进程拿到 `child.stdin/stdout/stderr` 流 | 收集输出、写入输入 |
| `"inherit"` | 直接接父进程的终端 | 让子进程交互式占用 stdin/stdout——如 `git commit` 拉起编辑器写 commit message、`npm init` 的问答 |
| `"ignore"` | 接 `/dev/null` | 不关心某个流，避免泄漏 fd |

`stdio` 数组每项也可以直接填一个流或 fd（把子进程 stdout 直接 pipe 到自己的 socket），低频，一句话带过。真实风格示例——spawn `git diff` 并分别收集两个流：

```ts
import { spawn } from "node:child_process";

const child = spawn("git", ["diff", "HEAD~1", "HEAD"], {
  stdio: ["ignore", "pipe", "pipe"], // stdin 不给，stdout/stderr 都要收
});

let stdout = "";
for await (const chunk of child.stdout) stdout += chunk.toString("utf8"); // 第 07 章

child.stderr.on("data", (c: Buffer) => console.error("[git]", c.toString())); // 伴生流用事件式
```

注意 `stdin` 配了 `"ignore"`，所以 `child.stdin` 是 null——stdio 数组和可用属性一一对应。

`inherit` 的真实用法（agent 让出终端给子进程）：

```ts
// git commit 需要拉起 $EDITOR 让人写 message：
// 编辑器必须直接读写 TTY，pipe 模式下它检测不到终端会直接失败
const exit = await new Promise<number | null>((resolve) =>
  spawn("git", ["commit"], { stdio: "inherit" }).on("close", (c) => resolve(c)),
);
```

## 9.4 退出：exit / close、exit code 与 signal【必须掌握】

**close 与 exit 的区别一句话**：`exit` 在进程退出时触发，此时 stdio 管道里可能还有没读完的数据；`close` 在所有 stdio 流也关闭后触发——收集输出必须等 `close`。

```ts
child.on("close", (code: number | null, signal: string | null) => {
  if (code === 0) resolve(stdout);
  else if (code !== null) reject(new ExitError(code));
  else reject(new SignalError(signal)); // code === null：被信号杀死
});
```

三个语义点：

- **exit code**：0 成功、非 0 失败，对照 `System.exit()` / JVM 正常退出返回 0。源码里最常见的就是 `if (code !== 0)` 分支——agent 里通常不是 throw，而是把错误信息做成 tool result 回传 LLM 让它自己纠错。
- **signal**：进程被信号杀死时 `code` 为 `null`、`signal` 为 `"SIGTERM"` / `"SIGKILL"` 等字符串。超时被杀的命令走的就是这条路。速查：

| 信号 | 来源 | 能否被捕获 |
|---|---|---|
| SIGINT | Ctrl+C | 能（默认退出） |
| SIGTERM | `kill` 默认 / AbortSignal | 能（可忽略，编辑器借此弹"是否保存"） |
| SIGKILL | `kill -9` | 不能，立即死 |

- 读源码时两者一起看：`on("close", ...)` + 对 `code`/`signal` 的解构，是所有命令执行封装的收尾形状。

另外 `on("error")` 与退出不同类：它报告的是 spawn 本身失败（如 ENOENT 找不到可执行文件），此时可能根本没有进程被创建，`close` 也许不会触发。健壮的封装两个都监听。

## 9.5 进程管理：kill、AbortSignal、detached【看懂即可】

- `child.kill(signal)`：默认发 SIGTERM。注意 SIGTERM 可以被子进程捕获/忽略（编辑器弹"是否保存"就是捕获了它），强杀用 `SIGKILL`。对照 Java：`destroy()` ≈ SIGTERM，`destroyForcibly()` ≈ SIGKILL。
- **AbortSignal 集成**：`spawn(cmd, { signal: controller.signal })`——abort 时 Node 自动给子进程发 SIGTERM。配合 `AbortSignal.timeout(ms)` 就是"超时杀命令"的标准做法，而且能把同一个 signal 从 HTTP 请求一路传到子进程（用户按 Esc 取消 → 命令跟着死）：

```ts
const ac = new AbortController();
ui.on("abort", () => ac.abort());           // 用户取消
const child = spawn("npm", ["test"], { signal: ac.signal });
// 之后无论 ac.abort() 还是超时，子进程都会收到 SIGTERM
```

- **子进程不会随父进程自动死**：父进程 crash 或退出，子进程被过继给 init 继续跑——表现为僵尸 dev server 占着端口。`detached: true` 显式创建新进程组（配合 `child.unref()` 让父进程不等它），反过来也用于按进程组整组杀。细节多，遇到再查。

## 9.6 环境控制：cwd 与 env【看懂即可】

`options` 里两个高频字段，agent 源码几乎每个 spawn 都带：

```ts
spawn("npm", ["test"], {
  cwd: projectRoot,            // 命令在哪个目录跑：agent 的多项目/会话隔离靠它
  env: { ...process.env,       // 继承父进程环境
    npm_config_registry: mirror,
    ANTHROPIC_API_KEY: undefined }, // 剔除敏感变量：防止 LLM 让子进程 echo 出密钥
});
```

要点：`env` 不传则继承父进程全部变量——agent 进程里往往躺着 API key，而子进程命令是 LLM 生成的，"打印环境变量"是一次合法调用。真实实现会显式白名单化 env。这是 child_process 在 agent 场景下独有的安全边界，Java/Python 的 subprocess 教科书不会强调它。

## 9.7 完整骨架：一个 bash tool【必须掌握】

真实 coding agent bash 工具的核心形状，把本章全部要点串起来：

```ts
import { spawn } from "node:child_process";

const MAX_OUTPUT = 30_000; // 截断阈值：防止撑爆 LLM 上下文

interface BashResult {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  signal: string | null;
  truncated: boolean;
  timedOut: boolean;
}

async function runBash(command: string, timeoutMs = 120_000): Promise<BashResult> {
  const timeout = AbortSignal.timeout(timeoutMs);
  const child = spawn(command, {
    shell: "/bin/bash",          // bash 工具要支持管道 / && / glob
    signal: timeout,             // 超时自动 SIGTERM（9.5 的标准做法）
  });

  let stdout = "", stderr = "", truncated = false;
  const collect = (s: NodeJS.ReadableStream, bucket: "stdout" | "stderr") => {
    s.on("data", (c: Buffer) => {
      if (stdout.length + stderr.length >= MAX_OUTPUT) { truncated = true; return; }
      if (bucket === "stdout") stdout += c.toString("utf8");
      else stderr += c.toString("utf8");
    });
  };
  collect(child.stdout, "stdout"); // 两个流分开收，LLM 要区分看
  collect(child.stderr, "stderr");

  const { code, signal } = await new Promise<{ code: number | null; signal: string | null }>(
    (resolve) => child.on("close", resolve), // 等 stdio 读完，不只等 exit
  );

  return { stdout, stderr, exitCode: code, signal, truncated, timedOut: timeout.aborted };
}
```

逐行对应前面的知识点：`shell` 支持 shell 语法；`signal` 管超时；`collect` 是流消费 + 截断（`truncated` 标记告诉 LLM 输出被截过）；等 `close` 而非 `exit` 拿完整输出；exitCode 原样返回而非 throw。真实实现还会加 cwd/env 隔离（9.6）、stdin 写入、输出边收边流式渲染——但核心就这 40 行。

主循环侧的接法（骨架怎么被用起来）：

```ts
// 收到 LLM 的 tool_use 后
const result = await runBash("npm test -- --runInBand", 180_000);
const toolResult = {
  type: "tool_result",
  tool_use_id: toolUse.id,
  is_error: result.exitCode !== 0, // 测试挂了也是"信息"，不是异常
  content: `exit code: ${result.exitCode}${result.timedOut ? " (timed out)" : ""}\n` +
    truncate(result.stdout + result.stderr, 8_000), // 二次截断适配上下文窗口
};
await client.messages.create({ messages: [...history, toolResult] }); // 回传，下一轮
```

## 9.8 长驻子进程：另一种形态【看懂即可】

上面都是"跑一条命令等它死"。agent 生态里还有反向形态：子进程活着不动，通过 stdin/stdout 长期对话——语言服务器（LSP）、ripgrep 服务化、shell 快照进程。协议通常是每行一个 JSON（JSON-RPC over stdio）：

```ts
const lsp = spawn("typescript-language-server", ["--stdio"], { stdio: ["pipe", "pipe", "ignore"] });

// 出向请求：往 stdin（Writable）写一行 JSON
lsp.stdin.write(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "initialize" }) + "\n");

// 入向响应：stdout 按行切流后逐条解析——第 07 章的 lineSplitter 直接复用
for await (const line of lsp.stdout.pipe(createLineSplitter())) {
  const msg = JSON.parse(line as string);
  if (msg.id === 1) onInitialized(msg.result);
}
```

识别特征：`spawn` 之后没有 `on("close")` 收尾，而是长期持有两个流。这就是 IDE 后端和 agent 编辑器集成的底座。

## 9.9 对照 Java ProcessBuilder / Python subprocess

Java（几乎同构）：

```java
Process p = new ProcessBuilder("git", "diff").start();
try (var r = new BufferedReader(new InputStreamReader(p.getInputStream()))) {
  String line; while ((line = r.readLine()) != null) System.out.println(line);
}
int code = p.waitFor();
```

| Java | Node 对应 |
|---|---|
| `new ProcessBuilder(...).start()` | `spawn(cmd, args)` |
| `p.waitFor()` 返回码 | `on("close")` 的 `code` |
| `p.getInputStream()` 是子进程 stdout | `child.stdout`（Readable） |
| `p.destroy()` / `destroyForcibly()` | `kill("SIGTERM")` / `kill("SIGKILL")` |

两个差异值得记住：一是命名陷阱——`getInputStream()` 返回的是子进程的 stdout（站在父进程"读入"的视角），`child.stdout` 无此歧义。二是 Node 的优势：`child.stdout` 天然是异步流，Java 里阻塞读 stdout 必须另开线程，否则 OS 管道缓冲区（约 64KB）写满后子进程的 write 阻塞、整条链死锁——这正是第 07 章说的"Java 无背压"在进程间的具体形态。

Python：`subprocess.run(cmd, shell=True, capture_output=True, timeout=30)` ≈ exec（收集全部输出，`timeout` 参数语义同 `AbortSignal.timeout`）；`subprocess.Popen` ≈ spawn（`p.stdout.readline()` 流式读）；`communicate()` 内部开线程同时读 stdout/stderr，正是为防上面 Java 那个死锁。整体心智可以平移，Node 版只是把输出统一成了流对象。

## 本章只记住这 5 件事

1. Agent 的 bash 工具本质 = `spawn` + shell + 流式收集 + 等 `close` + exit code 回传 LLM。
2. spawn：参数数组、不走 shell、输出是流；exec：shell 字符串、缓冲全部输出、maxBuffer 默认 1MB。默认用 spawn。
3. stdio 三配置：`pipe` 收流、`inherit` 让子进程直接占用终端、`ignore` 丢弃。
4. 收输出等 `close` 不等 `exit`；`code === null` + `signal` 有值 = 进程被信号杀死（超时被杀的标志）。
5. 超时杀命令的标准做法：`spawn(cmd, { signal: AbortSignal.timeout(ms) })`。
6. 子进程不随父进程自动死；父进程退出前要自己清理，否则僵尸进程占端口。

## 源码识别

- 看到 `spawn(cmd, args)` 参数数组 → 不走 shell、无注入面、stdout 是流。
- 看到 `{ shell: true }` 或 `shell: "/bin/bash"` → 需要 shell 语法，检查命令来源是否可信。
- 看到 `stdio: "inherit"` → 子进程直接交互式占用终端（git 编辑器、CLI 问答）。
- 看到 `for await (const c of child.stdout)` → 第 07 章的流消费用在子进程上。
- 看到 `on("close", (code, signal) => ...)` → 命令执行封装的收尾：等输出读完 + 处理退出码。
- 看到 `if (code !== 0)` → exit code 分支；agent 里多是构造错误 tool result 而非 throw。
- 看到 `signal: AbortSignal.timeout(...)` → 超时自动杀命令的标准做法。
- 看到 `child.kill("SIGKILL")` → SIGTERM 被忽略后的强杀兜底。
- 看到 `fork(...)` + `on("message")` / `process.send` → Node 子进程 IPC（沙箱/插件宿主）。
- 看到 `maxBuffer` → exec 系 API 的输出上限被显式调整。

## Java/Python 工程师常见误区

- 错误认知："exec 是新 API，统一用 exec" → 实际 exec 是老的收集式封装，1MB maxBuffer + 全量缓冲，大输出场景必然翻车；流式首选 spawn。
- 错误认知："`spawn("ls", ["*.txt"])` 没匹配到文件" → spawn 不经 shell，glob 不展开；要么自己展开，要么 `{ shell: true }`。
- 错误认知："exit 了输出就齐了" → exit 时 stdio 管道可能没排干，等 close；同理 waitFor() 之后立刻读流在 Java 里也是坑。
- 错误认知："父进程退出，子进程会被清理" → 不会，子进程被 init 收养继续跑；agent 退出前要显式 kill 自己起的进程树。
- 错误认知："非 0 exit code 要 throw 中断流程" → agent 语义相反：exit code 是给 LLM 的业务信息，包进 tool result 让模型决定重试还是改代码。
- 错误认知："kill() 调完进程就死了" → SIGTERM 可被捕获/忽略，编辑器还能弹窗问保存；确定要死用 SIGKILL。

## 是否值得深入

- spawn / exec / stdio / exit code：当前阶段：建议掌握 —— 读和改 agent 的工具层全靠它们。
- bash tool 骨架（超时 + 截断 + close）：当前阶段：建议掌握 —— 这就是 coding agent 工具执行的核心形状。
- fork 与 IPC 通道：当前阶段：不需要深入 —— 沙箱/插件架构才用，遇到再查。
- detached / 进程组 / 信号语义细节：当前阶段：不需要深入 —— 写进程树管理时再看。
- pty（伪终端）：当前阶段：不需要深入 —— 知道"agent 里跑 vim 这类交互程序需要 pty 而不是普通 pipe"即可。
- Windows 上的 shell 与信号差异：当前阶段：不需要深入 —— 跨平台工具发布时再处理。
