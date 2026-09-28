# Java / Python / Node.js 概念映射总表

> 定位：读 Node 源码时"这个我在 Java/Python 里见过"的快速校准表。类比等级规则：【可直接类比】= 直觉直接用；【部分类比】= 形似但有关键差异，差异一句话给出；【不应类比】= 概念表面同名/近名，本质不同，套用必错。建议通读一遍 18.19 的 Top 8，再回头按主题查。

## 18.1 线程与并发模型

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 并发单位 | Thread / ExecutorService 线程池 | threading / asyncio.Task | 事件循环上的回调与 async 调用 | 【部分类比】Node 无每任务一线程，全在一个线程交错 |
| 并行受限 | 线程真并行 | GIL 限制 CPU 并行（IO 并行可行） | 主线程只有一个，CPU 密集卡全局 | 【不应类比】GIL 是解释器锁、线程真实存在；Node 是根本没有多线程执行 JS |
| 重活卸载 | 独立线程池 | ProcessPoolExecutor / 子进程 | worker_threads（隔离的 V8 实例）或子进程 | 【部分类比】worker 是独立 isolate，不是共享堆的线程 |
| 同步原语 | synchronized / Lock | threading.Lock / asyncio.Lock | 无内建锁——单线程天然免竞态（跨 await 才有交错） | 【不应类比】心智模型不同：不是"锁更少"，是"没有并行" |

## 18.2 异步

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 主形态 | CompletableFuture | coroutine + await | Promise + await | 【可直接类比】语法与语义高度同构 |
| 事件循环归属 | JVM 无内建循环（框架自带） | asyncio.run() 自建循环 | Node 进程即循环，无法绕开 | 【部分类比】Node 是运行时强制，asyncio 是可选库 |
| 入口阻塞 | future.get() | asyncio.run(main()) | 顶层 await（ESM）或 Promise 阻塞在事件循环自然驱动 | 【部分类比】Node 里"忘了 await"不阻塞，只会静默丢结果 |
| 未处理异常 | Future 无消费者则吞 | Task 未 await 时异常存于 Task | unhandledRejection 默认 crash 进程 | 【不应类比】Node 把它当致命错误，比 Java/Python 严格 |

## 18.3 Future / Task

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 句柄类型 | Future / CompletableFuture | asyncio.Future / Task | Promise | 【可直接类比】"未来才有值的句柄"一致 |
| 创建即运行 | supplyAsync() 立即执行 | ensure_future() / create_task() | 调用 async 函数即创建、立即调度 | 【部分类比】JS 无"冷启动"概念，没有 Python 里 coroutine 不 create 不跑的中间态 |
| 组合 | allOf / anyOf | gather / wait | Promise.all / allSettled / any / race | 【可直接类比】命名映射整齐，race 语义 Java 无直接对应 |
| 取消 | future.cancel(true) | task.cancel() | Promise 不可取消——用 AbortSignal 约定 | 【不应类比】取消是协作式信号，不是句柄自带能力 |

## 18.4 Stream

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 字节/字符流 | InputStream / Reader | file-like / open() | node:stream Readable / Writable | 【部分类比】同为逐步处理，Node 流是异步事件驱动 |
| 惰性产出 | Stream API（惰性中间操作） | generator / 惰性迭代器 | async generator / Readable | 【可直接类比】async generator ≈ async 版 generator |
| 背压 | Reactive Streams（Flow API，后补） | 无内建（asyncio 队列手搓） | 内建于 pipe：write 返回 false、read 暂停 | 【部分类比】Node 背压是默认机制，不是外挂规范 |
| 管道组合 | `a.pipe(b)`（JDK 9+） | 无标准组合 | pipe / pipeline（含错误清理） | 【部分类比】Java pipe 是同步字节搬移，Node 是异步含背压 |

## 18.5 事件

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 进程内事件 | EventListener / Guava EventBus | 回调列表 / PyDispatcher | EventEmitter | 【部分类比】同为进程内分发；EventEmitter 无注解/接口，靠事件名字符串 |
| 分发语义 | EDT 派发或同步调用 | 同步调用 | emit = 同步函数调用，listener 按注册序执行 | 【部分类比】无独立派发线程，在 emit 调用者的栈里跑 |
| 消息中间件 | Kafka / RabbitMQ | Celery 等 | ——（EventEmitter 不是） | 【不应类比】无持久化/异步/重试/跨进程，见 Top 8 第 1 条 |

