# 源码阅读速查表

> 定位：10~15 分钟快速过一遍，之后读源码时随查。每条一行解释，不展开论证；细节回对应章节（括号内文件名）。先看微例再看解释，或反之均可——本表假设你已读过正文，只做记忆唤醒。

## 17.1 语法速查（TS/JS）

| 形态 | 一句话 |
|---|---|
| `a?.b` | 可选链：a 为 null/undefined 时整条链短路返回 undefined，不抛错 |
| `a ?? b` | 空值合并：a 是 null/undefined 才取 b（0、""、false 都算有效值，区别于 `\|\|`） |
| `a ??= b` | 空值赋值：a 为空时才赋值，等价 `if (a == null) a = b`（常见于惰性初始化缓存字段） |
| `...arr` / `...obj` | 展开：数组按元素铺开、对象按属性铺开；函数调用/数组字面量/对象字面量三处可用 |
| `{ a, ...rest } = obj` | 解构 + 余项：a 取同名属性，rest 收剩余属性（读配置过滤代码的高频形态） |
| `` `x=${x}` `` | 模板串：反引号内插值，跨行字符串不需要拼接 |
| `x as T` | 类型断言：告诉编译器"按 T 看"，运行时零操作（CJS/ESM 互操作处常见 `as` 补类型） |
| `as const` | 冻结为字面量类型：数组变 readonly tuple、字符串变字面量联合（定义事件名/常量表用） |
| `satisfies T` | 校验但不拓宽：值满足 T，同时保留具体字面量类型（比 `: T` 多保类型，比 `as T` 多真检查） |
| `x!` | 非空断言：断言 x 不是 null/undefined（`res.body!`、`document.getElementById(...)!`） |
| `const [_, b] = arr` | `_` 惯用丢弃：解构时占位不用的变量，纯命名约定无语义 |
| `(x) => x + 1` | 箭头函数：无自己的 this，捕获外层（源码回调几乎全是它） |
| `void fn()` | void 运算符：执行 fn 并显式丢弃返回值，标记"我知道它返回 promise 但故意不等" |
| `a ? b : c` | 三元：表达式而非语句，可出现在 `const x = cond ? 1 : 2` 与 JSX/模板串里 |
| `a, b`（表达式） | 逗号表达式：从左到右求值取最后一个——for 更新段 `i++, j--` 之外少见，读到别当成笔误 |
| `outer: for(...)` | label：给循环命名供 `break outer` 跳出多层——出现即说明附近有多层循环耦合 |
| `#count` | 私有字段：真运行时私有（访问即抛错），区别于 TS 的 `private`（编译期检查、运行时无保护） |
| `get x()` / `set x(v)` | 存取器：属性语法背后跑函数——在接口/对象字面量/class 里都可定义，读源码别假设 `.x` 是纯数据 |
| `!!x` | 双重非：任意值转 boolean（`!!opts.verbose`），空串/0 得 false |
| `Object.entries(o)` | 对象转 `[key, value]` 数组，常接 `.map()`/`filter()` 做对象变换；`Object.keys/values` 同族 |
| `arr.flatMap(f)` | map 后摊平一层：`flatMap(split("\n"))` 是"每行变多行"的标准写法 |
| `parse<T>(s)` | 泛型调用：函数名后尖括号传类型参数——JSON 封装/zod 之后的取值函数签名常见 |

高频组合微例：

```ts
const { model, ...rest } = opts;          // 拆出 model，rest 继续透传
const events = ["message", "tool_call"] as const;   // 得到字面量联合类型
config.headers ??= {};                    // 惰性初始化
```

三种"约束值"写法的分界（读配置代码时最易混）：

```ts
const a: Config = { host: "x" };            // 类型标注：检查，但 host 被拓宽为 string
const b = { host: "x" } satisfies Config;   // 检查且保留字面量类型 "x"
const c = { host: "x" } as const;           // 不检查，只冻结为字面量/readonly
```

## 17.2 异步与流模式

