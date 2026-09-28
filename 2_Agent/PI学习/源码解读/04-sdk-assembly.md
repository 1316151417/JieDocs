# 第 4 章 SDK 与会话组装

> 本章回答：`createAgentSession()` 这个组合根到底装配了哪些服务；`AgentSessionServices` / `AgentSession` / `AgentSessionRuntime` 三个名字相近的东西为什么要拆成三层；配置文件如何分层生效。这是理解"pi 为什么可以整体换会话"的关键一章。

## 4.1 组合根：createAgentSession()

文件：`coding-agent/src/core/sdk.ts`，函数 `createAgentSession()`（约 L173 起）。它是全库最重要的组装点，官方 SDK 文档（`docs/sdk.md`）和全部 11 个示例（`examples/sdk/`）都从它进入。按代码顺序的装配步骤：

| 步 | 做什么 | 细节 |
|---|---|---|
| 1 | 解析路径 | `cwd`（默认 process.cwd()）、`agentDir`（默认 `~/.pi/agent`） |
| 2 | `ModelRuntime.create()` | 模型目录 + provider 注册 + 鉴权运行时 |
| 3 | `SettingsManager.create()` | 全局 + 项目两层 settings |
| 4 | `SessionManager.create()` | 会话树持久化（有 `inMemory()` 变体） |
| 5 | `DefaultResourceLoader` + `reload()` | 发现/加载扩展、skills、模板、主题、AGENTS.md、SYSTEM.md |
| 6 | 恢复既有会话 | `buildSessionContext()` 取回消息、模型、thinking 档位 |
| 7 | 模型决策 | 显式参数 > 会话恢复（校验鉴权，失败给 fallback 提示）> `findInitialModel()` 兜底链 |
| 8 | thinking 档位决策 | 会话恢复 > 每模型覆盖 > 全局默认 medium，再钳制到模型能力 |
| 9 | 初始工具集 | 默认 `["read","bash","edit","write"]`，settings `defaultTools`、`--tools`/`--exclude-tools` 修饰 |
| 10 | 构造底层 `Agent` | 见下文，注入四个扩展挂钩 |
| 11 | 会话记录初始化 | 新会话写 `model_change` + `thinking_level_change` entry，保证 resume 可还原 |
| 12 | `new AgentSession({...})` | 返回 `{ session, extensionsResult, modelFallbackMessage }` |

**每个服务都可注入**（options 里都有对应参数），且每个服务都有内存实现。这不是巧合，而是第 13 章测试体系的根基：整个应用可以零文件系统、零网络地跑起来。

## 4.2 第 10 步细看：Agent 是怎么被"接线"的

底层 `Agent`（来自 `@earendil-works/pi-agent-core`）本身是个通用执行内核，coding-agent 通过四个注入点把应用能力接进去：

```ts
new Agent({
  initialState: { model, thinkingLevel, tools, messages },
  streamFn,                    // 包装 modelRuntime.streamSimple：
                               //   注入 provider 重试、HTTP 空闲超时、
                               //   transformHeaders（合并扩展 before_provider_headers 钩子）
  onPayload / onResponse,      // 接扩展 before_provider_request / after_provider_response
  transformContext,            // 接扩展 context 钩子（每次请求前可改写上下文）
  convertToLlm,                // 消息转换，附带 blockImages 设置的动态过滤
  beforeToolCall / afterToolCall, // 接扩展 tool_call / tool_result 事件（第 7、11 章）
})
```

其中有一个值得单独讲的技巧——**可变引用盒**。扩展系统的 `ExtensionRunner` 要等 `AgentSession` 构造时才创建，但 Agent 先建、需要引用它。解法（`sdk.ts` 约 L304）：

```ts
const extensionRunnerRef: { current?: ExtensionRunner } = {};
// Agent 的各个闭包捕获 ref，运行时才读 ref.current
// ExtensionRunner 创建后填充 ref.current 即完成接线
```

这解决了"构造顺序循环依赖"，还附带一个好处：`/reload` 换了 Runner 后，Agent 闭包下次读 `ref.current` 自动用新的，无需重建 Agent。

## 4.3 三层结构：Services / AgentSession / Runtime

这是本章的核心。三个类名都含 "Session"，初学极易混淆。职责划分：