## 18.6 文件与路径

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 路径对象 | java.nio.file.Path | pathlib.Path | path 模块（纯字符串函数，非对象） | 【部分类比】Node path 返回 string，无链式 Path 对象 |
| 文件读写 | Files.readString() | Path.read_text() | fs/promises readFile / writeFile | 【可直接类比】Promise 版一一对应 |
| 目录操作 | Files.list / walk | iterdir / rglob | readdir / 需自己递归（或 fswalk 类库） | 【部分类比】Node 标准库无递归 walk |
| 文件监听 | WatchService | watchdog（三方） | fs.watch（各平台行为不一） | 【部分类比】语义对齐，稳定性都一般 |

## 18.7 进程

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 启动子进程 | ProcessBuilder.start() | subprocess.run / Popen | spawn / exec / execFile | 【可直接类比】spawn ≈ Popen（拿句柄），exec ≈ run（拿结果） |
| 流式输出 | process.getInputStream() | Popen.stdout 逐行读 | child.stdout 是 Readable，on("data") / for await | 【可直接类比】都是"读管道"，Node 侧是异步流 |
| 环境与目录 | builder.environment() / directory() | env= / cwd= | options.env / options.cwd | 【可直接类比】 |
| 结束与信号 | waitFor / destroy / destroyForcibly | wait / terminate / kill | child.on("close") / kill(signal) | 【部分类比】Node 默认 SIGTERM，signal 可指定；kill 名字误导（不是只能 SIGKILL） |
| 专属子进程 | —— | multiprocessing（fork/spawn） | fork()：子进程带 IPC channel | 【部分类比】Node fork 本质是 spawn 同一 runtime + 通信通道 |

## 18.8 模块

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 单元 | package（目录+类） | module（一文件）/ package（目录+`__init__`） | 一文件一模块（ESM/CJS 两套语法） | 【部分类比】Node 有两代模块系统并存，读源码要会认两套 |
| 导入 | import com.x.Y（编译期全限定） | import / from ... import | import / export（运行时解析路径） | 【部分类比】Node 的 import 是表达式级的运行时动作，路径必须带扩展名 |
| 可见性 | public/private/protected | `_` 约定 / `__` 名称改写 | export 与否二值；`#` 运行时私有字段 | 【部分类比】模块级只有导出/不导出，无包私有 |
| 命名空间 | package 唯一性（classpath 决定） | 包各自独立 | node_modules 嵌套可同包多版本共存 | 【不应类比】见 Top 8 第 7 条 |

## 18.9 包与发布

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 产物 | jar（class 集合） | wheel | npm 包（源码/转译后 js + package.json） | 【部分类比】npm 包通常直接是可读 JS，接近"发布源码" |
| 坐标 | groupId:artifactId:version | name + version | name + version；scope 包 `@scope/name` | 【部分类比】scope 前缀兼作组织命名空间与权限边界 |
| 中央仓库 | Maven Central | PyPI | npm registry | 【可直接类比】可换源/私服（.npmrc ↔ settings.xml） |

## 18.10 依赖管理

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 清单 | pom.xml / build.gradle | pyproject.toml | package.json | 【可直接类比】 |
| 锁定 | 无官方 lock（Gradle 有可选） | uv.lock / pip-tools | package-lock.json（官方默认生成） | 【部分类比】npm 锁定是常态且必提交 |
| 版本范围 | Maven 区间（默认精确） | PEP 440（常精确） | semver：`^1.2.3` `~1.2.0` 默认带范围 | 【部分类比】"最小改动升级补丁"哲学，lock 才是真相 |
| 安装位置 | ~/.m2 全局共享 | venv site-packages 项目内 | node_modules 项目内（monorepo 提升到根） | 【部分类比】Node 与 venv 相近、与 .m2 相反；见 Top 8 第 4、5 条 |

## 18.11 构建工具

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 主工具 | Maven / Gradle | build backend（setuptools/hatch） | tsc / esbuild + npm scripts | 【部分类比】Node 无统一构建器，工具按环节拼装 |
| 生命周期 | phase 有序（validate→test→package） | hooks（可选） | scripts 无序纯别名 | 【不应类比】见 Top 8 第 8 条 |
| 转译 | javac（检查+字节码） | 无对应（mypy 不产出） | tsc / esbuild / tsx（擦类型） | 【部分类比】tsc 产物丢类型，与 javac 保留类信息相反 |
| 打包 | shade / assembly | wheel | esbuild bundle 单文件 | 【可直接类比】bundle ≈ shade |

