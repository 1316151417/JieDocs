# 第 9 章 会话持久化与分支

> 本章回答：会话文件的物理格式；"树形会话"如何用追加式日志表达；fork/tree 的实现；崩溃后如何恢复；resume 时上下文如何重建。读完你会理解 pi 最有辨识度的产品能力——**对话是一棵树，不是一条线**——在数据结构层面是如何成立的。
>
> 主要文件：`coding-agent/src/core/session-manager.ts`（1786 行）、`core/agent-session.ts` 的 navigateTree、`core/compaction/branch-summarization.ts`。官方文档 `docs/session-format.md` 是格式的权威说明。

## 9.1 物理格式：一个 JSONL 文件，一棵树

位置：`~/.pi/agent/sessions/--<cwd 编码>--/<时间戳>_<uuid7>.jsonl`（目录名把路径里的 `/ \ :` 都换成 `-` 并包 `--…--`，保证按项目归档）。

文件第一行是 header，其后每行一个 entry：

```jsonl
{"type":"session","version":3,"id":"01a0e874-…","timestamp":"…","cwd":"/Users/you/proj","parentSession":null}
{"type":"message","id":"a1b2c3d4","parentId":null,          "message":{…system…}}
{"type":"message","id":"e5f6a7b8","parentId":"a1b2c3d4",    "message":{…user…}}
{"type":"message","id":"c9d0e1f2","parentId":"e5f6a7b8",    "message":{…assistant…}}
{"type":"message","id":"3a4b5c6d","parentId":"c9d0e1f2",    "message":{…toolResult…}}
{"type":"model_change","id":"7e8f9a0b","parentId":"…",      "provider":"…","modelId":"…"}
```

要点：

- **`parentId` 链就是树**。写入顺序只是追加顺序；真正的树由 `byId` 索引 + parentId 链还原。当前分支 = 从 leaf 沿 parentId 走到根再反转（`buildSessionPath()`）；
- entry id 默认 8 位 hex（冲突重试 100 次后回退全 UUID）；
- `parentSession` 字段记录 fork/clone 的来源文件——fork 不是复制对话，是**开新文件 + 记录血统**。

### entry 类型全表

| type | 用途 |
|---|---|
| `message` | 六种消息（system/user/assistant/toolResult/bashExecution/custom） |
| `model_change` / `thinking_level_change` | 中途换模型/档位（resume 依据） |
| `compaction` | 压缩检查点（第 10 章）：summary + firstKeptEntryId + systemMessage 快照 |
| `branch_summary` | 分支切换摘要（见 9.4） |
| `custom` | 扩展私有状态（**不进上下文**） |
| `custom_message` | 扩展注入消息（进上下文） |
| `label` / `session_info` | 书签 / 会话命名 |

版本迁移内建：v1（线性）→ v2（id/parentId 树）→ v3（hookMessage 改名 custom），加载旧文件自动迁移并重写——旧会话永久可用。

## 9.2 写盘策略：延迟建文件，逐行追加

`_persist()`（约 L1040 起）的两个决定值得背下来：

**决定一：会话文件在第一条 assistant 消息出现前不存在。** 只发了 user 消息还没等到模型回复？entry 留在内存（`flushed=false`）。第一条 assistant 到来时才 `openSync(file, "wx")` 把积攒的全部 entry 一次写入。动机：避免为"打开 pi 问了一句就关"的场景制造垃圾文件。

**决定二：此后每条 entry 立即 `appendFileSync` 一行。** 不缓冲、不批量。原子性不靠临时文件+rename，而靠格式本身：**每行是独立 JSON，崩溃最多丢最后一行或留半行**。

配套的崩溃恢复（`loadEntriesFromFile`）：手写分块读取（1MB buffer + StringDecoder 处理 UTF-8 跨块），逐行 parse，**malformed 行直接跳过**；读完后若末行无换行（上次写了一半），补一个 `\n` 修复文件。宽松加载器 + append-only 格式，这是比"事务日志"轻得多但够用的可靠性方案。

## 9.3 分支：移动 leaf 指针，永不改写历史

四个 API，从轻到重：

```ts
branch(entryId)        // 只把 leaf 指针移到历史 entry。不删不改任何行。
                       // 下一次 append 就自然挂在该 entry 下 → 新分支诞生
resetLeaf()            // leaf 置 null，下次 append 成为新根（"重新编辑第一条消息"用）
branchWithSummary(id, summary)
                       // 移 leaf + 追加 branch_summary entry，
                       // fromId 记录被放弃的旧 leaf
createBranchedSession(leafId)
                       // 把 root→leaf 路径抽取到【新文件】（/fork 用）：
                       // 剥掉路径上的 label entry、重接父子链、
                       // remap compaction.firstKeptEntryId、写 parentSession
```

