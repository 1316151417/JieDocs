# Node.js + TypeScript 源码阅读指南（Java/Python 工程师向）

## 定位

本教材面向有多年 Java 后端经验（Spring Boot / Kafka / 线程池），熟悉 Python 与 asyncio，做过 LLM Agent / LangGraph / Coding Agent 项目的工程师。目标不是"学会从零开发 Node 项目"，而是**获得阅读现代 TypeScript / Node.js 项目源码的能力，并能安全地修改**，重点覆盖 AI Coding Agent 类项目的技术面：流式输出、子进程执行、CLI/TUI、monorepo。

写法以知识迁移为主线：每个概念先给 Java/Python 中的最近对应物，再重点讲差异与错误类比——凡说"相似"必说清哪里不等价。心智模型优先于 API 罗列：不装环境、不讲通用编程概念、不做 API 手册式清单。示例均为 5~30 行真实源码风格短片段，多处取材自 monorepo 型 Coding Agent 项目的典型结构。

第一遍通读约 6~7 小时，之后作为读源码时的查阅手册使用。

## 不覆盖的内容

- 浏览器端 JS：DOM、前端框架（React/Vue）、浏览器侧构建链
- 部署与运维：PM2、容器化、性能调优、集群
- 类型体操：条件类型、infer 递归等高级类型编程（读不懂时再回查 01）
- 测试框架专讲（vitest 只在第 13 章作为工具链一环提及）
- Node C++ 扩展、V8 与 libuv 源码内部

## 目录

| 文件 | 标题 | 预计阅读时间 | 必读/选读 | 一句话说明 |
|---|---|---|---|---|
| [00-overview.md](00-overview.md) | Java/Python 工程师的 Node.js + TypeScript 阅读地图 | 15 分钟 | 必读 | 四大概念边界、编译/Runtime/包管理三层结构、知识地图与阅读路线 |
| [01-typescript-essential.md](01-typescript-essential.md) | TypeScript 核心（源码阅读所需） | 45 分钟 | 必读 | 类型标注、interface/type、泛型、union、类型收窄：读懂 .ts 的最小集合 |
| [02-typescript-modules.md](02-typescript-modules.md) | 模块系统与 import/export | 20 分钟 | 必读 | ESM 语法、default/named export、模块解析；CJS 只学认读 |
| [03-node-runtime.md](03-node-runtime.md) | Node.js Runtime 与 Event Loop 模型 | 20 分钟 | 必读 | V8 + libuv、单线程事件循环；对照 Java 线程模型与 asyncio |
| [04-async-programming.md](04-async-programming.md) | 异步编程：Promise / async / await | 40 分钟 | 必读 | Promise 链、并发原语、错误传播；对照 CompletableFuture 与 asyncio 的差异 |
| [05-filesystem-path-process.md](05-filesystem-path-process.md) | fs / path / process | 20 分钟 | 必读 | 文件、路径、进程环境：Coding Agent 读写仓库的三大基石 |
| [06-events.md](06-events.md) | EventEmitter 与事件模型 | 20 分钟 | 必读 | Node 内置观察者模式；agent 事件流与日志流的底座 |
| [07-stream.md](07-stream.md) | Stream（重点章） | 35 分钟 | 必读 | Readable/Transform/Writable 与 backpressure：LLM 流式输出的底层机制 |
| [08-buffer-binary.md](08-buffer-binary.md) | Buffer 与二进制 | 10 分钟 | 速读 | 字节容器与编码的最小认知，知道存在即可 |
| [09-child-process.md](09-child-process.md) | child_process（重点章） | 30 分钟 | 必读 | spawn/exec、stdio 管道、子进程生命周期：agent 执行 shell 命令的核心 |
| [10-package-json.md](10-package-json.md) | package.json 详解 | 25 分钟 | 必读 | 依赖、scripts、exports/bin；对照 pom.xml 与 pyproject.toml |
| [11-npm-lock-node-modules.md](11-npm-lock-node-modules.md) | npm / lockfile / node_modules | 15 分钟 | 必读 | 扁平化 node_modules 与版本锁定；对照 ~/.m2 与 lockfile 语义 |
| [12-monorepo-workspace.md](12-monorepo-workspace.md) | Monorepo 与 npm workspaces（重点章） | 25 分钟 | 必读 | 多包仓库结构；对照 Maven 多模块，现代 Coding Agent 主流布局 |
| [13-build-toolchain.md](13-build-toolchain.md) | 构建与工具链 | 15 分钟 | 必读 | tsc / tsx / esbuild / vitest 各自的职责与从源码到运行的链路 |
| [14-error-handling.md](14-error-handling.md) | 错误处理 | 20 分钟 | 必读 | Error 子类、error.cause、未捕获异常与退出码；受检异常缺失下的纪律 |
| [15-cli.md](15-cli.md) | CLI 与终端 | 20 分钟 | 必读 | stdin raw mode、ANSI 转义、TUI：交互式 agent 的输入输出层 |
| [16-coding-agent-architecture.md](16-coding-agent-architecture.md) | Coding Agent 架构串讲（终章） | 35 分钟 | 必读 | 把 TS、Stream、子进程、事件模型拼装成一个完整 agent 的数据流 |
| [17-source-reading-cheatsheet.md](17-source-reading-cheatsheet.md) | 源码阅读速查表 | 10 分钟 | 随时翻 | 读源码时反复出现的模式速查：导入、导出、异步、配置识别 |
| [18-java-python-node-map.md](18-java-python-node-map.md) | Java/Python/Node 概念映射表 | 10 分钟 | 随时翻 | 三方概念对照，遇到陌生名词先查这里 |