| 形态 | 一句话 |
|---|---|
| `await p` | 等一个 Promise 出值；同步形态写异步代码，函数必须标 async |
| `async function f()` | 返回值自动包成 Promise；内部 throw 变 rejection 而非同步异常 |
| `await Promise.all([a, b])` | 并发等全部，任一 reject 整体立即 reject（≈ `asyncio.gather` / `allOf`） |
| `Promise.allSettled` | 并发等全部，永不 reject，拿到 `[{status, value/reason}]` 数组 |
| `Promise.race` | 取最先 settle 的（成或败），做超时用 |
| `Promise.any` | 取最先 fulfill 的，全败才 reject（AggregateError） |
| `for await (const x of s)` | 消费 async iterable：LLM 流、Web Stream、`events.on(...)` 的标准消费形态 |
| `async function* g()` | 异步生成器：`yield` 产出值，调用侧 `for await` 拉取——事件流风格的载体 |
| `new AbortController()` | 取消通道：`controller.abort()` 后所有持有该 signal 的 await 抛 AbortError |
| `AbortSignal.timeout(ms)` | 到点自动 abort 的 signal；`AbortSignal.any([a, b])` 并联多路信号 |
| `p.then(x).catch(e)` | 链式风格：老代码常见；链尾不接 catch 就是 unhandledRejection |
| `p.finally(fn)` | 无论成败的收尾清理（关句柄、清 loading 状态） |
| `for (const x of a) await f(x)` | 循环内 await = 严格串行；要并发先 `.map(f)` 再 `Promise.all`——读写源码都要分清 |
| `fs.readFile(p, (err, data) => {})` | 回调风格：Node 老标准，err 为 null 表示成功——读得懂即可，新代码用 promises API |
| `rs.pipe(ws)` | 管道：Readable 接 Writable，自动背压；但不传播错误 |
| `stream.pipeline(rs, tf, ws)` | 管线：同 pipe 但统一错误传播与清理——新代码的默认选择 |
| `stream.on("data", c)` | 事件式消费：push 模式，快消费者不暂停流时可能丢/积压（对照 for await 的 pull 模式） |

取消组合微例（Coding Agent 里最常见的三行）：

```ts
const ctrl = new AbortController();                 // CLI 层创建
process.on("SIGINT", () => ctrl.abort());           // 信号接入
const res = await fetch(url, { signal: ctrl.signal });  // 任一 fetch/spawn 共用
```

事件转 async iterator 微例（emitter 与 for await 的桥）：

```ts
import { on } from "node:events";
for await (const [line] of on(readline, "line")) handle(line);   // 06 的桥接用法
```

## 17.3 Node API 速记

| 形态 | 一句话 |
|---|---|
| `process.argv` | 命令行参数数组：[0]=node、[1]=脚本路径、[2..] 才是用户参数 |
| `process.env.X` | 环境变量：读 API key / base URL 的标准位置，值全为 string |
| `process.cwd()` | 当前工作目录：相对路径的解析基准（区别于 `import.meta.dirname`——脚本所在目录） |
| `process.exit(code)` | 立即退出：跳过未刷的 stdout 缓冲，CLI 源码里 exit 前常见显式 flush |
| `process.on("SIGINT", fn)` | 信号处理：Ctrl+C 默认杀进程，挂了 handler 就归你管 |
| `readFile / writeFile` | fs/promises 整文件读写：传 encoding（如 utf8）返回 string，不传返回 Buffer |
| `readdir / stat / rm / mkdir` | fs/promises 其余常客：列目录、查元信息、递归删、建目录 |
| `path.join(a, b)` | 拼路径：按平台分隔符，不做绝对化 |
| `path.resolve(a)` | 解析成绝对路径：以 cwd 为基准，读 `.`/`..`——安全检查（路径逃逸）的常客 |
| `path.relative(from, to)` | 两绝对路径的相对表示：算"文件在根目录下多深"用 |
| `readline.createInterface` | 行切分器：把字节流按行产出（stdin 逐行读的标准姿势） |
| `process.platform` / `os.homedir()` | 平台判断与用户主目录：跨平台 CLI 的两个取值点 |
| `spawn(cmd, args)` | 子进程：流式 stdio，适合长输出/交互——bash 工具的标准选择 |
| `exec(cmd)` | 子进程：shell 字符串 + 整块缓冲输出，方便但有注入与 maxBuffer 上限 |
| `execFile(cmd, args)` | 同 exec 但不经 shell、参数数组安全版 |
| `fork(module)` | spawn 的专线上阵：父子里带 IPC channel，`child.send()` 通信 |
| `Buffer.from(s)` | string → 字节（默认 utf8）；网络/文件边界处的货币 |
| `Buffer.concat([...])` | 拼接多段字节：流式收集二进制结果的收尾一步 |
| `buf.toString("utf8")` | 字节 → string；流式解码用 `TextDecoder` 带 `{ stream: true }` 防劈开多字节字符 |
| `emitter.on / emit / once` | 事件注册/触发/一次性注册：emit 是同步函数调用，不是消息队列 |
| `emitter.off / removeAllListeners` | 注销监听：会话结束、测试 teardown 的标配（防泄漏） |
| `process.stdin / stdout` | 标准流：本身是 Stream + EventEmitter，`write` 即渲染 |
| `process.stdout.isTTY` | 判断是否真终端：管道/重定向时为 false——CLI 决定要不要彩色/交互 |
| `stdin.setRawMode(true)` | 按键级输入：绕过行缓冲，TUI 前提；Ctrl+C 变普通字节要自己处理 |