**洞察：分叉是 O(1) 的。** 因为历史永不改写，"回到过去重新来"只是移动一个指针。这是树形会话全部产品能力（/tree 导航、/fork、多方案探索）的数据结构基础。

### UI 命令如何落到这些 API

| 命令 | 效果 | API 路径 |
|---|---|---|
| `/tree` | 同文件内导航到任意历史节点 | `AgentSession.navigateTree()` → branch/branchWithSummary |
| `/fork` | 从某条 user 消息开**新文件** | runtime.fork("before"/"at") → createBranchedSession |
| `/clone` | 复制当前活动分支到新文件 | 同上 |
| `/new` `/resume` | 整会话替换 | runtime（第 4 章） |

`navigateTree()`（`agent-session.ts` 约 L3208 起）的目标语义有个贴心区分：选中 **user** 消息 → leaf 设为它的 parent、**原文回填编辑器**（编辑重发即生成分支）；选中 assistant/工具节点 → leaf 直接落到该处（从此继续）。

## 9.4 分支摘要：被离开的那条线发生了什么

切走分支时，旧 leaf 到公共祖先之间的对话就"不可见"了——但那些探索往往有价值（试过什么、为什么放弃）。`branch-summarization.ts` 解决这个问题：

```
collectEntriesForBranchSummary()
  // 求两条路径的最深公共祖先，收集"旧 leaf → 祖先"的全部 entry
  // （compaction 摘要也作为待摘要内容，不在压缩边界停）

prepareBranchEntries()
  // token 预算 = contextWindow - reserveTokens
  // 两遍扫描：先收集全部文件操作集合（含嵌套摘要里的），
  // 再从新到旧装消息直到预算

generateBranchSummary()
  // serializeConversation() 把对话转成 [User]/[Assistant] 标签纯文本，
  // 包 <conversation>，配结构化 prompt：
  //   Goal / Constraints / Progress / Key Decisions / Next Steps
  // 摘要前加 preamble："用户探索了另一条分支后回到这里…"
  // 尾部拼 <read-files>/<modified-files>（跨次累积的文件操作集合）
```

摘要作为 `branch_summary` entry 写进新分支，模型开局就知道"另一条线上试过什么"。`/tree` 切换时 UI 会问"是否摘要被离开的分支"（No summary / Summarize / 自定义 prompt），扩展也可经 `session_before_tree` 钩子接管。

## 9.5 resume：从文件到运行时会话

`createAgentSession()`（第 4 章）里的恢复链：

```
buildSessionContext()
  = buildSessionPath()              // leaf → 根，得到当前分支的 entry 路径
  → getSessionContextSettings()     // 沿途扫 model_change / thinking_level_change / assistant
  → buildContextEntries()           // 处理压缩边界（第 10 章）
  → sessionEntryToContextMessages() // entry → AgentMessage
```

模型恢复有 fallback 链（`restoreModelFromSession`）：会话里的模型（不存在/无鉴权时）→ 可用模型 → 默认表 → 第一个可用，并生成 `modelFallbackMessage` 提示用户。工具集恢复走 `_restoreToolsFromTranscript()`：从重放后的 system 消息 `toolsAdded` 重建（transcript 即真相的最后一次登场）。

## 9.6 设计权衡：为什么不用 SQLite / 单 JSON？

pi 的选择是"一个会话一个 JSONL 文件 + 树形 entry"。对照其他方案看它的得与失：

| 方案 | 得 | 失 |
|---|---|---|
| JSONL（pi 的选择） | 追加即持久（每条消息零延迟落盘）；人类可读可 grep；崩溃恢复简单；git/diff 友好；分叉 O(1) | 全量加载（有 header 快扫优化）；跨会话查询要遍历文件 |
| 单 JSON 文件 | 结构清晰 | 每次全量重写；写放大；崩溃易损坏 |
| SQLite | 查询强、事务强 | 不可读；并发与迁移复杂；对"每条消息即时落盘"没有额外收益 |

仓库其实两者都有：`packages/session-backends/sqlite-node` 是 SQLite 后端（供下一代 harness 用），说明这不是"不会用数据库"，而是对当前产品形态的判断——**单会话访问模式 + 人类可读性 + 追加式持久**，JSONL 恰好是最便宜的正确答案。

## 9.7 本章问题

1. `branch(entryId)` 之后追加的第一条消息的 parentId 是什么？此时文件里存在两个"叶子"，`buildSessionPath()` 如何知道该走哪条？（提示：leaf 指针在内存，重开后呢？——想想"最后一个 entry"默认值）
2. 为什么 `createBranchedSession` 要剥掉 label entry？不剥会发生什么？
3. 崩溃场景推演：进程在 `appendFileSync` 写到一半时被 kill。下次 `pi --session` 打开这个文件，加载、修复各发生什么？第 2 章问题 3 的答案（5 行 entry）现在能精确到字段了吗？

下一章：数据侧的第二站——上下文本身：system prompt 的组装与压缩。
