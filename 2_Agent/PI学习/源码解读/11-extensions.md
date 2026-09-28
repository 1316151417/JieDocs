# 第 11 章 扩展生态

> 本章回答：扩展是什么、从哪里来、能拦截什么；工具审批、skills、斜杠命令、`@` 补全、子代理分别如何用扩展实现。读完你应该能判断：给 pi 加一个新能力，该做成扩展还是改内核。
>
> 主要文件：`coding-agent/src/core/extensions/runner.ts`、`extensions/types.ts`、`core/resource-loader.ts`。官方文档 `docs/extensions.md` 是权威 API 参考，`examples/extensions/` 有大量可运行示例。

## 11.1 扩展是什么

一个扩展就是一个 JS/TS 模块，默认导出一个工厂函数：

```ts
export default function myExtension(pi) {
  // pi.on(...) 订阅事件
  // pi.registerTool(...) / registerCommand(...) / registerAutocompleteProviderFactory(...)
  // pi.ctx 访问会话上下文（settings、ui、cwd、sendMessage…）
}
```

加载来源与优先级（第 4 章 5 节）：CLI `--extension` > 项目 packages > 全局 packages > settings 路径 > 自动发现目录（项目 `.pi/extensions` 需项目信任）。同名工具/命令冲突时**都保留，按加载顺序决定优先级**，冲突记 diagnostic 提示。

`ExtensionRunner`（`core/extensions/runner.ts`）是事件分发中枢：AgentSession 把内核事件翻译成扩展事件并 emit，扩展 handler 的返回值有塑造能力（block / transform / replace）。第 4 章的 `extensionRunnerRef` 引用盒把它接到 Agent 的钩子上——**扩展与内核之间没有直接依赖，全部经 runner 中转**。

## 11.2 事件钩子全景

按生命周期阶段分组（返回值能力列在右侧）：

| 阶段 | 事件 | 能做什么 |
|---|---|---|
| 启动/重载 | `session_start` | 初始化；此时 UI 已可用（可弹 dialog） |
| 输入 | `input` | `{action:"transform"}` 改写文本/图片；`{action:"handled"}` 吞掉 |
| 提交前 | `before_agent_start` | 返回 `{message}` 注入消息、`{systemPrompt}` 本轮强制提示词、改 selectedTools |
| 模型请求 | `before_provider_request` / `after_provider_response` | 改 payload / 观察 raw 响应 |
| 上下文 | `context` 钩子（transformContext） | 每次请求前改写上下文 |
| 工具 | `tool_call` / `tool_result` | **block+reason 拦截**；改 input 参数；改写结果/注入图片 |
| 消息 | `message_end` | 返回替换消息（原地覆写，第 5 章） |
| 回合/运行 | `turn_start/end`、`agent_start/end` | 观察 |
| 会话生命周期 | `session_before_compact` / `session_compact_failed` / `session_before_tree` / `session_before_switch` / `session_before_fork` / `session_shutdown` | cancel 或接管（自定义摘要等） |
| 用户 bash | `user_bash` | 返回 `{operations}` 换执行层，或 `{result}` 全接管 |
| 资源 | `resources_discover` | 动态贡献 skills/prompts/themes 路径 |
| 界面 | `registerAutocompleteProviderFactory` / `registerEditorFactory` / widget 注册 | 补全源、整编辑器替换、界面组件 |

（`model_select`、`project_trust` 等更多事件见 `extensions/types.ts`。）

三个使用范例，分别对应三种塑造强度：

**例一：拦截（第 7 章的审批）**——事件返回值中断执行流：

```ts
pi.on("tool_call", async (event, ctx) => {
  if (event.toolName === "bash" && event.input.command?.includes("rm -rf")) {
    const ok = await ctx.ui.confirm("Dangerous!", "Allow rm -rf?");
    if (!ok) return { block: true, reason: "Blocked by user" };
  }
});
```

**例二：transform（输入改写）**——`input` 钩子链式替换，如把 `#123` 展开成 issue 正文、把大文件路径替换为内容。

**例三：注册（能力注入）**——`pi.registerTool()` 添加新工具（与内置工具同一接口、同一过滤管道），`pi.registerCommand()` 添加斜杠命令（自动进 `/` 补全菜单）。

## 11.3 skills：提示词层面的扩展

skill 是最小成本的扩展形态：一个含 frontmatter 的 markdown 目录（`SKILL.md` + 可选附属文件）：

```markdown
---
name: interactive-testing
description: 用 tmux 测试 pi 交互模式时的注意事项…
---
正文即指令内容…
```

生效路径：resource-loader 发现 → 用户输入 `/skill:interactive-testing 参数`（或模型看到 skills 列表后主动调用）→ `prompt()` 管线第 4 步把命令展开为：

