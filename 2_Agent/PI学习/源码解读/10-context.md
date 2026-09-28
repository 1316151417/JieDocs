# 第 10 章 上下文工程

> 本章回答：发给模型的 system prompt 到底由什么组成、AGENTS.md 在哪个位置生效；运行中改工具/技能为什么不打断对话；compaction 的触发条件与算法；UI 右下角的上下文百分比是怎么算出来的。
>
> 主要文件：`coding-agent/src/core/system-prompt.ts`、`core/resource-loader.ts`（上下文文件发现）、`core/compaction/`。官方文档 `docs/compaction.md` 可对照。

## 10.1 system prompt 的分节结构

`buildSystemPromptSections()`（`system-prompt.ts` 约 L121 起）把提示词组织为**命名 section**，除 `preamble` 外每节包在 `<name>...</name>` 标签里：

| 节 | 内容 | 来源 |
|---|---|---|
| `preamble` | 身份声明（"You are an expert coding assistant operating inside pi…"） | 默认常量，或 SYSTEM.md 替换 |
| `tools` | 每工具一行 `- name: 一句话说明` | 工具注册时的 snippet |
| `rules` | 行为规则：按启用工具动态拼装（没开 grep 就指导用 bash 的 rg）、各工具 guidelines、固定规则（"Be concise"…），去重 | 代码 + 工具定义 |
| `docs` | pi 自身文档/示例的路径指引 | 固定 |
| `addendum` | 追加指令 | APPEND_SYSTEM.md 或 `--append-system-prompt` |
| `project_context` | **AGENTS.md 内容**，包 `<project_instructions path="...">` | resource-loader |
| `skills` | 技能文件格式化列表 | resource-loader |
| `cwd` | 当前工作目录 | 运行时 |

这个结构的用意不在"好看"，而在**可差分**（见 10.3）：节是 diff 的单位。

### AGENTS.md 的发现与合并

`resource-loader.ts` 的规则：

- 同目录候选名优先级：`AGENTS.override.md > AGENTS.md > AGENTS.MD > CLAUDE.md > CLAUDE.MD`（取第一个命中，**不叠加**）；
- 采集范围：全局 `~/.pi/agent/` 一份 + 从 cwd **逐级向上到根**各目录一份，去重、按"根→叶"排序（外层在前）；
- git linked worktree 有个特判（`findShadowedContextFile`）：嵌套 worktree 会同时命中主仓的同名文件造成双份，检测后跳过被遮蔽那份；
- AGENTS.md **不受项目信任门控**（它是提示词内容，不是可执行代码）；`.pi/SYSTEM.md`（整体替换提示词）则受门控。

## 10.2 为什么 system prompt 是消息，不是配置

第 1 章埋的主线在这里完全展开。system prompt（和工具声明）作为 **system 消息存进 transcript**：

- 首次请求：完整 sections + `toolsAdded` 的首条 system 消息；
- 之后任何变化（开关工具、加载技能、扩展改节）：`diffSystemPromptSections()` 生成**补丁型 system 消息**（sections 里只含变化的节，`null` 表示删除；工具差异走 `toolsAdded/toolsRemoved`）；
- 当前状态 = 按序**回放**全部 system 消息（`ai/src/utils/transcript.ts` 的 `getCurrentSystemMessage()`）。

三个直接收益：

1. **不打断对话**：换工具不发全量新提示词，只发一条小补丁消息——省钱、省 token、且历史上下文里的指代不失效；
2. **resume 天然正确**：重放消息即恢复当时的确切提示词与工具集；
3. **请求期投影**：不支持会话中 system 消息的 API（如某些厂商）在发送前折叠为头部一条（`collapseSystemMessages`）；扩展强制提示词（forceSystemPrompt）走 `transformContext` 投影，**不污染 transcript**——回放一致性与扩展自由两全。

每回合刷新（第 5 章的 `prepareNextTurnWithContext` 钩子）保证"模型看到的"与"`session.systemPrompt` getter 返回的"在每次请求前重新对齐。

## 10.3 compaction：什么时候压、怎么压

长对话终将超出上下文窗口。compaction 的目标是：**在保留任务关键信息的前提下，把旧历史折叠成一条摘要消息**。

### 触发：三个检查点 + 三种原因

设置：`compaction.{enabled=true, reserveTokens=16384, keepRecentTokens=20000, modelOverrides}`。阈值：`contextTokens > contextWindow - reserveTokens`。

三个检查点（第 5 章见过其中两个）：

1. 回合内：工具批之后、下一次模型请求之前（`prepareNextTurn` 钩子，用户无感）；
2. run 结束后（`_handlePostAgentRun`）；
3. 新 user prompt 提交前（兜住被中止响应的残留）。

三种原因（`_checkCompaction`）：

