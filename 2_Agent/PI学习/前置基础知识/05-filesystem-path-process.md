# fs / path / process：文件、路径与进程全局

> fs 读写文件、path 拼路径、process 提供进程级全局（argv / env / cwd / exit / 标准流）。这三样是 Coding Agent 的地基：read/write/edit 工具、配置加载、凭据读取全部建立在它们之上。读完的标准：在源码里看到任何 `fs.*`、`path.*`、`process.*` 调用，能立刻说出它在干什么、路径相对于什么解析。

## 5.1 fs：三套并存的 API【必须掌握】

Node 的文件操作有三套同时存在的接口，功能一致，区别只在调用风格。读源码时三种都会遇到：

| 风格      | 形态                                          | 导入                 |
| ------- | ------------------------------------------- | ------------------ |
| 同步      | `fs.readFileSync(p, "utf8")`                | `node:fs`          |
| 回调      | `fs.readFile(p, "utf8", (err, data) => {})` | `node:fs`          |
| Promise | `await readFile(p, "utf8")`                 | `node:fs/promises` |

```ts
import * as fs from "node:fs";                 // 同步 + 回调两套都在这里
import { readFile } from "node:fs/promises";   // Promise 式，现代首选

// 1. 同步：阻塞事件循环，拿到结果才继续（≈ Java 的普通阻塞 IO）
const a = fs.readFileSync("package.json", "utf8");

// 2. 回调：老代码风格，err 永远是第一个参数
fs.readFile("package.json", "utf8", (err, data) => {
  if (err) throw err;
  console.log(data.slice(0, 20));
});

// 3. Promise：async 函数里 await（≈ Files.readString 的异步版）
const b = await readFile("package.json", "utf8");
```

选择规则一句话：库与服务端代码用 `node:fs/promises`；CLI 启动期读一次配置，同步版完全可接受（那时还没有可被阻塞的并发任务）；回调版只活在老代码里，读得懂即可，不要在新代码里模仿。

### 常用函数速览

```ts
import { readFile, writeFile, stat, readdir, mkdir, rm } from "node:fs/promises";

const text = await readFile("a.txt", "utf8");         // 读文本（整体读入）
await writeFile("out.log", text, "utf8");             // 写文本（整体覆盖，无 append）
const st = await stat("a.txt");                       // st.isFile() / st.size / st.mtime
const names = await readdir("src");                   // 目录项名，string[]
await mkdir("a/b/c", { recursive: true });            // ≈ Files.createDirectories
await rm("build", { recursive: true, force: true });  // ≈ rm -rf
```

迁移对照：`fs/promises` ≈ `java.nio.file.Files` + `Paths` 的异步版。`Files.readString(p)` ↔ `await readFile(p, "utf8")`；`Files.createDirectories` ↔ `mkdir(p, { recursive: true })`；Python 侧对应 `pathlib.Path.read_text()` 的 await 化。一个差异：Node 的路径就是字符串，没有 Path 对象这一层。

### 不传 encoding，拿到的是 Buffer

`await readFile(p)` 不带 `"utf8"` 时返回 `Buffer`（原始字节），带了才是 string。源码里处理二进制（图片、未知格式、按字节切分）就会省略 encoding。Buffer 的细节见第 08 章，本章只记结论：**没传 encoding 的 readFile，返回值是 Buffer 不是 string**，TS 类型会明确告诉你。

### 相对路径一律相对 cwd【高频陷阱】

```ts
await readFile("src/index.ts", "utf8");
// 实际解析为：path.join(process.cwd(), "src/index.ts")
```

这一点三门语言一致：Java 的 `new File("src")` / `Paths.get("src")` 相对 `user.dir`，Python 的 `open("src")` 相对 `os.getcwd()`。真正的差异在 Coding Agent 场景：**cwd 在会话中途是可变的**。bash / cd 类工具的实现就是 `process.chdir(dir)`，此后所有相对路径的含义跟着变。所以工具实现里看到相对路径，第一反应是"它此刻会 resolve 到哪"；路径校验与沙箱越界判断都必须基于当时的 cwd。

### createReadStream：本章只教认出【看懂即可】

```ts
import { createReadStream } from "node:fs";

const rs = createReadStream("huge.log", { encoding: "utf8" });
rs.on("data", (chunk) => process.stdout.write(chunk));
```

