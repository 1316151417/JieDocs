# Java/Python 工程师的 Node.js + TypeScript 阅读地图

你的存量经验里，大约七成可以直接迁移到 Node/TS：静态类型、模块化、依赖管理、异步编排，概念层面全都有对应物。真正的新东西是剩下的三成：类型会在"编译"后消失、运行时是单线程事件循环、依赖被完整复制进项目目录。本章先把边界画清楚——四个名词各是什么、三层结构怎么切、一个项目从源码到运行经过哪些环节——再给出全套教材的知识地图和阅读路线。

## 1. 四个名词，各自是什么

### TypeScript：一层会消失的类型

TypeScript = JavaScript + 类型系统 + 少量语法扩展（interface、泛型等）。它**不是独立运行时**：`.ts` 文件不能直接执行，必须先编译——准确说是转译（transpile）——成 `.js`，且转译时类型标注**全部擦除**。

最近对应物：mypy 风格的类型注解。但有两点不等价：

- mypy 是语言外挂，可装可不装、可不跑；TS 类型检查内建于标准工具链（tsc / 编辑器），默认强制执行。
- Java 的类型保留到运行时（`instanceof`、反射、`getClass()` 都依赖它）；TS 的类型在转译后**彻底不存在**，运行中的代码没有任何手段询问"这个值的 TS 类型是什么"。

### JavaScript：语言核心 + 宿主 API

JavaScript 不是一个单一精确的东西，它 = ECMAScript 语言规范（语法、对象、Promise、模块……）+ 宿主环境提供的 API。同一门语言，装进不同宿主就是不同的"JS"：

```
                ECMAScript 语言核心
     （语法 / 对象 / Promise / class / 模块）
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
   浏览器宿主 API              Node.js 宿主 API
   DOM / window /              fs / path / process /
   document / localStorage     net / child_process
```

所以 **Node.js ≠ 浏览器里的 JS**：语言核心相同（`async/await`、`Map`、class 两边都能跑），API 面完全不同——Node 里没有 `document` / `window`，浏览器里没有 `fs` / `process`（少数 API 两边都有，如 `fetch`，Node 18+ 起内置）。源码里出现 `import fs from "node:fs"` 即可断定这是 Node 侧代码，搬进浏览器必然报错。最近类比：Python 语言核心与宿主环境的关系——但 Python 标准库跨宿主基本一致，JS 的宿主 API 天生分裂，这是历史包袱。

### Node.js：V8 + libuv 打包成的服务端运行时

Node.js 把 Chrome 的 JS 引擎 V8（角色对应 JVM：真正执行代码的虚拟机）和 libuv（事件循环 + 异步 I/O 封装）打包成一个可执行程序，附一组服务端 API。它是**单进程、主线程单线程**的运行时，靠事件循环 + 非阻塞 I/O 获得并发。心智模型最接近 Python asyncio（一个主循环 + 协作式任务），而不是 Java 的每请求一线程。细节在第 03 章展开。

### npm：包管理器 + 中央仓库

npm 一词指三样东西：CLI 工具（`npm install`）、包清单格式 package.json（对照 pom.xml / pyproject.toml）、中央仓库 registry（对照 Maven Central / PyPI）。与 Maven 最大的行为差异：依赖不装进全局 `~/.m2` 共享，而是完整复制进**每个项目的 node_modules 目录**。副作用是仓库 clone 下来自带全部依赖源码，读依赖实现比 Java 方便得多。

### 四者关系一句话

TS 转译成 JS，JS 跑在 Node 上，npm 负责安装 TS/JS 包；TS 与 npm 服务于开发期，Node 是唯一的运行时。

## 2. 三层边界：编译期 / Runtime / Package Manager

读 Node 项目时，心里要把任何一段代码归到三层之一。混乱多半来自层间混淆——最常见的就是以为 TS 类型在运行时生效。