## 18.12 异常

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 分级 | checked / unchecked | 无 checked | 无 checked，全 unchecked | 【可直接类比】与 Python 一致：编译器不强制处理 |
| 异步错误 | ExecutionException 包装 | await 时抛出 | Promise rejection / async throw，await 处统一 | 【可直接类比】 |
| 未捕获后果 | Thread 默认打印+线程死 | 打印 traceback | uncaughtException / unhandledRejection 默认 crash 进程 | 【部分类比】Node 更严格，尤其 unhandledRejection |
| 错误信号量 | Exception 类层次 | Exception 类层次 | Error 类 + err.code 属性约定 | 【部分类比】Node 靠 code 字符串（如 ENOENT）细分，类型系统不建模 |

## 18.13 CLI 参数

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 原始输入 | main(String[] args) | sys.argv | process.argv（前两项是 node 与脚本路径） | 【部分类比】Node 需先切掉两个元素 |
| 解析库 | picocli / commons-cli | argparse / click | commander / yargs / 自写 | 【可直接类比】commander ≈ argparse 的声明风格 |
| 子命令 | picocli 子命令 | click.group | commander.action / 自写 switch | 【可直接类比】 |

## 18.14 环境变量

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 读取 | System.getenv("X") | os.environ["X"] | process.env.X | 【可直接类比】 |
| 类型 | String | str | string（undefined 表示缺失） | 【部分类比】访问不存在的键得 undefined 而非抛错（Python 会 KeyError） |
| 写入 | 不可（启动时固定） | 可改 os.environ | 可改 process.env（影响后续 spawn 的 env） | 【部分类比】Node 里 env 是可变对象，测试里常临时改 |

## 18.15 序列化

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 主库 | Jackson | json 标准库 | 内置 JSON.parse / stringify | 【可直接类比】一行级对应 |
| 数据类 | POJO + 注解 | dataclass | TS interface（纯类型，运行时不存在） | 【部分类比】解析结果不自动校验，边界要 zod 之类 schema 库补 |
| 运行时校验 | Bean Validation 注解 | pydantic | zod / valibot | 【可直接类比】pydantic ≈ zod 的角色 |

## 18.16 HTTP

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 标准客户端 | java.net.http.HttpClient | urllib（少用） | fetch（18+ 内置，底层 undici） | 【可直接类比】fetch 即浏览器同款 API |
| 常用三方 | OkHttp | httpx / requests | undici / got / axios | 【可直接类比】 |
| 流式响应体 | BodyHandlers.ofInputStream() | response.iter_bytes() | response.body 是 ReadableStream，for await 消费 | 【可直接类比】LLM SSE 消费的落点 |

## 18.17 类型系统

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 类型兼容 | nominal（名字必须匹配） | 渐进（运行时无类型） | structural（形状匹配即可） | 【部分类比】TS 不看类名看结构，"鸭子类型的静态版" |
| 泛型运行时 | 擦除但保留类信息（raw type 可反射） | 无泛型（注解） | 全擦除，运行时零泛型痕迹 | 【不应类比】见 Top 8 第 6 条 |
| 判别联合 | 无（sealed + 模式匹配近似） | Union / Literal（mypy） | `\|` union + 字面量类型 + 收窄 | 【可直接类比】sealed interface + switch 模式匹配最接近 |
| 运行时查询 | instanceof / 反射 | type() / isinstance | typeof / instanceof（仅限 class，interface 不行） | 【部分类比】TS interface 在运行时不存在，instanceof 查不到 |

## 18.18 运行时

| 行 | Java | Python | Node.js/TS | 类比 |
|---|---|---|---|---|
| 引擎 | JVM（字节码 + JIT） | CPython（解释执行，PyPy 另说） | V8（JIT，即时编译热点） | 【可直接类比】V8 ≈ JVM 的角色：真正执行代码的 VM |
| I/O 底座 | NIO / netty（框架层） | selector / asyncio 封装 | libuv 内建（事件循环+线程池做阻塞 I/O） | 【部分类比】libuv 是运行时一部分，无法绕开 |
| 启动形态 | jar 交给 java | 脚本交给 python | js 交给 node（.ts 需转译或类型剥离） | 【可直接类比】 |

