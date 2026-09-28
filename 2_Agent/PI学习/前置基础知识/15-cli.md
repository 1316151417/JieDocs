# CLI 与终端：一个 Coding Agent 的输入输出层

agent 的一切用户可见行为都压在这一层：键盘输入怎么进来、输出怎么画到屏幕、Ctrl+C 怎么打断当前回合、进程怎么退得干净。做 Java 服务端很少碰终端编程——那是 ncurses 的老地盘；本章从零建立这层模型：三个标准流、TTY、raw mode、信号、退出码。第 16 章会把这些与 LLM 调用、工具执行拼成完整架构。

## 15.1 一张图：输入输出层全景【必须掌握】

```
Keyboard
   ↓
stdin（流）
   ↓
Agent（解析按键 / 命令）
   ↓
LLM / Tools（网络 I/O、子进程）
   ↓
stdout / stderr（流）
   ↓
Terminal 渲染
```

自上而下过一遍，每环标注归属：

- **键盘不是事件，是 stdin 流上的字节**。按 a 产生字节 0x61，按 Ctrl+C 产生 0x03，方向键是一串以 ESC 开头的字节——怎么"分组"成按键，由 raw mode 决定（15.5）。
- **Agent 层把字节解析成按键 / 命令**。这是你读的 TUI 源码所在的一层：按键路由、命令解析（`/model` 这类斜杠命令）、状态更新。
- **LLM / Tools** 是第 04 / 09 章的内容：网络流与子进程，对输入输出层只是"耗时操作 + 最终产生输出"。
- **stdout / stderr 是流**（第 07 章）；`console.log` 是 `process.stdout.write` 的语法糖（第 05 章）。
- **Terminal 渲染不在你的代码里**。终端模拟器读你写出的字节流，遇到转义序列就执行指令（移动光标、变色），其余当文本画上字符网格（15.4）。

这张图最重要的一条推论：**TUI 程序与终端之间只有字节流**——没有 GUI 事件对象、没有组件树、没有绘制回调。一切"界面"都是写出去的字节，一切"输入"都是读进来的字节。

读源码时按环节定位归属：

| 环节 | 归谁写 | 识别特征 |
|---|---|---|
| 键盘字节进入 | runtime（不归你） | `process.stdin` |
| 按键 / 命令解析 | agent 的 TUI 层 | `on("data")` + 字节判断；斜杠命令表 |
| LLM / 工具执行 | agent 核心层 | `for await` 消费流、`spawn`（第 04 / 09 章） |
| 输出构造 | TUI 渲染层 | `stdout.write` + `\x1b[` 序列 |
| 终端渲染 | 终端模拟器（不归你） | — |

## 15.2 process.argv：参数是裸数组【必须掌握】

```ts
// 命令行：agent chat --model sonnet --verbose
process.argv;
// [
//   "/usr/local/bin/node",   // argv[0]：node 可执行文件
//   "/repo/dist/cli.js",     // argv[1]：入口脚本（package.json 的 bin 指向它，第 10 章）
//   "chat", "--model", "sonnet", "--verbose", // argv[2] 起：真正的参数
// ]
```

argv 的结构（argv[2] 起才是用户参数）第 05 章已拆过，这里补 CLI 视角。与 argparse / click 的本质差异是接管方向：Python 那边是**框架接管**——你声明参数，框架解析、校验、生成 help、报用法错误；Node 传统是**数组自取**——runtime 只交给你一个原始数组，解析是你自己的事。所以小工具常见手写解析：

```ts
const args = process.argv.slice(2);
let model = "default";
let verbose = false;
const positional: string[] = [];
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--model") model = args[++i];
  else if (args[i] === "--verbose") verbose = true;
  else positional.push(args[i]);
}
```

库只是这一层之上的可选封装：commander（声明式，最像 argparse）、yargs（老牌功能全）、cac（轻量）【看懂即可】——看到 `new Command().option(...)` 知道在声明选项即可。读源码的意义：argv 解析几乎总在 cli.ts / main.ts 最顶端，是找"这个命令支持哪些行为"的入口。