何时用：文件太大不宜整体读入内存（日志、模型权重、tar 包）时，分块流式处理。`on("data")` 的事件机制属于第 06 章的内容，backpressure 与流全家桶见第 07 章。本章目标只有一个：看到 `createReadStream`，知道"这是在流式读大文件"。

权限位（`fs.access`）、chmod、软链（`symlink`）、watch【暂时跳过】：低频设施，读源码撞到再查文档。

## 5.2 path：join 与 resolve，读源码最常混淆的一对【必须掌握】

### join 是拼接，resolve 是求绝对路径

```ts
import path from "node:path";

path.join("src", "lib", "a.ts");      // "src/lib/a.ts"       —— 纯拼接，结果仍可是相对路径
path.resolve("src", "lib", "a.ts");   // "/cwd/src/lib/a.ts"  —— 转绝对：拼上 cwd
path.resolve("/base", "src", "./x");  // "/base/src/x"        —— 从右向左遇绝对段，前面丢弃
path.join("/base", "..", "b");        // "/b"                 —— join 也会顺带 normalize
```

| | `path.join` | `path.resolve` |
|---|---|---|
| 干什么 | 把若干段拼成一个路径 | 把参数解析成绝对路径 |
| 用到 cwd 吗 | 不用 | 没有绝对段时用 cwd 兜底 |
| 典型用途 | 在已知目录下拼文件名 | 把外部给的路径锚定成绝对路径 |

读源码的判断口径：join 关心"路径长什么样"，resolve 关心"这条相对路径到底指哪"。工具实现里最常见的写法是 `path.resolve(cwd, p)`——把模型或用户给的路径锚定到会话工作目录。

### dirname / basename / extname

```ts
const p = "/repo/src/agent/run.ts";
path.dirname(p);          // "/repo/src/agent"  —— ≈ Path.getParent / os.path.dirname
path.basename(p);         // "run.ts"           —— ≈ Path.getFileName（含后缀）
path.basename(p, ".ts");  // "run"              —— 第二参可去掉后缀
path.extname(p);          // ".ts"              —— ≈ pathlib 的 .suffix，带点
```

### 为什么不能手写 "/" 拼接

Windows 的分隔符是 `\`：`path.sep` 随平台变化，join 内部按平台处理并 normalize（`a/../b`、重复分隔符、尾部斜杠）。手写 `dir + "/" + name` 在 POSIX 上碰巧能跑，到 Windows 上解析、比较、去重全乱。规范是：拼接一律 path.join，连字面量 `/` 都不手写。`path.posix` / `path.win32` 强制按某一平台规则执行（拼 URL、生成跨平台配置时用）【看懂即可】。

## 5.3 process：全局进程对象【必须掌握】

`process` 是全局对象，不 import 就能用（同 `console`）。语义上是 Java 里 `System` + `Runtime` + 标准流 + 信号处理的合体。现代代码为了显式声明依赖常写 `import process from "node:process"`——同一个东西，见到不要困惑。

### argv：命令行参数从下标 2 开始

```ts
// 终端执行：node bin/cli.js --model gpt-5 "修复登录"
process.argv;
// [0] "/usr/local/bin/node"   ← node 可执行文件
// [1] "/repo/bin/cli.js"      ← 入口脚本（package.json 的 bin 指向它）
// [2] "--model" [3] "gpt-5" [4] "修复登录"   ← 真正的参数

process.argv.slice(2);    // 手写参数解析从这里开始
```

惯例与 C 的 `argc/argv` 同源：argv[0] 是程序自身，参数从 2 开始（中间夹了一个脚本路径）。这和 Java `main(String[] args)` 不同——args 里没有程序名。成熟项目用 commander / yargs / cac 解析，但它们底层读的就是 process.argv。

### env：一张 string 映射

```ts
const key = process.env["ANTHROPIC_API_KEY"];      // 类型 string | undefined
const debug = process.env["DEBUG"] === "1";
const port = Number(process.env["PORT"] ?? 3000);  // 没有数字型 env，自己转
```

对照 Java `System.getenv()`（缺失返回 null）与 Python `os.environ`（缺失抛 KeyError / 用 .get）。两个一句话陷阱：所有值都是 string，`PORT` 也要自己 Number；Windows 上变量名大小写不敏感（`env.Path === env.PATH`），跨平台代码不要用大小写区分变量。

### cwd() 与 __dirname / import.meta.dirname：两个"在哪"

```text
$ cd /tmp
$ node /home/dev/agent/bin/cli.js