```
AgentSessionServices        "服务束"——cwd 绑定的基础设施
  { cwd, agentDir, modelRuntime, settingsManager, resourceLoader, diagnostics }
        │ createAgentSessionFromServices()
        ▼
AgentSession                "会话"——有状态的行为主体
  持有：底层 Agent、ExtensionRunner、工具注册表、
       steering/followUp 镜像队列、压缩/重试控制器
  提供：prompt()/steer()/followUp()/abort()/setModel()/compact()/navigateTree()…
        │ 宿主持有
        ▼
AgentSessionRuntime         "运行时容器"——可整体替换的宿主
  持有：当前 session + services + 重建工厂 createRuntime
  提供：switchSession()/newSession()/fork()/importFromJsonl()/dispose()
```

### 为什么要拆？

**原因一：会话切换是"换整机"，不是"换零件"。**
`/resume` 到另一个目录的会话时，settings、资源、扩展全是 cwd 绑定的——不可能只换 SessionManager。所以 runtime 的所有替换操作走同一个模式：

```
emitBefore*(可被扩展 cancel)
  → teardownCurrent():
       session.abort()           // 让被中断回合的工具结果先落盘
       emit session_shutdown
       beforeSessionInvalidate() // 宿主 UI 同步拆掉扩展组件
       session.dispose()         // 旧扩展 ctx 标记 stale，防悬挂引用
  → createRuntime()              // 用保存的工厂闭包按新 cwd 重建整束
  → apply() + finishSessionReplacement()
  → 宿主经 setRebindSession 回调重新绑定、重渲染
```

`teardownCurrent` 的顺序也是刻意的：先 abort 让在途回合完整落盘，再广播关闭，最后 dispose。`dispose()` 会对扩展 ctx 做 `invalidate`——此后扩展若还持有旧 `pi` 对象调用，会收到明确的错误提示（错误消息本身就是文档）。

**原因二：可测试性。**
`createAgentSessionFromServices()` 允许测试先手工构造 services（全内存），再建会话。`services.diagnostics` 的设计同理：启动期的非致命问题（扩展冲突、配置错误）不打印不退出，作为数据返回，**展示策略交给 app 层**——core 保持 headless 可用。

**原因三：三种模式共享。**
上一章的三种模式拿到的都是 `AgentSessionRuntime`，谁也不直接 new AgentSession。

### Runtime 替换的四个入口

| 方法 | 场景 | 要点 |
|---|---|---|
| `switchSession(path)` | `/resume` | 新 SessionManager + 新 AgentSession |
| `newSession()` | `/new` | 持久化则新建文件，否则复用 inMemory |
| `fork(position)` | `/fork`、树视图双击 | `"at"`：在选中 entry 处分叉出新会话文件；`"before"`：在选中 user 消息**之前**分叉，并把原文回填编辑器供修改重发 |
| `importFromJsonl(path)` | `/import` | 复制外部 JSONL 进 sessionDir（重名去重）后打开 |

## 4.4 配置体系：两个维度 four 层

pi 的配置从两个维度叠加：**文件位置**（全局/项目）×**配置类型**（settings / 模型 / 凭据 / 键位）。

### settings.json（`core/settings-manager.ts`）

- 全局：`~/.pi/agent/settings.json`；项目：`<cwd>/.pi/settings.json`；
- 深合并，**项目覆盖全局**；`proper-lockfile` 同步锁保证并发写安全；
- 项目 settings 需要项目信任（见下）；
- 关键配置项速览：

| 类别 | 配置 |
|---|---|
| 模型 | `defaultProvider/defaultModel/defaultThinkingLevel/modelThinkingLevels/enabledModels` |
| 压缩 | `compaction.{enabled,reserveTokens=16384,keepRecentTokens=20000,modelOverrides}` |
| 行为 | `steeringMode/followUpMode`（all \| one-at-a-time）、`retry.{enabled,maxRetries=3,baseDelayMs}`、`transport` |
| 工具 | `defaultTools` |
| 资源 | `packages`、`extensions/skills/prompts/themes` 路径 |
| 界面 | `theme/tuiMode/autocompleteMaxVisible/hideThinkingBlock/markdown.mermaid` |
| 环境 | `defaultProjectTrust`、`shellCommandPrefix`、`httpProxy`、`images.blockImages` |

### 其他配置文件