spawn 骨架微例（bash 工具最小形态）：

```ts
const child = spawn(cmd, args, { signal });          // abort 自动 kill
child.stdout.on("data", (c: Buffer) => buf += c);    // 边到边收，防管道堵死
child.on("close", (code) => resolve({ code, out: buf }));
```

isTTY 分支微例（管道里跑同一 CLI 不吐乱码的原因）：

```ts
if (process.stdout.isTTY) stdout.write(color(text));  // 真终端才上色
else process.stdout.write(plain(text));               // 重定向/管道保持纯文本
```

## 17.4 工程/模块速记

| 形态 | 一句话 |
|---|---|
| `import type { X }` | 只导入类型：转译后整行消失，不会产生运行时依赖（也避免循环依赖报错） |
| `import { x } from "./x.js"` | ESM 相对导入：必须带扩展名且用 `.js`（即使源文件是 `.ts`——转译后路径不变） |
| `const x = require("pkg")` | CJS：老模块系统，同步加载；npm 老包与存量代码大量存在，会读即可 |
| `export * from "./mod"` | 重导出：聚合入口（index.ts）的标准写法；`export { x as y }` 顺带改名 |
| `"type": "module"` | package.json 字段：声明本包按 ESM 解析（`.mjs`/`.cjs` 扩展名可覆盖它） |
| `"exports"` | 入口映射表：限定外界能 import 的路径与条件分支（types/import/require）——比 main 更细 |
| `"main"` / `"types"` | 老式入口声明：无 exports 时的默认入口与类型入口 |
| `"bin"` | CLI 入口声明：`{ "pi": "dist/cli.js" }`，npm 安装时链接进 `node_modules/.bin` |
| `"scripts"` | 命令别名表：`npm run check` 即执行；无生命周期、无依赖序，就是字符串 |
| `"workspaces": ["packages/*"]` | monorepo 声明：各包依赖提升到根 node_modules 共享 |
| `"dependencies"` vs `"devDependencies"` | 运行时需要 vs 仅开发/测试需要（≈ Maven 的 compile vs test/provided scope） |
| `"peerDependencies"` | 宿主提供依赖：插件/框架适配层声明"要与你项目里的 react 同一个实例" |
| `"engines"` | 声明要求的 Node 版本区间：读它可以立刻知道项目吃哪版语法（如 22.6+ 类型剥离） |
| `"private": true` | 禁止 npm publish：根 package.json 与内部包的标配 |
| `import.meta.url / import.meta.dirname` | 当前模块文件的绝对路径：定位"脚本旁边的资源文件"（区别于 cwd） |
| `npm run xxx -w @scope/agent` | 在指定 workspace 包里执行脚本（`-w` 选包） |
| `node_modules/.bin` | 本地命令行工具入口：npx 跑的就是这里，不污染全局 |
| `.npmrc` | npm 配置：registry 换源、scope 映射私有仓库（≈ settings.xml 镜像段） |
| `package-lock.json` | 锁定整棵依赖树的精确版本与 integrity 哈希：可复现安装，提交进库 |