process.cwd()        = /tmp                   ← 进程从哪启动；可被 process.chdir 改变
import.meta.dirname  = /home/dev/agent/bin    ← cli.js 源码文件所在目录；恒定不变
```

- `process.cwd()`：运行时工作目录。**模型给的相对路径的解析锚点**，agent 的 cd 工具会改它。
- `__dirname`（CJS）/ `import.meta.dirname`（ESM，Node 20.11+）：源码文件所在目录。**加载随代码分发的资源**（提示词模板、内置脚本）的锚点，与从哪启动无关。

分工是硬规则：工具路径用 `path.resolve(process.cwd(), p)`，内置资源用 `path.join(import.meta.dirname, "assets/prompt.txt")`。混用是真实 bug 来源——把资源相对 cwd 去找，换个目录启动就找不到文件。

### exit：同步立即退出

```ts
process.exit(1);        // ≈ System.exit(1)：同步、立即、不等挂起的 I/O
process.exitCode = 1;   // 温和版：事件循环自然排空后以 1 退出
```

0 成功、非 0 失败，与 JVM / POSIX 约定一致，CI 与 npm scripts 靠它判断成败。高频陷阱：`process.stdout.write` 之后紧跟 `process.exit`，管道里没刷完的输出被直接丢弃——日志被截尾。所以 CLI 里更推荐设 `exitCode` 让循环自然结束。信号与优雅退出归第 15 章。

### 三个标准流：一句话

`process.stdin` / `process.stdout` / `process.stderr` 就是 fd 0/1/2 那三个标准流；`console.log` 的底层是 `process.stdout.write`。它们同时是 EventEmitter 又可读写——细节全部归第 15 章，本章认得出即可。

## 5.4 在 Coding Agent 里：read 工具就是 fs + path

read / write / edit 工具的本质，是把模型的请求参数翻译成受控的 fs 调用：

```text
模型输出 tool_call: { path: "src/a.ts", offset: 10 }
        │
        ▼
path.resolve(process.cwd(), "src/a.ts")       ← 相对路径锚定到会话 cwd
        │
        ▼
stat 校验 isFile → readFile(p, "utf8")        ← fs/promises
        │
        ▼
"11\texport ...\n12\t..."                     ← 行号化文本，作为 tool_result 喂回模型
```

read 工具骨架，主干就这么多：

```ts
// tools/read.ts（骨架）
import { readFile, stat } from "node:fs/promises";
import path from "node:path";

async function read(params: { path: string; offset?: number; limit?: number }) {
  const abs = path.resolve(process.cwd(), params.path);  // 锚定会话 cwd
  const st = await stat(abs);
  if (!st.isFile()) throw new Error(`not a file: ${abs}`);
  const text = await readFile(abs, "utf8");              // 传 utf8 得 string；不带 encoding 则是 Buffer
  const lines = text.split("\n");
  const start = params.offset ?? 0;
  const end = params.limit ? start + params.limit : lines.length;
  return lines.slice(start, end)
    .map((l, i) => `${start + i + 1}\t${l}`)             // 行号 + tab，喂给模型
    .join("\n");
}
```

edit 工具同理：readFile 全文 → 校验 `old_string` 在全文中唯一 → 字符串替换 → writeFile 写回。工作目录决定一切相对路径的解析结果，所以很多 agent 提供一个 cd 工具，核心实现就是一行 `process.chdir(dir)`。

CLI 启动时从 env 读凭据是另一个固定模式：

```ts
function requireEnv(name: string): string {
  const v = process.env[name];
  if (v === undefined) throw new Error(`环境变量未设置: ${name}`);
  return v;
}