## 使用约定

- 深度标注三级：【必须掌握】读懂源码必需；【看懂即可】见到能认出、不必会写；【暂时跳过】低频细节，一句话带过，知道存在即可，需要时再查。
- 各章结尾固定四节：本章只记住这 5 件事 / 源码识别 / Java/Python 工程师常见误区 / 是否值得深入，用于快速复习与自查。
- 正文中的"对照"均指 Java/Python 最近对应物；紧随的"不等价"是该类比最容易踩的坑。
- 示例代码默认为 TypeScript 或 JSON，语言标注在代码块首行；ASCII 图示不加语言标注。

## 推荐阅读顺序

第一遍通读（按序号 00 → 16，约 6 小时 50 分钟）：

1. 语言层：00 → 01 → 02（约 1 小时 20 分）——先解决"看得懂语法"
2. 模型层：03 → 04（约 1 小时）——建立"单线程事件循环"心智模型
3. API 层：05 → 06 → 07 → 08 → 09（约 1 小时 55 分）——Node 宿主 API，Coding Agent 的武器库；07、09 是重点章
4. 工程层：10 → 11 → 12 → 13（约 1 小时 20 分）——看懂项目组织与构建链
5. 收尾：14 → 15 → 16（约 1 小时 15 分）——终章把全书知识拼进一个真实 agent 架构

第一遍可跳过：08 速读；CJS 历史与构建工具配置细节；各章标注【暂时跳过】的段落。

第二遍按需查阅：

- 17、18 不必顺序读，读源码卡住时随手翻
- 动手改流式输出相关代码前重读 07；改命令执行前重读 09
- 接手 monorepo 项目时回查 12；类型报错看不懂时回查 01
- 想确认某个 Java/Python 概念在 Node 里的对应物时查 18

## 时间预算

第一遍通读（00~16）约 6 小时 50 分钟；19 章全部合计约 7 小时 10 分钟，落在"4~8 小时完成第一遍"的设计区间内。标注时间按"阅读 + 对照自身经验"估算，不含动手改代码的时间。

## 各部分说明

- **TypeScript 部分（01、02）**：语言与模块，解决"这行代码什么意思"。类型部分按源码阅读所需裁剪，不覆盖类型体操。
- **Node Runtime 部分（03、04）**：执行模型，解决"这段代码何时跑、谁先谁后"；事件循环对照 Java 线程模型与 asyncio。
- **核心 API 部分（05~09）**：Node 区别于浏览器 JS 的宿主 API，也是 Coding Agent 的主要武器库；07 Stream 与 09 child_process 最重要。
- **工程与 npm 部分（10~13）**：项目怎么组织、依赖从哪来、源码怎么变成可运行产物。
- **Coding Agent 专项（14~16）**：错误处理与终端交互，终章以真实架构串讲收束全书。
- **速查（17、18）**：不用于顺序阅读，读源码时当字典翻。