package.json 一眼读法微例：

```jsonc
{
  "type": "module",                    // ESM
  "bin": { "pi": "dist/cli.js" },      // CLI 入口在这
  "workspaces": ["packages/*"],        // monorepo
  "exports": { ".": "./dist/index.js" }// 外界只能 import 这个入口
}
```

## 本章只记住这 5 件事

1. `?.` `??` `??=` `...` 解构是源码出现密度最高的五个语法形态，先练到不假思索。
2. 异步三板斧：`await` 消费、`Promise.all*` 组合、`AbortController` 取消——Coding Agent 源码里的并发几乎全是它们的组合。
3. `for await` 统一了三种消费场景：LLM 流、Node Stream、emitter 事件（`on()` 包装）。
4. fs/spawn 的分工：整文件用 fs/promises，子进程一律 spawn + 流式收集 + signal。
5. package.json 五字段定乾坤：type、exports、bin、scripts、workspaces——结构、入口、工具链全在这。

## 源码识别

- 看到 `?.` `??` 连环 → 防御式取配置，脑内展开成 null 检查
- 看到 `as const` → 字面量联合类型，事件名/命令表的定义处
- 看到 `x!` → 非空断言，此处作者替编译器打包票，值得多看一眼
- 看到 `for await` → 流式消费点，顺着 iterable 找数据源
- 看到 `new AbortController()` → 取消链源头，找谁持有 controller、谁 abort
- 看到 `(err, data) =>` 双参回调 → CJS 时代异步风格，node:fs 回调版或老库
- 看到 `pipeline(` → 正确的流管线写法，错误会传播、资源会清理
- 看到 `spawn(` → 工具执行点，检查 signal / stdout 消费 / 超时三件套齐不齐
- 看到 `import type` → 纯类型依赖，转译后消失
- 看到 `from "./x.js"`（源文件却是 .ts）→ ESM 相对导入的固定后缀，不是笔误
- 看到 `satisfies` → 声明常量表且想保住字面量类型，往下通常接 `as const` 的消费代码
- 看到 `isTTY` → 输出形态分支：真终端上色/交互，管道退化为纯文本
- 看到 `import.meta.dirname` → 以脚本位置（而非 cwd）为基准定位资源

## Java/Python 工程师常见误区

- 错误认知：`??` 等价 `\|\|` → 实际：0、""、false 是有效值，只有 null/undefined 才走右侧。
- 错误认知：`as T` 是类型转换 → 实际：零运行时操作，只骗编译器；真转换要自己写。
- 错误认知：回调风格是过时写法可以无视 → 实际：node:fs 回调版与老包仍大量存在，读得懂是底线。
- 错误认知：`pipe` 会传播错误 → 实际：不会，错误处理要用 pipeline 或手动 on("error")。
- 错误认知：`from "./x.js"` 写错了目录 → 实际：TS 源码的 ESM 导入固定写 .js 后缀，转译后路径原样保留。
- 错误认知：`npm run xxx` 像 mvn phase 有依赖序 → 实际：纯命令别名，串行靠 `&&` 自己拼。

## 是否值得深入

- 17.1 全部语法形态：当前阶段：建议掌握——认不出语法就读不了行。
- Promise 组合子语义差异（all vs any vs race）：当前阶段：建议掌握——并发正确性的分水岭。
- label、逗号表达式、void 运算符：当前阶段：不需要深入——低频，读到能查即可。
- stream 高阶组合（Transform/duplex/manual pause）：当前阶段：不需要深入——速查级知道 pipeline 即可，改流式代码时回 07。
- package.json exports 条件导出全部分支：当前阶段：不需要深入——认得 `.` 入口与 types 分支即可，报错时回 10。