| 层 | Java | Python | Node 生态 |
|---|---|---|---|
| 编译 / 检查 | javac → 字节码，类型保留到运行时 | mypy（可选外挂，不强制） | tsc → JS，类型**擦除** |
| Runtime | JVM | CPython | Node.js（V8 + libuv） |
| 包管理 | Maven / Gradle + `~/.m2` | pip + PyPI / site-packages | npm + 项目内 node_modules |

编译线自上而下：

```
TypeScript
    ↓ compile / transpile（类型擦除）
JavaScript
    ↓
Node.js Runtime（V8 + libuv）
    ↓
OS
```

每一跳的对照：

- TS → JS：javac 同样是"检查 + 翻译"，但字节码携带类型信息供运行时反射使用；tsc 的产物把类型删得干干净净，类型只存在于源码与编译期报错里。
- JS → Node：类比 `.class` 交给 JVM。Node 不关心 JS 是手写还是 tsc 生成的。
- Node → OS：libuv 把异步 I/O 派发给系统调用或内部线程池，对 JS 层完全隐藏——类比 asyncio 底层的 selector + 线程池，但内建于运行时、无法绕开。

包管理线（独立于编译线）：

```
package.json
    ↓
npm（依赖解析）
    ↓
node_modules / workspace
    ↓
Node.js
```

`npm install` 把依赖树写进 node_modules（monorepo 里是根 node_modules，由 workspaces 共享）；Node 运行时遇到 `import "x"` 从 node_modules 查找（第 02、11 章）。两条线在进程启动那一刻汇合。

## 3. 一个现代 Node 项目从源码到运行

以典型的 monorepo 型 Coding Agent 为例（如本仓库 pi：packages/ai、packages/agent、packages/tui、packages/coding-agent）。根 package.json 通常长这样：

```json
{
  "name": "pi-monorepo",
  "private": true,
  "workspaces": ["packages/*"],
  "scripts": {
    "check": "tsc --noEmit",
    "dev": "tsx packages/coding-agent/src/main.ts"
  }
}
```

从 clone 到跑起来的完整链路：

```
git clone ─→ npm install ─→ npm run dev
                                     │
                                     ↓
              scripts.dev = "tsx packages/.../main.ts"
                                     │
        ┌────────────────────────────┼────────────────────────────┐
        ↓                            ↓                            ↓
   tsx 即时转译                  import 解析                   事件循环启动
   擦除类型，内存中              逐级向上查找                  异步 I/O 派发，
   生成 JS 交给 Node             node_modules/<pkg>            回调串行执行
```

拆开看五个环节：

1. **源码 .ts**：开发者写 TypeScript，类型标注齐全，编辑器里实时检查。
2. **类型检查**：`tsc --noEmit` 只检查、不产出文件，跑在 CI 或编辑器里。看到 `--noEmit` 要想到"这一步不产生任何 JS"。
3. **转译 / 打包**：开发期用 tsx 即时转译后直接运行（底层 esbuild）；发布期用 tsc / esbuild 转译进 dist/，或 bundle 成单文件（类比 Maven shade）。新版 Node 还内置了类型剥离（type stripping，22.6 引入需 `--experimental-strip-types`，23.6 起默认开启），可以直接 `node xxx.ts`——同样只删类型、不做检查。
4. **Node 执行**：`node dist/index.js`。此刻进程里没有任何 TS 痕迹，类型错误不可能在这一步被发现。
5. **依赖解析**：运行中遇到 `import { z } from "zod"`，Node 从当前文件所在目录逐级向上查找 `node_modules/zod`，读它的 package.json（exports / main 字段）决定入口文件。monorepo 中各包的依赖被提升（hoist）到根 node_modules 共享（第 11、12 章）。

这条链上最值得记住的对照：Java 里你读 `.java`，运行的是不反编译就看不了的 `.class`；Node 里你读的 `.ts` 与运行产物之间只隔一次"删类型"，**源码几乎就是全部真相**。

## 4. 全套教材知识地图