- **overflow + retry**：请求因上下文溢出报错（或可恢复的 length 截断）→ 删掉失败的 assistant 消息、压缩、重试一次（`_overflowRecoveryAttempted` 防死循环）；
- **overflow 不重试**：响应完成但已超窗 → 压缩、保留响应；
- **threshold**：常规阈值触发。此处有多重防误触：error/零 usage 消息回退估算、校验 usage 时间戳在最近压缩边界之后（防"压缩前的大 usage 假触发"）、换模型后旧溢出不触发。

### 算法：找切点，做摘要，存检查点

`core/compaction/compaction.ts` 的 `prepareCompaction()` + `compact()`：

```
1. 路径末尾已是 compaction？→ 跳过（"Already compacted"）
2. 定位上次压缩边界：重复压缩时，被摘要区间从上次保留边界开始
   （上次幸存的摘要会再次进入新摘要——信息不丢）
3. findCutPoint()：
   合法切点 = user/assistant/bashExecution/custom/branchSummary/compactionSummary
   ★ 绝不切在 toolResult——工具结果必须跟着它的 toolCall
   从最新往回累积 token 估算（chars/4 启发式，图片按 4800 字符），
   达到 keepRecentTokens 即停
   单个 turn 本身超预算 → "split turn"：turn 前缀单独成段
4. 摘要生成：
   已有旧摘要 → UPDATE_SUMMARIZATION_PROMPT（迭代式："保留旧信息+合并新进展"）
   首次       → SUMMARIZATION_PROMPT（结构化模板：Goal / Constraints /
                 Progress(Done/In Progress/Blocked) / Key Decisions /
                 Next Steps / Critical Context）
   对话先经 serializeConversation() 转成 [User]:/[Assistant]: 纯文本并包
   <conversation> 标签——防模型把待摘要内容当成对话继续；
   toolResult 截断到 2000 字符控制摘要请求体积
5. 文件追踪：从 assistant 的 toolCall（read/write/edit）+ 上次 details 累积
   read-files / modified-files 集合，附在摘要尾部 <read-files>/<modified-files>
6. 摘要请求本身：cacheRetention:"none" + 新路由 session id
   （一次性请求不污染 prompt cache），带重试包装
```

### 压缩后的上下文长什么样

`appendCompaction()` 同时把**当前完整 system 消息**（提示词 sections + 工具声明）快照进 `entry.systemMessage`。重建时（`buildContextEntries`）：

```
[system(systemMessage 快照), compactionSummary(以 user 消息形态), 保留的消息…]
```

即 compaction entry 是树上的普通子节点（不是终点，不产生新分支），并且自带完整检查点——**任意分支的压缩状态都可精确重放**。`compactionSummary` 进 LLM 请求时带固定前缀"The conversation history before this point was compacted into the following summary"。

扩展可经 `session_before_compact` 钩子取消或接管摘要（含自定义模型），`session_compact_failed` 通知失败。

## 10.4 token 统计：真实 usage 优先，诚实的"?"

两套统计，用途不同：

**累计统计**（`getSessionStats`）：遍历全部 entry（含被压缩掉的历史），按 `provider/responseModel` 分组汇总 token 与费用——反映整场会话真实计费。

**上下文占用**（`getContextUsage`，UI 右下角 `72.3%/200k (auto)`）：

```
取最后一条有效 assistant 的真实 usage 作为基数
  （排除 aborted/error/全零，且要求其时间戳不早于其后任何消息——
    防压缩摘要插入后失真）
其后的新消息按 chars/4 估算追加
percent = tokens / contextWindow
```

压缩后有个诚实细节：若最近压缩之后还没有新的 assistant 响应，真实上下文大小未知，返回 `null` → UI 显示 `?/200k` 而不是编造一个数。`(auto)` 后缀表示 autoCompact 开启；>70% 变黄、>90% 变红。

## 10.5 把三件事连起来看

本章 + 第 9 章的三件"上下文折叠"机制，本质上回答同一个问题的三种变体——"历史太长/太多/太乱怎么办"：

| 机制 | 折叠对象 | 折叠产物 | 触发者 |
|---|---|---|---|
| compaction | 当前分支的旧消息 | compaction entry（结构化摘要+检查点） | 自动（阈值/溢出）或 `/compact` |
| branch summary | 被离开的分支 | branch_summary entry | 用户切分支时（可选） |
| system diff | 提示词/工具变更 | 补丁 system 消息 | 任何配置变化 |

三者都遵守同一纪律：**折叠产物也是 transcript 里的 entry/消息，回放语义永远成立**。

## 10.6 本章问题

1. 切点为什么不能落在 toolResult 上？构造一个会出问题的上下文序列（提示：Anthropic 要求 tool_result 紧跟 tool_use）。
2. 重复压缩时"从上次保留边界开始摘要"而不是"从上次摘要点开始"，两种选择各丢/保什么信息？
3. UI 显示 `?/200k` 的那段时间里，`getContextUsage` 为什么不干脆用 chars/4 全文估算？（提示：估算误差在压缩边界附近最大，而此时做错决策的代价是什么——联系 autoCompact）

下一章：把系统撑起来的最后一根柱子——扩展生态。