```
<skill name="interactive-testing" location="/path/to">
正文（去 frontmatter）
</skill>
```

随 user 消息注入。与扩展的本质区别：**skill 是数据（进提示词），扩展是代码（进进程）**。skill 因此不需要项目信任以外的审查——它只能影响模型说什么，不能拦截工具。`settings.enableSkillCommands` 可关闭 `/skill:` 命令形式。

## 11.4 斜杠命令的三种来源

`/` 补全菜单（第 12 章的 autocomplete）合并四路命令源：

1. **内置命令**（`core/slash-commands.ts` 的 `BUILTIN_SLASH_COMMANDS`，约 20 个：`/model /thinking /settings /fork /tree /resume /compact /login /trust …`）——在 interactive-mode 的 submit 链硬编码分发（第 3 章）；
2. **prompt 模板**（`~/.pi/agent/prompts/*.md`，frontmatter 定义名与参数）——展开为提示词发送；
3. **扩展命令**（`registerCommand`）——`handler(args, ctx)` 自主行为，可通过 `pi.sendMessage()` 自行管理 LLM 交互；描述带来源标签 `[u]`/`[p]`（用户/项目）；
4. **`/skill:name`**（上节）。

扩展命令与内置重名时被跳过或改名（记 diagnostic）。命令在 agent 流式输出期间也**立即执行**（第 5 章管线第 1 步），但 steer/followUp 队列里不允许排命令。

## 11.5 界面级扩展点

- **补全源**：`registerAutocompleteProviderFactory` 包裹默认 provider，可声明 `triggerCharacters`（如 `#` 触发 issue 补全）；
- **编辑器替换**：`registerEditorFactory` 整体换编辑器（vim 模式扩展就这么做），新编辑器绑回默认 submit 链保持行为一致；
- **widget**：扩展组件挂到编辑器上/下方容器（第 3 章构造函数里的 `widgetContainerAbove/Below`）；
- **UI 对话框**：`ctx.ui.confirm/select/...`，rpc 模式下这些请求会被转发给宿主客户端渲染（`extension_ui_response`）——同一扩展在终端和嵌入式宿主里都能弹框。

## 11.6 子代理：扩展的进程级用法

pi 内核没有内置 subagent 工具，官方示例 `examples/extensions/subagent/` 展示了推荐做法：

- 每个子代理是一个 markdown 文件（frontmatter：name/description/model/tools），正文即 system prompt；
- 扩展 `registerTool("spawn_subagent")` → 实现里 **spawn 独立进程**：

```bash
pi --mode json -p --no-session \
   [--model …] [--thinking …] [--tools …] \
   --append-system-prompt <临时文件>  "任务文本"
```

- 主进程解析 JSON 流收集结果。

为什么用进程而不是进程内嵌套 agent：上下文窗口物理隔离、崩溃隔离、天然并行（示例上限 8 任务/4 并发）、零状态污染。代价是进程启动开销与结果只有文本摘要（无共享 transcript）。这是"简单、可组合"哲学的又一次体现——对比在进程内建 subagent 调度器的方案，pi 的选择明显偏向前者。

## 11.7 什么时候改内核，什么时候写扩展

判断准则（从源码结构反推）：

| 特征 | 走扩展 | 改内核/core |
|---|---|---|
| 需要拦截/观察现有流程 | ✅ 事件钩子覆盖几乎所有流程点 | 事件粒度不够时（如新的队列语义） |
| 新工具 | ✅ registerTool，与内置同权 | 需要特殊并发模式（如全局顺序锁）时考虑 |
| 新模型厂商 | provider 注册也走扩展（`pendingProviderRegistrations`，第 4 章） | 新 API 家族才需要改 ai 包 |
| 改变循环结构（终止条件、回合语义） | ❌ 钩子只有 shouldStopAfterTurn/prepareNextTurn 两个口子 | ✅ agent 包 |
| 改持久化格式 | ❌ | ✅ session-manager |

一句话：**扩展覆盖"编排"（什么时机做什么），内核保留"语义"（消息/循环/持久化的不变量）**。这个分界与第 5 章"管/不管"清单一致。

## 11.8 本章问题

1. 把第 7 章的 6 行审批扩展升级为"always allow"：你会把已批准规则存在哪？（提示：扩展模块的模块级状态 vs `custom` entry vs settings——各自的生命周期和作用域）
2. `input` 钩子和 `before_agent_start` 钩子都能注入内容，语义差别是什么？（回看第 5 章管线第 3 步与第 10 步）
3. 子代理示例用 `--no-session`：如果去掉这个参数，会发生什么资源层面的问题？（联系第 9 章"延迟建文件"——什么时候才真正产生垃圾文件？）

下一章：最后一块拼图——终端界面是如何渲染的。