```
Node.js + TypeScript 源码阅读能力
│
├── 一、TS 语言 ─────────────────────── 01, 02
│   ├── 类型标注 / interface / type / 泛型 / union（01）
│   └── ESM import / export / 模块解析（02）
│
├── 二、Node Runtime ────────────────── 03, 04
│   ├── V8 + libuv / 事件循环（03）
│   └── Promise / async / await / 并发原语（04）
│
├── 三、Node 核心 API ───────────────── 05 ~ 09
│   ├── fs / path / process（05）
│   ├── EventEmitter（06）
│   ├── Stream（07）重点
│   ├── Buffer（08）
│   └── child_process（09）重点
│
├── 四、npm 与项目结构 ──────────────── 10 ~ 13
│   ├── package.json 详解（10）
│   ├── npm / lockfile / node_modules（11）
│   ├── monorepo / workspaces（12）重点
│   └── 构建与工具链（13）
│
├── 五、Coding Agent 专项 ───────────── 14 ~ 16
│   ├── 错误处理（14）
│   ├── CLI 与终端（15）
│   └── 架构串讲（16）重点，终章
│
└── 六、速查 ────────────────────────── 17, 18
    ├── 源码阅读速查表（17）
    └── Java/Python/Node 概念映射表（18）
```

六大块的分工：一、二解决语言与执行模型；三解决 Node 特有 API（Coding Agent 的武器库）；四解决项目组织与构建；五把前面所有知识拼进真实 agent 架构；六是字典。

## 5. 阅读顺序与可跳过项

第一遍按序号顺序读 00 → 16（约 6 小时 50 分钟）：语言（01 02）→ 模型（03 04）→ API（05~09）→ 工程（10~13）→ 专项收尾（14~16）。

第一遍可以直接跳过：

- Buffer 的编码与二进制细节（08 速读，知道它是字节容器即可）
- CJS 的历史沿革、CJS/ESM 互操作的边角规则（能认出 `require` 语法就够，第 02 章会给最小集合）
- 构建工具配置细节（tsconfig 全量编译选项、bundler 插件机制；读懂项目现有配置即可）
- 各章内标注【暂时跳过】的段落——低频细节，知道存在即可，需要时再查

第二遍按需查阅：17、18 当字典随手翻；改流式输出相关代码前重读 07；改命令执行前重读 09；接手 monorepo 时回查 12；类型报错看不懂时回 01。

## 6. 第一眼词汇表

读 Node 项目的 README、package.json、源码注释时最先撞上的名词：

| 名词 | 含义 | 最近对照 |
|---|---|---|
| TS / JS | TypeScript / JavaScript | — |
| ESM | ECMAScript Modules，`import` / `export` 标准模块系统 | Java / Python 的 import |
| CJS | CommonJS，旧模块系统：`require()` / `module.exports` | 老式模块约定，无精确对应 |
| transpile | 转译：TS → JS，类型擦除 | javac（但产物不保留类型） |
| bundle | 把多模块及其依赖打成单文件（esbuild / rollup） | Maven shade |
| npm | 包管理器 + 中央仓库 | Maven + Maven Central |
| node_modules | 项目内依赖目录，扁平化布局 | `~/.m2`（但在项目里、源码可读） |
| lockfile | package-lock.json，锁定精确版本 | Gradle lockfile / pip constraints |
| workspace | npm workspaces：monorepo 多包共享 node_modules | Maven 多模块（reactor） |
| tsx | 开发期即时转译并运行 TS 的工具，底层 esbuild | 无（Java 无此形态） |
| TUI | Terminal UI，终端字符界面 | jline + jansi 拼出来的东西 |
| V8 | Node 内嵌的 JS 引擎 | JVM |
| libuv | 事件循环与异步 I/O 的底层 C 库 | asyncio 的 selector 层 |
| REPL | 裸敲 `node` 进入的交互环境 | jshell / 裸敲 `python` |
| devDependency | 仅开发期需要的依赖（devDependencies 字段） | Maven 的 test / provided scope |
| registry | npm 包仓库服务器，可换源（.npmrc） | Maven Central / 镜像 |

