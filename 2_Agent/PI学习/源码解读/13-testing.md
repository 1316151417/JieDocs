# 第 13 章 测试体系

> 本章回答：一个强依赖外部模型 API 的项目如何做到 CI 无 key、无网络、确定性；faux provider 如何以"脚本化响应队列"模拟任意模型行为；harness 如何驱动完整 agent 循环；77 个 issue 回归测试如何组织。
>
> 主要文件：根 `test.sh`、`packages/ai/src/providers/faux.ts`、`packages/coding-agent/test/suite/harness.ts`、`test/suite/README.md`。

## 13.1 总体形态

| 包 | 框架 | 备注 |
|---|---|---|
| ai / agent / chord / client / coding-agent / durable / protocol / server / telemetry / sqlite-node | vitest 4 | `vitest --run` |
| **tui** | **node:test** | 零依赖直接执行 TS（全仓 erasable 语法约束的根源） |
| evals | vitest + vitest-evals | 需要 `PI_PROVIDER/PI_MODEL` |

根 `package.json`：`test = test:scripts + 各 workspace 逐个 test`。**正确入口永远是从仓库根跑 `./test.sh`**，而不是直接 `npm test`——原因是 e2e 门控（下文）。

`vitest.base.ts` 把所有 workspace 包名 alias 到各自 **src 源码**（`@earendil-works/pi-agent-core` → `packages/agent/src/index.ts`），monorepo 内测试无需先 build。

coding-agent 的 vitest 配置还设了 `PI_OFFLINE=1`——测试**默认离线**，需要网络的测试用 `allowNetwork()` 显式开启。

## 13.2 test.sh：环境隔离的教科书

直接跑 vitest 有个坑：AGENTS.md 警告 "Never run the full vitest suite directly: it includes e2e tests that activate when endpoint/auth env vars are present"——你 shell 里的 `ANTHROPIC_API_KEY` 会激活真实付费的 e2e。`test.sh` 的解法是一次性解决环境问题的组合拳：

1. **临时根**：`mktemp` 建隔离 HOME/TMPDIR/cache，加 `.pi-test-owned` 标记；cleanup 只删"路径匹配 + 非软链 + 带标记"的目录（防误删）；
2. **空环境**：`env -i` 从零开始，只透传白名单变量——PATH/PWD/临时目录/`LANG=C TZ=UTC`；
3. **git 隔离**：`GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_ASKPASS=$(type -P false)`——杜绝 git 交互和读用户配置；
4. **npm 隔离**：userconfig/globalconfig/cache 全指向临时文件；
5. **效果**：因为 `env -i` 清空了一切 API key，**所有依赖 key 的 e2e 自动 skip**；`PI_NO_LOCAL_LLM=1` 再跳过本地 LLM 依赖的测试。

脚本自己打印的总结："Running tests without API keys in isolated home"。

e2e 的门控实现本身很轻：`test/utilities.ts` 里 `API_KEY = process.env.ANTHROPIC_OAUTH_TOKEN || process.env.ANTHROPIC_API_KEY`，测试块用 `describe.skipIf(!API_KEY)`——有 key 时才会真实调 `streamSimple`。

## 13.3 faux provider：脚本化的模型

`packages/ai/src/providers/faux.ts` + `registerFauxProvider()`（`compat.ts`）。它是一个**注册进 model registry 的真 provider**，因此调用链路与真实厂商完全一致（registry → auth → adapter 分派 → 事件流），只是不发网络。四个机制：

**响应队列**。`setResponses([...])` 预置脚本；每次 `stream()` 消费队首一条；**队列耗尽返回 `stopReason:"error"` "No more faux responses queued"**——逼测试显式声明模型的每一步行为，少声明一条立刻暴露。每条可以是静态 AssistantMessage，也可以是 `(context, options, state, model) => AssistantMessage` 工厂（可依据请求上下文动态构造）。辅助构造器：`fauxText / fauxThinking / fauxToolCall(name, args) / fauxAssistantMessage(...)`。

**流式同构**。`streamWithDeltas()` 把完整消息按 tokenSize（3-5 字符）切块，按真实 provider 的**同构顺序**推事件：start → 各块 start/delta/end → done/error，全程携带共享 partial。`tokensPerSecond` 可模拟限速；`signal.aborted` 在任意 chunk 边界产出 `stopReason:"aborted"`。

**usage 仿真**。`estimateTokens = ceil(len/4)`；按 sessionId 维护 promptCache，用最长公共前缀把 prompt 拆成 cacheRead/cacheWrite——压缩/上下文窗口类测试无需真实 token 计数就有逼真的 usage。

**deferred 支持**。`stopReason:"deferred"` + 可配 `pendingFetches`/`pollAfterMs` 模拟长任务轮询。

