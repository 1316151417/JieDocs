# 第 14 章 进阶方向与架构启示

> 本章回答两件事：一是 `chord / durable / protocol / client / server` 这些实验包在往哪走（当前 `PI_EXPERIMENTAL=1` 才启用，主线学习可跳过，但方向值得知道）；二是从整个仓库带走什么——如果你要写或重构自己的 agent 项目，这份清单是本教程的收束。
>
> 进阶材料：`packages/agent/docs/harness.md`（durable 规范）、`packages/chord/README.md`、`packages/durable/docs/pico-v5.md`、`coding-agent/src/experimental/services/README.md`。

## 14.1 为什么有"下一代线"

当前主线（coding-agent + agent + ai）把全部东西放在**一个进程**里：TUI、循环、工具执行、扩展。这在单机单会话下是最简正确的架构。但有几个压力点：

- 扩展与主进程同生共死，一个崩溃全崩；
- TUI 必须和 agent 在同一进程（无法做 WebUI/远程）；
- 会话的"持久"只到消息级，运行中的任务（工具执行到一半、流式输出到一半）没有事务性恢复。

下一代线就是对这些压力的回答，分三块：组合运行时（chord）、进程拆分（protocol/client/server）、持久执行（durable）。

## 14.2 chord：应用组合运行时

`packages/chord`，standalone（不依赖任何 pi 包），定位原文："Standalone application-composition runtime for services, replicated state, RPC, and plugins"。核心抽象：

- **Plugins**：声明提供/要求哪些服务的 setup 单元；host 校验依赖图、按序激活、逆序销毁；
- **Facets**：插件的"可分离部分"，同一插件的不同部分可以 bundle 到不同进程（backend / TUI / browser）；
- **Services**：类型化 token 标识的服务，可 process-local 也可远程暴露；provider 掉线/替换时 consumer 仍持稳定 facade；
- **Replicated state**：生产者 mutate 一个 state 代理后 `publish(context)`，消费者收到完整不可变值；断连时副本标记 unready 直到重新 hydration；
- **传输无关的 wire grammar**：chord 定义服务编解码，framing/路由（WebSocket、Unix socket…）留给应用；
- **delta 子系统**：对 plain JSON 记录做 track/apply，字符串赋值保留 append 语义与滚动窗口。

一句话：chord 把"多进程共享一组服务与状态"变成声明式配置。当前主线的 settings/telemetry/context 传递里已经有它的身影（agent 包依赖 chord 的 Context），.experimental 架构则全面用它。

## 14.3 protocol / client / server：进程拆分三件套

- **protocol**：运行时中立的路由信封 + CBOR 编码 + 4 字节长度前缀分帧。路由目标 `{serverId}` 或 `{serverId, sessionId, attachmentId}`——复合路由防跨服务器/跨会话误路由；支持请求取消、订阅更新、out-of-band attachment。载荷对协议不透明（strict-JSON），chord 语义在服务适配层校验；
- **client**：传输中立客户端（`ByteTransportFactory` 抽象任何有序字节流）；显式 `reconnect()`、**从不自动重连**；
- **server**：跑 durable Session 与 AgentHarness 接口的实验性本地服务器；一个 Session 可挂多个 presentation attachment（多个界面看同一会话）；服务器只验路由不解码业务。

在 coding-agent 里由 `src/experimental/server.ts` / `client-tui.ts` 组装：`PI_EXPERIMENTAL=1` 时 `pi client` 经 Unix socket 连接服务器，**跨进程驱动完整 agent**（AgentController 服务发 prompt/abort，Transcript 以复制状态同步到客户端）。`mini-test.sh` 跑的新 mini TUI 就是这条线的产物。

## 14.4 durable 与 AgentHarness：持久执行

两处相关代码：`packages/agent/src/harness/`（AgentHarness/AgentLane 接口 + Entry 树会话 + JSONL/SQLite 持久化 + 内置工具工厂 + compaction，规范在 `docs/harness.md`）和 `packages/durable`（Pico 运行时，规范 `docs/pico-v5.md`）。

核心规则一句话（Pico5 规范）："A Session atomically commits immutable entries, full task records, and Chord-tracked documents. **Only committed state is observable.**" 关键概念：