## 本章只记住这 5 件事

- TypeScript 不是运行时：转译后类型全部擦除，运行时没有任何 TS 类型信息。
- JavaScript = ECMAScript 语言 + 宿主 API；浏览器 JS 与 Node JS 同语言、不同 API 面，互不通用。
- Node.js = V8 + libuv 的单线程事件循环运行时，心智模型是 asyncio，不是 Java 线程池。
- 三层边界各归各：tsc（编译期，对应 javac）、Node（运行时，对应 JVM）、npm（包管理，对应 Maven）。
- 依赖装在项目内的 node_modules，import 从那里逐级向上解析；monorepo 由 workspaces 提升共享。

## 源码识别

- 看到 `.ts` / `.tsx` 文件 → 想到运行前必有转译环节（构建进 dist/，或由 tsx / Node 类型剥离即时处理）
- 看到 `import fs from "node:fs"` → 想到 Node 内置模块（`node:` 前缀是标志），不来自 node_modules
- 看到 `import x from "@scope/pkg"` → 想到 monorepo 内部包或 npm scope 包（第 12 章）
- 看到 `process.env.XXX` → 想到 `System.getenv()` / `os.environ["XXX"]`
- 看到 `export default` → 想到默认导出，import 侧名字可以随便起（与命名导出不同，第 02 章）
- 看到 `tsc --noEmit` → 想到纯类型检查，不产出任何 JS
- 看到 `npm run xxx` → 想到执行 package.json 的 scripts 字段，近似 mvn 的 goal
- 看到 `node_modules/.bin/` → 想到本地安装的 CLI 工具入口，npx 调用的就是它

## Java/Python 工程师常见误区

- 错误认知：TS 类型像 Java 一样运行时可用（instanceof 接口、反射拿泛型）→ 实际：转译后类型全部消失，运行时只有普通 JS 对象，任何"运行时类型检查"都要自己写。
- 错误认知：Node 像 Tomcat 一样一个请求一个线程 → 实际：主线程只有一个事件循环，所有回调串行执行；一个 CPU 密集任务会卡住整个进程，重活要丢给子进程或 worker_threads。
- 错误认知：npm 像 Maven 一样把依赖放全局仓库按需引用 → 实际：依赖完整复制进每个项目的 node_modules，目录可删可重建，用磁盘换隔离。
- 错误认知：`require` / `module.exports` 是可以无视的历史 → 实际：存量代码、npm 上的老包、大量文档仍是 CJS；必须能读（会认即可，第 02 章）。
- 错误认知：async/await 与 Python 语义完全相同 → 实际：九成相同，但未处理的 Promise rejection 在 Node 15+ 默认直接 crash 进程，且并发没有 `asyncio.gather` 的一站式 API（第 04 章）。

## 是否值得深入

- TS 类型系统（泛型、union、类型收窄）：当前阶段：建议掌握 —— 类型签名就是源码里的函数文档，读不懂等于少读一半注释。
- 事件循环内部阶段（timers / poll / check 时序细节）：当前阶段：不需要深入 —— 记住"单线程 + 微任务先于宏任务"即可，需要时再查。
- V8 内部与内存调优：当前阶段：不需要深入 —— 与读源码无关，排查内存问题时再查。
- Stream 与 backpressure：当前阶段：建议掌握 —— LLM 流式输出的底层机制，Coding Agent 核心路径。
- Buffer 编码细节：当前阶段：不需要深入 —— 当字节容器用，遇到编码问题再查。
- CJS/ESM 互操作边角规则：当前阶段：不需要深入 —— 会认两种语法、知道 default import 的坑即可，报错时再查。
- npm 依赖解析与 lockfile：当前阶段：建议掌握 —— 看懂"这个版本从哪来"是安全改依赖的前提。
- 构建工具链配置：当前阶段：不需要深入 —— 能读懂项目现有 tsconfig / scripts 即可，要加构建需求时再查。
