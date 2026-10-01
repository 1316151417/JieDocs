# 01–05 睡前巩固

一句话主线：**类型擦除（01）→ 模块即文件（02）→ 单线程事件循环（03）→ 异步三原语（04）→ fs/path/process 薄封装（05）**。五章合起来回答一个问题：Coding Agent 源码里的代码长什么样、在哪跑、怎么异步、怎么碰文件。

## 01 TS 核心：类型只活在编译期

- 运行时零类型：`as` 不是 Java 强转（运行时零检查零动作）；`instanceof` 只认 JS 自带值；`JSON.parse(x) as User` 之后字段可能是任何值。
- 结构化类型：按形状赋值，不查类名继承链。参数要的是形状，不必找 implements 族谱。
- 默认建模 = object literal + union + 字面量类型；class、enum 都是配角（enum 用 `"a" | "b"` union 替代）。
- 最高频模式 **discriminated union**：`{ type: "success", ... } | { type: "error", ... }` + `switch (e.type)` + `assertNever`——TS 手工拼出的 sealed class：运行时靠 tag 字段分发（擦除不掉），编译期靠 never 检查穷尽。
- 值驱动类型三件套：`typeof config`（从值取类型）、`keyof`（字段名 union）、`Pick / Omit / Partial / Record`；`Awaited<ReturnType<typeof fn>>` 不 import 类型就能引用返回值类型。
- 边界数据（JSON / stdin / LLM 响应）标 `unknown`，先 narrow 再用；默认值用 `??` 不用 `||`（0 / "" / false 会被 `||` 误杀）。

## 02 模块：一文件一模块

- 可见性只有两档：export / 不 export，没有 Java 式层级。
- 现代约定只用 named export：default import 的名字随意且不可校验，是维护性陷阱。
- 只出现在类型位置的名字用 `import type`——单文件转译器（esbuild）不能自动识别删除，留成运行时导入会被 ESM 链接期直接拒绝。
- 源码是 `.ts`，import 写 `.js`：写的是**编译产物路径**（ESM 规范要求扩展名 + tsc 不重写说明符），不是笔误。
- ESM / CJS 判定：`.mjs` / `.cjs` 最优先，其次 package.json `"type"` 字段；ESM 里没有 `__dirname` / `require`，用 `import.meta.url` / `createRequire` 自己造。
- 裸包名解析 = 从当前目录**逐级向上**找 node_modules + package.json 的 exports/main；不同子树可并存同一依赖的不同版本（不像 Maven 全局一份）。

## 03 Node 运行时：单线程为什么扛 I/O

- Node = V8（执行 JS）+ libuv（事件循环 + 线程池 + OS 抽象）+ 核心模块（fs/http/stream…）。`node:` 前缀必是核心模块。
- "单线程"只约束你的 JS；I/O 不占 JS 线程——网络走 OS 非阻塞 syscall，fs/crypto/dns 走 libuv 线程池。
- 心智模型最接近 Python asyncio，但 async 是**内建的传染性语法**：底层一个函数 async 化，整条调用链只能跟着 async。
- Event Loop = 一个循环 + 若干阶段 + 若干队列：同步代码和每个回调都**执行到完成**；所有队列空、无挂起 I/O/timer → 进程退出。
- 四类全局阻塞要条件反射：`xxxSync`、大 JSON.parse、CPU 循环（diff / 加密 / AST）、正则回溯。判断口径：**同步的才阻塞，不是"有没有 await"**。
- 没有并发度旋钮（无 maxThreads）：唯一要管的是"同时挂起的任务数"，那是业务层信号量，不是线程池参数。

## 04 异步：await / 组合子 / AbortSignal