- **Entry 的双面**：模型面（发给 LLM 的消息）与应用面（data payload）分离；`head` 选择活动上下文起点；`edits`（omit/replace）可覆盖早期 entry 对模型上下文的贡献——比当前主线的 compaction 更细粒度的上下文控制；
- **Task**：挂在 conversation 上的持久状态机——工具执行到一半进程崩溃，重启后任务记录在案，可恢复；
- **Document**：chord delta op 表示的可变 JSON 状态；
- **usage ledger**：独立记账的 token 台账。

对照第 9 章可以看清演进：主线 JSONL 已经是"append-only + entry 树"，durable 把它推到"事务提交 + 任务级恢复 + 文档级状态"。当你的 agent 开始跑小时级任务时，这些概念会从 nice-to-have 变成必需。

## 14.5 telemetry：契约式观测

`packages/telemetry` 是 vendor-neutral 契约（span/attribute/event/status + 显式 context 传递，无全局 current-span、无 exporter），默认 NOOP。agent 包定义的 schema 覆盖 `pi.ai.request`（含 TTFT、chunk 数、分项 usage/cost）与 `pi.harness.run`。应用自行适配 OTel/Sentry。另外注意与 coding-agent 的"install telemetry"（匿名使用统计，`PI_TELEMETRY`/settings 开关）是两回事，别混淆。

## 14.6 带走什么：十条可迁移的设计

整个教程收束成一份清单。按"对你的 agent 项目影响最大"排序：

1. **transcript 即真相**。把系统提示词、工具集、模型选择都做成消息流的一部分，变更=追加（diff 补丁）。resume/分支/压缩/回放全部共享一套重放逻辑。这是 pi 最有复利的一个决定。
2. **错误是数据**。模型层错误编码进事件流（stopReason），工具层错误转 isError 结果，循环层兜底合成闭合事件序列。上层因此能实现重试、UI 永不卡在"半条消息"。
3. **事件顺序的固定纪律**：扩展改写 → UI 渲染 → 持久化。任何"多订阅者 + 可改写"的系统都需要明确这个顺序。
4. **工具的 content/details 分离**（给模型的与给界面的），加上"每次截断附带行动指令"。
5. **双队列输入模型**（steering/followUp）+ 队列模式的可配置。交互手感的核心，成本极低。
6. **按 API 家族做适配器 + compat 标志收纳方言**；品牌类型守住归一化边界。第三家厂商接入时你会感谢这个结构。
7. **凭证所有权模型**：存储凭证独占 provider、唯一写路径、双检锁刷新、无静默回退。
8. **会话 = append-only 树形 JSONL**：分叉 O(1)、崩溃恢复靠宽松加载器、人类可读。在单会话访问模式下比数据库便宜且更好。
9. **组合根 + 全量注入 + 内存实现**：可测试性是架构属性，不是测试技巧（第 13 章表格）。
10. **业务下沉 SDK、界面只是渲染器**：interactive/print/json/rpc 四模式共享同一会话层。当你想加 WebUI 时，这条决定省掉一次重写。

## 14.7 继续深入的路线图

- **想改 pi 本身**：读 `CONTRIBUTING.md`（贡献门禁与质量标准）→ 挑 `good first issue` → 按第 13 章写回归测试；
- **想深读 agent 内核**：`packages/agent/docs/harness.md`（durable 规范，比主线更严格的循环语义）；
- **想追新架构**：`coding-agent/src/experimental/services/README.md`（chord 服务化的 agent）+ `packages/durable/docs/pico-v5*.md`；
- **想看同类对照**：拿本教程第 6 章的事件序列和终止条件，去读 Claude Code / Codex CLI 的公开行为描述，找差异并问为什么——这是把"读过"变成"读懂"的最快方法。

## 14.8 终章问题

1. chord 的 replicated state 与"每个客户端自己 fetch 最新状态"的差异是什么？哪种更适合 Transcript 这种只增数据？
2. durable 的 Entry "模型面/应用面分离"解决了主线 JSONL 的什么痛点？（提示：toolResult 的 details 字段进不进模型上下文，主线是怎么处理的？）
3. 回到你自己的项目：14.6 清单里哪两条你目前没有？补上它们的改造顺序应该是什么？（依赖关系提示：1 依赖消息模型；3 依赖事件系统；9 依赖 1-8 的接口化程度）

——教程完。回到 [目录](README.md)。