## 18.19 最容易做错误类比的 Top 8

1. **EventEmitter ≠ MQ**：没有异步投递、持久化、重试、跨进程——emit 只是同步函数调用。
2. **Promise ≠ 可取消的 Future**：Promise 自身不可取消，取消要靠 AbortSignal 全链路约定。
3. **npm install ≠ mvn install**：npm install 是"解析+下载+落盘进本项目"；mvn install 是"把构件发布到 ~/.m2 供别人引用"——方向完全相反，这是 Java 转 Node 最著名的误区。
4. **node_modules ≠ 单一 classpath**：依赖按目录树嵌套解析，同一包多版本可共存；classpath 里同名类只有一个胜出。
5. **单线程 ≠ GIL**：GIL 是"有真线程但锁住"；Node 是"根本没有并行执行 JS 的线程"，同步代码天然免竞态。
6. **TS 泛型 ≠ Java 泛型**：Java 擦除后仍保留类信息可反射；TS 类型整层消失，运行时连接口都查不到，且匹配规则是 structural。
7. **module ≠ classpath 唯一性**：import 按 node_modules 逐级向上解析，无全局唯一命名空间，包名不保证"同一个东西"。
8. **package.json scripts ≠ Maven phase 生命周期**：scripts 是无序命令别名，没有 validate→compile→test 的隐式链条，串联靠 `&&`。

## 本章只记住这 5 件事

1. 直接类比的可以放心用：Promise↔CompletableFuture、fs/promises↔Files、spawn↔ProcessBuilder、fetch↔HttpClient、zod↔pydantic。
2. 部分类比的重点在差异那一句话：流（异步事件驱动+内建背压）、模块（一文件一模块+双系统）、依赖（semver 范围+lock 才是真相）。
3. 不应类比的集中在四件事上：EventEmitter、Promise 取消、模块唯一性、TS 类型运行时——这四个坑踩一遍就记住了。
4. npm install 与 mvn install 是同名异义，方向相反，逢人便值得提醒。
5. 单线程事件循环的正确锚点是 asyncio 而不是 Java 线程模型；差异是 Node 的循环内建于运行时、不可绕开。

## 源码识别

- 看到 `new Promise(...)` → CompletableFuture 的手工展开形态，找 resolve/reject 的触发点
- 看到 `AbortController` → 本项目的取消通道，顺着 signal 找它能中断的所有 await
- 看到 `on("data")` → 异步事件驱动的流消费，对应 Python 侧"读 file-like"的形态
- 看到 `JSON.parse` 后紧跟 zod `.parse()` → 边界处的运行时校验，TS 类型不管这里
- 看到 `import x from "@scope/pkg"` → scoped 包，可能是 monorepo 内部包也可能是 npm 组织包
- 看到 `child.kill()` → 发 SIGTERM（不是 SIGKILL），对应 Popen.terminate()
- 看到 `typeof x === "string"` → 运行时类型检查，TS 类型帮不上时的手写判别
- 看到 `Promise.all(map(...))` → gather/allOf 的并发扇出形态

## Java/Python 工程师常见误区

- 错误认知：Node 单线程像 GIL 一样"线程存在但被锁" → 实际：JS 只在一个线程上执行，并行要 worker_threads 或子进程。
- 错误认知：import 的包名全局唯一，同名的就是同一个包 → 实际：按 node_modules 目录树解析，同名可指向不同副本。
- 错误认知：package.json scripts 有 Maven 式生命周期 → 实际：纯命令别名，顺序自己拼 `&&`。
- 错误认知：TS interface 可以 instanceof → 实际：类型全擦除，运行时只有 class 才能 instanceof。
- 错误认知：npm install 把包发布到本地仓库 → 实际：安装到当前项目；发布到本地仓库的动作在 npm 里不存在对应命令。

## 是否值得深入

- 各主题"部分类比"行的差异点：当前阶段：建议掌握——这就是读 Node 源码时唯一的新知识负担。
- Top 8 清单：当前阶段：建议掌握——每个都对应一类真实 bug。
- 各主题 API 细节（如 libuv 线程池大小、V8 JIT 策略、semver 完整规范）：当前阶段：不需要深入——用到再查，与源码阅读无直接关系。