- Promise 是 **eager**：调用 async 函数即开始执行（Python coroutine 是惰性的）→ 不 await 的调用已经在跑（fire-and-forget），每个这样的调用点都要能回答"错误去哪了"。
- await 挂起的是**这个函数**——不阻塞线程、不阻塞进程，线程回 Event Loop；await 边界是并发交错点：恢复时共享状态可能已被其他任务改过。
- 组合子选型：`all` = fail-fast（其余任务不会停，只是不等了）；`allSettled` = 收全部成败（Parallel Tool Calls 标配，失败转错误消息回模型）；`race` = 超时（输家照跑）；`any` = 最快成功。
- microtask（then 回调、await 续体）在**当前同步代码之后、下一个宏任务之前**清空。
- `for await...of` 消费 async iterator（`next()` 返回 Promise）——LLM token 流与 Stream（第 07 章）的统一接口。
- 取消不在 Promise 里，在 **AbortSignal**：`AbortSignal.timeout(ms)` 超时、`AbortSignal.any([...])` 合并取消源、signal 沿调用链层层下传；abort 是协作通知不是打断——纯 CPU 循环收不到取消。
- agent loop 骨架四原语各就各位：signal 负责取消链、for await 负责流、allSettled 负责并行容错、timeout 负责兜底。

## 05 fs / path / process

- fs 三套 API 并存：`node:fs/promises` + await 是现代首选；CLI 启动期读配置用 Sync 合法；回调版只读不写。
- `readFile(p)` 不传 encoding 返回 **Buffer**，传 `"utf8"` 才是 string。
- 相对路径一律相对 `process.cwd()`——不是源码目录（Python `__file__` 直觉在这里是错的）；agent 的 cd 工具 = `process.chdir(dir)`，路径含义随会话漂移。
- `path.join` 只拼接；`path.resolve` 求绝对路径（无绝对段时拼 cwd，遇绝对段丢弃前面参数）——工具边界最常见写法 `path.resolve(cwd, p)`。
- `process.argv` 参数从下标 **2** 开始（0 是 node，1 是脚本）；`process.env` 全是 `string | undefined`；`process.exit` 立即退出并丢弃挂起输出（温和版：`process.exitCode` 让循环自然排空）。
- 两个"在哪"要分清：`process.cwd()` = 进程在哪（工具路径锚点）；`import.meta.dirname` = 源码在哪（内置资源锚点）。
- read/write/edit 工具 = fs + path 的薄封装：resolve 锚定 → stat 校验 → readFile → 行号化文本喂回模型；CLI 凭据 = `process.env` + 启动期快速失败。

## 睡前自测（能秒答就过关）

1. `JSON.parse(raw) as User` 之后 `u.name` 一定是 string 吗？→ 不一定。类型擦除，运行时零校验。
2. 源码 import `"./tool.js"` 但磁盘上是 tool.ts，是 bug 吗？→ 不是。写的是编译产物路径，ESM 标准 形态。
3. `readFileSync` + `JSON.parse(50MB)` 卡住的是谁？→ 整个进程。唯一 JS 线程被占，所有连接的回调一起排队。
4. `llmCall()` 忘了 await，请求发出去了吗？→ 发出去了（Promise eager）。Python 裸调用什么都不发生的直觉在这里是错的。
5. `Promise.all` 里一个 reject，其他任务停吗？→ 不停。fail-fast 只是"不等了"，结果被丢弃；要等全部用 allSettled。
6. 用户按 Esc 怎么取消在飞的 fetch？→ AbortController.abort() + signal 层层下传。Promise 本身没有 cancel。
7. `path.join("a", p)` 和 `path.resolve("a", p)` 差在哪？→ join 纯拼接；resolve 求绝对路径（p 是绝对段时 "a" 被丢弃）。
8. `||` 做默认值哪里危险？→ 0 / "" / false 被误换成默认值，应该用 `??`。
9. ESM 文件里 `__dirname` 能用吗？→ 不能。用 `dirname(fileURLToPath(import.meta.url))` 或 `import.meta.dirname`。
10. 怎么让一个 setInterval 不阻止进程退出？→ 调它的 `.unref()`。