const apiKey = requireEnv("ANTHROPIC_API_KEY");  // 启动时读一次，缺了就快速失败
```

## 5.5 对照总结

| Node | Java 最近对应物 | 备注 |
|---|---|---|
| `fs/promises` | `Files` + `Path`（异步化） | Node 的路径是纯字符串 |
| `fs.readFileSync` | 阻塞式 `Files.readAllBytes` 等 | 语义相同：拿到才继续 |
| `path.join` | `Paths.get(a, b)` | join 不碰 cwd |
| `path.resolve` | `path.toAbsolutePath()` | resolve 自带 cwd 兜底 |
| `process.env` | `System.getenv()` | 属性访问 vs 方法调用 |
| `process.argv` | `main(String[] args)` | Node 前两个元素是 node 与脚本 |
| `process.exit(code)` | `System.exit(code)` | Node 更容易丢未刷出的输出 |
| `process` 整体 | `System` + `Runtime` + 标准流 + 信号 | 一个全局对象全包 |

## 本章只记住这 5 件事

1. fs 三套 API 并存，现代代码首选 `node:fs/promises` + await；同步版在 CLI 启动路径上合法；回调版只读不写。
2. `readFile` 不传 encoding 返回 Buffer，传 `"utf8"` 才是 string。
3. 相对路径一律相对 `process.cwd()`；agent 的 cd 工具会中途改 cwd，路径含义随会话漂移。
4. `path.join` 只拼接，`path.resolve` 产出绝对路径（无绝对段时拼 cwd）——读源码最常混淆的一对。
5. `process` 是免 import 的全局：argv 参数从下标 2 开始；env 全是 string；exit 立即退出并丢弃挂起 I/O。
6. `process.cwd()` 是"进程在哪"，`import.meta.dirname` 是"源码在哪"；工具路径用前者，内置资源用后者。
7. Coding Agent 的 read/write/edit 工具 = fs + path 的薄封装；CLI 凭据 = `process.env` + 启动期快速失败。

## 源码识别

- 看到 `from "node:fs/promises"` → 异步文件操作，检查调用点有没有 await
- 看到 `fs.readFileSync` → 同步阻塞，通常在启动 / 配置加载路径上
- 看到 `path.resolve(cwd, p)` → 把外部输入的路径锚定成绝对路径（工具边界）
- 看到 `path.join(__dirname / import.meta.dirname, ...)` → 加载随代码分发的资源
- 看到 `process.env.XXX` → 读配置或 API key，看旁边的 undefined 检查
- 看到 `process.argv.slice(2)` → 手写 CLI 参数解析（或 commander / yargs 的入口）
- 看到 `process.exit(1)` → CLI 失败退出路径；留意附近有没有没刷完的 stdout
- 看到 `createReadStream` → 大文件流式读，机制细节跳到第 07 章
- 看到 `process.chdir` → agent 的 cd 工具，cwd 从此改变

## Java/Python 工程师常见误区

- 错误认知：Node 的 fs 天然异步，不存在同步读文件 → 实际：三套并存，`readFileSync` 在 CLI 代码里大量出现。
- 错误认知：`await readFile(p)` 返回 string → 实际：不传 encoding 返回 Buffer，TS 类型不会撒谎。
- 错误认知：相对路径相对"源码文件所在目录"（Python 的 `Path(__file__).parent` 直觉）→ 实际：相对 `process.cwd()`；源码目录要用 `import.meta.dirname` 另取。
- 错误认知：`path.resolve` 和 `path.join` 差不多 → 实际：resolve 引入 cwd、吸收绝对段；join 只是拼接加 normalize。
- 错误认知：`process.exit` 后输出总会刷出（类比 JVM shutdown hook）→ 实际：挂起 I/O 直接丢弃，stdout 可能被截断。
- 错误认知：`process.env` 的值有类型分层（数字 / 布尔）→ 实际：清一色 `string | undefined`，全靠自己解析。

## 是否值得深入

- fs 三套 API 与常用函数：当前阶段：建议掌握——每次读 Agent 源码都会撞上。
- createReadStream / stream / backpressure：当前阶段：不需要深入——第 07 章的主题，先会认出即可。
- 权限、软链、fs.watch：当前阶段：不需要深入——低频设施，撞到再查文档。
- path 的 Windows 细节与 posix / win32：当前阶段：不需要深入——记住"拼接交给 path 模块"就够。
- process 信号处理（SIGINT / SIGTERM）：当前阶段：不需要深入——归第 15 章 CLI 生命周期。