位置参数的第一个通常是子命令（chat / model / run），路由到各自 handler。agent 项目常见命令表形态——注册表驱动，补全提示与帮助从同一张表生成：

```ts
const commands = new Map<string, (args: string[]) => Promise<void>>([
  ["chat", cmdChat],
  ["model", cmdModel],
]);
const run = commands.get(positional[0]);
if (!run) { printUsage(); process.exitCode = 2; } // 用法错误：惯例用 2 与一般失败区分
else await run(positional.slice(1));
```

argparse 的 subparsers 在 Node 没有唯一对应物，各项目自己定形态——读到分发逻辑时按"查表 + fallback usage"理解即可。

## 15.3 stdin / stdout / stderr 与 isTTY【必须掌握】

三个标准流就是 fd 0/1/2（第 05 章）：stdin 是 Readable，stdout / stderr 是 Writable，全是流（第 07 章）。这一节的关键是 `process.stdout.isTTY`：**stdout 接在终端上为 true，被 `| head`、`> file` 接管时为 false**。这个布尔值是无数 CLI 行为差异的钥匙：

```ts
const useColor = process.stdout.isTTY && !process.env.NO_COLOR;
const out = (s: string) => process.stdout.write(useColor ? `\x1b[36m${s}\x1b[0m` : s);
```

现象对齐：ls / jq 在终端里彩色、管道里纯文本；agent 在终端里转 spinner、显示流式 token，被管道接住时静默到底、结束吐一份纯结果——同一个 if 分支。彩色字节混进 `agent chat | jq` 会让 jq 解析失败，这就是管道下必须切纯文本的原因。

数据与诊断的分流约定：**数据走 stdout，日志 / 诊断 / 进度走 stderr**——对照 shell 重定向的用法：`2>/dev/null` 丢诊断、`> file` 拿数据、`2>&1` 合流。agent 场景即：会话文本与最终 patch 走 stdout，警告与遥测走 stderr，这样 `agent "fix bug" > patch.diff` 才拿得到干净产物。

stdin 同样有 `process.stdin.isTTY`：终端接着 stdin，可以开交互 TUI；管道喂入（`cat bug.md | agent chat`）则是 headless 模式，把 stdin 当数据读完（第 07 章的消费流写法）：

```ts
async function readAllStdin(): Promise<string> {
  let data = "";
  for await (const chunk of process.stdin) data += chunk.toString("utf8"); // 流的 for await
  return data.trim();
}
```

启动时按 isTTY 分支，决定整个前端形态——15.7 的骨架里落地。

## 15.4 TTY 与 TUI【必须掌握】

- **TTY**：终端这一设备 / 接口。词源是 teletypewriter（电传打字机），今天指终端模拟器呈现的字符设备：收键盘字节、按字符网格渲染输出。`isTTY` 为 true 即"接着这个设备"。
- **TUI**（terminal UI）：在终端里画界面的程序——vim、htop 是传统形态，ink / blessed 是现代框架。coding agent 的交互前端就是一个 TUI。
- 渲染机制【看懂即可】：**ANSI 转义序列**——stdout 写出的特定字节（ESC `[` 即 `\x1b[` 开头）被终端解释为指令而非文本：

```ts
process.stdout.write("\x1b[2K\r"); // 清当前行并回到行首：spinner / 进度条重画的原子操作
process.stdout.write("\x1b[1A");   // 光标上移一行：重画上方区域
process.stdout.write("\x1b[?25l"); // 隐藏光标（\x1b[?25h 恢复）
```

TUI 的"刷屏" = 光标移动 + 重写内容。全屏界面（vim 进去退出后 shell 还在原地）用的是 alternate screen buffer（`\x1b[?1049h` 切入）——细节知道存在即可，需要时再查。

进度提示的最小实现——同一行反复清掉重写，就是一切 spinner / 进度条的本质（走 stderr：它是诊断信息，不该污染管道里的数据流）：

```ts
const frames = ["|", "/", "-", "\\"];
let i = 0;
const timer = setInterval(() => {
  process.stderr.write(`\r${frames[i++ % frames.length]} thinking...`); // \r 回行首覆盖重写
}, 100);
// LLM 响应到达后：clearInterval(timer)，再 \r + 清行，别让残影留在输出里
```

## 15.5 raw mode：从行到键【必须掌握】

默认模式（canonical mode，行缓冲）：终端驱动攒一整行，按回车才交付给程序；期间退格、行内编辑都由驱动处理，Ctrl+C 被驱动转成 SIGINT 发给进程——程序还没见到这个键就（默认）死了。

`setRawMode(true)` 关掉全部加工，**逐键即得字节**：程序看到的是原始键码——按 a 得 0x61，按 Ctrl+C 得 0x03（不再自动变信号），方向键得 ESC 开头的一串。这一件事解释两件事：TUI 为什么能对每个键实时响应；raw mode 程序里 Ctrl+C 为什么不再默认退出——它只是一个字节，程序必须自己处理。

```ts
process.stdin.setRawMode(true);
process.stdin.on("data", (d: Buffer) => {
  if (d[0] === 0x03) { cleanup(); process.exit(130); } // Ctrl+C 是普通字节，退出要自己做
  else handleKey(d); // 其余交给按键解析 / TUI 框架
});
```

TUI 框架（ink / blessed【看懂即可】）就建在这层之上：开 raw mode + 解析转义序列 + diff 渲染。你读的 agent 源码大多直接用框架，但框架文档里"必须自己处理 Ctrl+C"的根源在这里。

常见键的字节形态——TUI 按键解析的原料，读源码认得即可：

| 键 | 字节 |
|---|---|
| Ctrl+C | `0x03` |
| Enter | `0x0d` |
| Backspace | `0x7f` |
| ESC | `0x1b`（也是方向键序列的首字节，解析要区分"单独 ESC"与"序列开头"） |
| 方向上 | `0x1b 0x5b 0x41`（ESC `[` `A`） |

纪律：**退出前必须恢复终端**（`setRawMode(false)`），否则 raw 状态残留——程序退出后 shell 无回显、按键错乱。"程序崩了终端坏了"说的就是它，shell 的 `reset` 命令就是修这个的。

## 15.6 exit code 与 process.exit【必须掌握】

0 成功、非 0 失败；CI、npm scripts、父进程全靠它判断成败（第 05 / 09 章）。但设置退出码有两种方式，行为不同：

```ts
process.stdout.write("final report ...");
process.exit(0);      // 立刻截断：stdout 接管道时写入是异步的，缓冲里没刷的输出直接丢失
process.exitCode = 0; // 只标记结果：事件循环自然排空（含 stdout 刷完）后进程退出
```

`process.exit()` 丢输出的原因：stdout 接终端时多为同步写，接管道 / 文件时是异步写，而 `exit()` 不等写队列——经典现场是 `agent report | head` 尾部被截。JVM 的 `System.exit` 与 shutdown hook 有类似的收尾问题，但 Node 这条在日常 CLI 里踩得更频繁（第 05 章埋的坑在这里展开）。

进程什么时候自然退出：没有挂起的 I/O、没有未触达的 timer、没有打开的 server、没有活跃的子进程（第 03 章）。CLI"退不出去"的排查就是找未关句柄：忘清的 `setInterval`、未 kill 的子进程、未 close 的 server。timer 型句柄可以 `unref()` 声明"不算进程存活的理由"（第 04 章）。

实践排序：优先 `exitCode` + 自然退出；`exit()` 只在"状态不可信必须立刻死"时用（14.4 的 uncaughtException 兜底）；SIGKILL 是外部强杀，程序内没有对应物（15.7）。

## 15.7 信号与优雅关闭【必须掌握】

两个常驻信号：SIGINT（Ctrl+C）、SIGTERM（`kill` 默认）。`process.on("SIGINT", handler)` 拦截后**默认行为被替换**——想退出就得自己设退出码。SIGKILL 不可捕获不可忽略（第 09 章的信号表）。

对照 JVM shutdown hook：`Runtime.addShutdownHook` 在正常退出与 SIGINT / SIGTERM 时依次执行一组钩子；Node 没有"一组钩子保证跑完"的框架——一个信号一个 handler，handler 里发起的异步清理若不等完、进程照样退，顺序与完成性全自己管。SIGKILL 两边都跳过。

agent 优雅关闭的清单：abort 进行中的 LLM 请求（AbortController，第 04 章）、杀掉自己起的子进程（子进程不随父死，第 09 章）、恢复终端（raw mode / 光标 / 屏幕缓冲）、flush 输出与日志、按结果设 exitCode。

Ctrl+C 的惯用法：**一次打断当前 turn**（abort，会话保留），**短时间内两次才退出**。raw mode 下 Ctrl+C 是字节不是信号，惯用写法是手工还原成信号——`process.kill(process.pid, "SIGINT")`——让 TUI 与非 TUI 共用一份信号处理路径：

```ts
const turnAbort = new AbortController(); // 当前 turn 的取消源（第 04 章）
const children: ChildProcess[] = [];     // 本会话起过的子进程（第 09 章）
let sigintCount = 0;

process.on("SIGINT", () => {
  if (sigintCount++ === 0) {             // 第一次：只打断当前 turn
    turnAbort.abort();
    process.stderr.write("\n已打断当前回合；再按一次退出\n");
    setTimeout(() => (sigintCount = 0), 1_000).unref(); // 双击窗口过后重置
    return;
  }
  cleanup();
  process.exitCode = 130;                // 128 + SIGINT(2)：shell 对 Ctrl+C 的惯例值
});

if (process.stdin.isTTY) {               // 交互模式：开 TUI
  process.stdin.setRawMode(true);
  process.stdin.on("data", (d: Buffer) => {
    if (d[0] === 0x03) process.kill(process.pid, "SIGINT"); // 字节还原成信号，统一处理
    else onKeypress(d);                  // 交给按键解析 / TUI 框架
  });
} else {
  runHeadless(await readAllStdin());     // 管道喂入：headless 模式，stdin 当数据读完
}

function cleanup() {
  if (process.stdin.isTTY) process.stdin.setRawMode(false); // 恢复终端，否则退出后无回显
  for (const c of children) c.kill("SIGTERM");
  turnAbort.abort();
}
```

骨架里每个选择都有出处：`exitCode = 130` 而非 `exit(130)`，让输出自然刷完（15.6）；`unref()` 让重置定时器不拖住进程（第 04 章）；cleanup 同样要挂到 `process.on("SIGTERM")`——容器停止（`docker stop`）发的就是 SIGTERM；恢复 raw mode 是"退出后终端还能用"的前提（15.5）。这份骨架加 15.3 的 isTTY 分支，就是一个交互式 agent 输入输出层的完整生命周期。

## 本章只记住这 5 件事

1. 全景图：键盘字节 → stdin 流 → agent 解析按键 / 命令 → LLM / tools → stdout / stderr 流 → 终端渲染；程序与终端之间只有字节，没有 GUI 概念。
2. `isTTY` 是行为分支的钥匙：终端彩色 / 交互，管道纯文本 / headless；数据走 stdout、诊断走 stderr，管道用法（重定向）才成立。
3. raw mode 把"按回车交付整行"变成"逐键即得字节"：Ctrl+C 变 0x03 普通字节，TUI 必须自己处理退出并恢复终端。
4. `process.exitCode` 让事件循环自然排空；`process.exit()` 立刻截断，管道下未刷完的 stdout 输出直接丢——优先前者。
5. SIGINT / SIGTERM 可拦截自定义（abort 请求、杀子进程、恢复终端），SIGKILL 不可；Node 没有 shutdown hook 式框架，异步清理的完成性自己负责。
6. Ctrl+C 惯用法：一次 abort 当前 turn、两次退出；raw mode 下用 `process.kill(process.pid, "SIGINT")` 把字节还原成信号，统一处理路径。
7. 启动时 `process.stdin.isTTY` 决定交互 TUI 还是 headless 管道模式。

## 源码识别

- 看到 `process.argv.slice(2)` → 手写参数解析的起点，通常在 cli 入口最顶端。
- 看到 `process.stdout.isTTY` → 终端 / 管道的行为分支（彩色、spinner、交互）。
- 看到 `setRawMode(true)` → TUI 逐键接收模式；顺带检查退出路径是否恢复。
- 看到 `\x1b[` / `\u001b[` 字节 → ANSI 转义序列：清行、移光标、变色等终端指令。
- 看到 `process.stdin.isTTY ? ... : ...` → 交互 / headless 双模式 CLI。
- 看到 `process.stdin.on("data", ...)` + 字节判断（0x03 / 0x1b）→ 键盘字节流的逐键解析。
- 看到 `process.on("SIGINT" / "SIGTERM")` → 拦截信号做优雅关闭：abort、杀子进程、恢复终端。
- 看到 `process.kill(process.pid, "SIGINT")` → raw mode 下把 Ctrl+C 字节还原成信号。
- 看到 `process.exitCode = N` → 等事件循环排空的退出方式；`process.exit(N)` → 立刻截断。
- 看到 ink / blessed 的 import → TUI 框架接管了键盘与渲染，读组件树而非字节处理。

## Java/Python 工程师常见误区

- 错误认知："键盘输入是事件回调（GUI / Swing 直觉）" → 是 stdin 流上的字节；"按键"是程序自己从字节解析出来的概念。
- 错误认知："write 了就输出成功了" → stdout 接管道时是异步写，`process.exit()` 会把没刷完的缓冲直接丢掉。
- 错误认知："Ctrl+C 永远终止程序" → 默认是；拦截后变成自定义行为；raw mode 下连信号都不是，只是一个 0x03 字节。
- 错误认知："进程退出会自动清理子进程和终端状态" → 都不会：子进程被 init 收养继续跑（第 09 章），raw mode 残留要手工恢复。
- 错误认知："调试输出走 stdout 还是 stderr 无所谓" → 数据 / 诊断分流是重定向用法的前提，混流会让 `> file` 拿到脏产物。
- 错误认知："像 JVM 一样有 shutdown hook 框架兜底清理" → Node 每个信号一个 handler，异步清理要自己显式等完成，否则进程照样走。

## 是否值得深入

- isTTY 分支 / 流式输出 / raw mode / 信号处理的组合：当前阶段：建议掌握 —— 读和改交互式 agent 前端的全部地基。
- Ctrl+C 打断与 AbortController 的联动：当前阶段：建议掌握 —— 15.7 骨架 + 第 04 章取消链合起来就是完整功能。
- ANSI 转义序列全集：当前阶段：不需要深入 —— 清行、光标移动、颜色三个够用；TUI 框架会代管。
- terminfo / 终端类型数据库：当前阶段：不需要深入 —— 现代终端模拟器兼容性足够好。
- ink / blessed 框架 API：当前阶段：看懂即可 —— 读到用它的项目时按需查文档。
- 信号全集与 Windows 差异（SIGHUP、SIGQUIT、无 POSIX 信号的平台）：当前阶段：不需要深入 —— SIGINT / SIGTERM / SIGKILL 覆盖主场景，跨平台发布时再查。
- pty（伪终端）：当前阶段：不需要深入 —— 知道"agent 里跑 vim 这类交互程序需要 pty 而非普通 pipe"即可（第 09 章口径）。