| 文件 | 位置 | 内容 |
|---|---|---|
| `auth.json` | `~/.pi/auth.json` | 各 provider 凭据（第 8 章） |
| `models.json` | `~/.pi/agent/models.json` | 自定义模型/provider 覆盖（baseUrl、key、headers） |
| `keybindings.json` | `~/.pi/agent/keybindings.json` | 键位覆盖（tui + app 动作） |
| `SYSTEM.md` / `APPEND_SYSTEM.md` | 项目 `.pi/` 或全局 | 替换 / 追加系统提示词（第 10 章） |
| `trust.json` | `~/.pi/agent/trust.json` | 项目信任决策 |

### 项目信任（Project Trust）

唯一内置的"启动时审批"。要保护的资源：项目 `.pi/settings.json`、`.pi/{extensions,skills,prompts,themes}`、`.pi/SYSTEM.md`、项目 `.agents/skills`——**防止 clone 一个仓库就被它注入的配置/扩展静默执行**。决策链：已存决策（本目录或最近父目录）→ CLI `--approve/--no-approve` → settings `defaultProjectTrust`（ask/always/never，默认 ask）。ask 时交互模式弹选择框；**非交互模式一律按不信任处理**（不弹框）。未信任的项目资源直接不加载；AGENTS.md 不受此门控（它只是提示词内容，不是可执行代码）。

信任解析本身还有个"两遍加载"细节：先以不信任状态加载一遍（只有用户级+CLI 扩展），把发现的项目扩展给用户看，确认后再正式加载——用户看到的是"即将执行什么"，而不是盲签。

## 4.5 资源加载：ResourceLoader 的发现顺序

`core/resource-loader.ts` 的 `reload()` 负责发现一切可加载资源。同名冲突时**先到者赢**，顺序是：

```
CLI 临时指定（--extension/--skill/...）
  > 项目 packages（settings.packages 的 project scope）
  > 全局 packages
  > settings 显式路径（项目条目先于全局条目）
  > 自动发现：
      项目 .pi/{extensions,skills,prompts,themes}（需信任）
      项目祖先目录的 .agents/skills
      用户 ~/.pi/agent/{...}
      用户 ~/.agents/skills
```

AGENTS.md 类上下文文件的发现不同（第 10 章）：候选名按 `AGENTS.override.md > AGENTS.md > AGENTS.MD > CLAUDE.md > CLAUDE.MD`，从全局取一份 + 从 cwd 逐级向上收集，按"根→叶"排序合并。

## 4.6 模型运行时：ModelRuntime 与四层 provider 叠加

`core/model-runtime.ts` 的 `ModelRuntime` 实现了 pi-ai 的 `Models` 接口，是编码助手专用的封装。它的 provider 目录来自四层叠加（`recomposeProvider()`）：

```
builtins（pi-ai 内置 40+ provider 目录）
  + nativeExtensionProviders（扩展注册的完整 Provider 对象）
  + config（models.json 的覆盖：baseUrl/apiKey/headers）
  + extensionProviders（扩展注册的 ProviderConfig 片段）
```

叠加失败会降级回 builtin 并记 `compositionErrors`（不崩）。可用性刷新有 seq 号机制防止过期响应覆盖新状态；凭据操作（login/logout）按 provider 排队串行化，避免交错。

`core/model-resolver.ts` 的 `findInitialModel()` 兜底链（第 3 章 main() 最终会走到这里）：

```
CLI --provider/--model
  > --models / enabledModels 的第一个
  > settings 保存的默认（需有鉴权）
  > defaultModelPerProvider 表（每个厂商的已知默认模型）
  > 第一个可用模型
  > 无 → 显示"无可用模型"指引
```

`resolveCliModel()` 里还有个实用细节：模型 id 找不到时 `buildFallbackModel()` 会**凭空构造**一个以该 provider 基础模型为模板的自定义条目——刚发布的新模型或私有部署还没进目录时也能直接用。

## 4.7 本章问题

1. `/resume` 一个位于其他项目的会话，为什么不能复用当前的 SettingsManager？这个约束决定了哪一层的设计？
2. `extensionRunnerRef` 引用盒解决的是构造顺序问题还是性能问题？如果不用它，替代方案是什么（提示：重建 Agent 有什么代价）？
3. settings 深合并里，如果全局设 `"defaultTools": ["read"]`、项目设 `"defaultTools": ["read","bash"]`，数组如何合并？去源码 `deepMergeSettings` 验证你的猜测。

下一章：进入 `AgentSession`，看 `prompt()` 管线的完整细节。