一个 faux 驱动"读文件并总结"的测试大致长这样：

```ts
faux.setResponses([
  fauxAssistantMessage([fauxToolCall("read", { path: "README.md" })], { stopReason: "toolUse" }),
  fauxAssistantMessage([fauxText("这个项目是…")], { stopReason: "stop" }),
]);
await session.prompt("读取 README.md 并总结");
// 断言：真实 read 工具被执行了（faux 只出意图，执行是真的）
//       events 里出现两次 message_end(assistant)、一次 tool_execution_end
```

## 13.4 harness：驱动完整循环

两代 harness 并存，新人只用新版：

**旧版** `test/test-harness.ts`：自写 `createFauxStreamFn` 直接注入 `new Agent({streamFn})`，绕过 registry。`test/suite/README.md` 明确：除非缺少能力，不再扩展此路径。

**新版** `test/suite/harness.ts`：走**生产代码路径**——`registerFauxProvider()` 注册进 registry，Agent 用真实 `streamFn: streamSimple` + 真实 convertToLlm，扩展钩子（onPayload/onResponse/transformContext）经 `extensionRunnerRef` 全部接通。组装时全部服务用内存实现（`SessionManager.inMemory()` 等）。返回的 harness 暴露 `faux`、`events`、`eventsOfType(type)`、`getUserTexts/getAssistantTexts`。

由于 faux 是被 registry 正常路由的 provider，一条 `session.prompt("hi")` 驱动的是与生产完全相同的链路：faux 响应 → 真实工具执行 → follow-up 响应 → 落盘（内存）→ 事件广播。**测试与生产之间唯一的差别就是 provider 的实现**。

## 13.5 suite 的组织

`test/suite/` 两层：

- **顶层 characterization 测试**（约 10 个）：锁定核心行为——prompt 基本循环、单工具 turn、一轮多工具（含并发慢/快工具的事件顺序）、排队、压缩（含 model overrides）、重试事件、runtime 生命周期、bash 持久化、工具结果图片；
- **`regressions/` 77 个文件**，**按 GitHub issue 号命名**（`3317-network-connection-lost-retry.test.ts`、`8328-zero-usage-auto-compaction.test.ts`、`8537-custom-message-tool-result-ordering.test.ts`…），覆盖流解析、网络重试、压缩、扩展、事件排序、分支树等真实 bug 场景。规约（AGENTS.md + suite README）：修 issue 必须加带 issue 号注释的回归测试；只能用 harness + faux，禁止真实 API/key/网络/付费 token，必须 CI-safe 确定性。

老 `test/` 目录（200+ 文件）另覆盖 CLI 参数、配置迁移、主题、组件、选择器、导出、SDK、模型解析、RPC 等，多为单元/集成性质。

## 13.6 可测试性的架构回声

回头看，测试体系如此干净不是靠测试技巧，而是前几章的架构决定的：

| 架构决定 | 测试收益 |
|---|---|
| 组合根全量注入（第 4 章） | harness 一行换掉全部存储为内存实现 |
| streamFn 抽象 + provider 注册制（第 6、8 章） | faux 以 provider 身份进入，链路零改动 |
| 事件驱动 + 错误是数据（第 6 章） | 断言对象是确定性的 event 序列，不是时序敏感的副作用 |
| 渲染与执行分离（第 7 章）、Terminal 接口（第 12 章） | UI 可用 VirtualTerminal 断言 |
| usage 归一化（第 8 章） | faux 仿真的 cacheRead/cacheWrite 可直接喂压缩逻辑 |

如果你的 agent 项目测试难写，问题几乎总在左边那一列。

## 13.7 动手建议

1. 跑一次 `./test.sh`，观察它打印的隔离说明；
2. 读 `test/suite/agent-session-prompt.test.ts`（最短的 characterization），注意它如何用 `fauxToolCall` 让真实工具执行起来；
3. 挑一个 regression（比如 `8537-custom-message-tool-result-ordering.test.ts`），先读 issue 场景再读测试——这是理解"事件顺序不变量"最快的路径；
4. 试着用 harness 写一个自己的测试：让 faux 连续调用两次 read，断言两次 toolResult 的顺序。

## 13.8 本章问题

1. "队列耗尽即报错"让测试很严格。对比"默认返回空响应"的设计，各会漏掉/暴露什么类别的 bug？
2. faux 仿真 usage（cache 前缀拆分）为什么对压缩测试是必要的？如果 usage 恒 0，哪类测试写不出来？
3. 你的 agent 项目里，哪个架构决定阻碍了"无 key 跑全量测试"？参照 13.6 表格给出重构方向。

下一章（最后一章）：chord/durable/protocol 这些实验包在往哪走，以及整个仓库能带走的设计清单。
