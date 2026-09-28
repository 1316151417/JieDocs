# 第 7 章 工具执行系统

> 本章回答：一个工具在 pi 里的完整形状；8 个内置工具各自的实现要点（edit 的匹配算法、bash 的进程管理值得细读）；工具输出如何截断；以及 pi 为什么没有内置审批。文件位置：`coding-agent/src/core/tools/`。

## 7.1 AgentTool 接口：content 给模型，details 给界面

回顾内核定义的工具接口（`agent/src/types.ts`），再看 coding-agent 侧的工厂模式：

```ts
interface AgentTool<TParameters, TDetails> {
  name: string;
  description: string;               // 给模型的说明
  parameters: TSchema;               // typebox Type.Object(...) —— JSON Schema
  label: string;                     // UI 显示名
  prepareArguments?(args): params;   // schema 校验前的兼容 shim
  execute(toolCallId, params, signal?, onUpdate?): Promise<AgentToolResult>;
  executionMode?: "parallel" | "sequential";  // per-tool 覆盖整批策略
}

interface AgentToolResult<TDetails> {
  content: (TextContent | ImageContent)[];  // ★ 给模型看的
  details?: TDetails;                       // ★ 给 UI/日志看的结构化数据
  usage?: Usage;                            // 工具自身的 LLM 用量（如子代理）
  isError?: boolean;
  terminate?: boolean;
}
```

**content 与 details 分离**是本系统的第一原则：模型只需要文本（或图片），界面需要 diff、截断元数据、路径列表等富信息。配套地，`core/tools/renderers/` 目录独立实现各工具的渲染——"只显示工具输出的进程不加载执行路径和 typebox schema"。

每个内置工具都是 `createXxxToolDefinition(cwd, options)` 工厂，参数 schema 用 typebox 声明（这同时是给模型的参数文档和运行时校验器）。`constrainedSampling: { type: "json_schema", strict: "prefer" }` 让支持的厂商启用严格结构化输出。

默认启用 4 个：`read / bash / edit / write`；`grep / find / ls` 是只读工具、**默认关闭**（`--tools` 或 settings 开启）；Windows 上 powershell 替代 bash。

## 7.2 八个内置工具逐个看

### read（`tools/read.ts`）

- 输入 `{ path, offset?(1-based), limit? }`；
- 文本：按行切片，截断上限 **2000 行 / 50KB 双上限**（取先到者）；输出**纯内容不带行号**，截断时附行动提示 `[Showing lines A-B of N. Use offset=B+1 to continue.]`——把"怎么继续读"告诉模型；
- 图片：按 MIME 识别，自动缩放（默认 2000x2000 上限）后作为 image content 返回；非视觉模型附注"图片将被忽略"；
- 一个有趣的防御：路径找不到时重试 macOS 变体——截图文件名里的窄不换行空格、NFD Unicode、花引号（`'`→`'`）。LLM 抄写文件名的错误分布是真实数据驱动的；
- `ReadOperations` 接口可插拔（readFile/access/mime 检测），远程后端（SSH/容器）由此接入。

### bash（`tools/bash.ts`）

进程管理是这个工具的全部重量：

- `getShellConfig()` 拿 shell 路径；命令经 **stdin 传输**（防 ps 进程列表泄露命令内容）；
- `spawn` 时 `detached: true`（非 Windows）+ `trackDetachedChildPid` 跟踪 detached 子进程——**pi 退出时统一 kill，不留孤儿**；
- 超时/abort → `killProcessTree()` 杀整棵进程树（不只杀直接子进程）；
- `waitForChildProcess` 的写法保证不被 detached 后代持有的 stdio 挂死；
- 无 exitCode（被信号杀）→ 按 shell 惯例返回 `128 + signal`；
- 输出用 `OutputAccumulator` 流式累积，**尾部截断**（最后 2000 行/50KB——命令输出尾部通常最有用），与 read 的 head 截断形成对照；**截断时全量输出写入临时文件**，结果里给 `fullOutputPath`；
- `onUpdate` 节流推送实时输出（UI 的 BashExecutionComponent 靠它流式刷新）；
- 非零退出码 → throw（转 isError 结果）；abort → "Command aborted"；
- 环境注入：`PI_SESSION_ID / PI_SESSION_FILE / PI_PROVIDER / PI_MODEL / PI_REASONING_LEVEL`（`exposeSessionEnvironment` 默认开），系统提示鼓励模型自检这些变量；
- `BashOperations` + `spawnHook`（改写 command/cwd/env）+ `commandPrefix` 三个扩展点。

### edit（`tools/edit.ts` + `edit-diff.ts`）——最值得精读

输入 `{ path, edits: [{oldText, newText}, ...] }`，**单调用多编辑**（减少往返），全部匹配基于"原始文件"而非增量。

`prepareArguments` 兼容 shim 值得一看：模型会把 edits 发成 JSON 字符串（某些模型的高频错误）、单个对象、或 legacy 顶层字段——shim 全部归一化成数组。这是"模型会犯什么错"的又一处经验沉淀。

匹配与应用算法（`edit-diff.ts`）：

```
预处理：剥 BOM、检测行尾(CRLF/LF)、归一化为 LF
对每个 edit：
  1. 精确 indexOf 匹配
  2. 失败 → fuzzy：NFKC 归一化 + 每行去尾空白 +
     智能引号→ASCII + Unicode 破折号→"-" + 特殊空格→普通空格
     （全部针对 LLM 高频抄写错误）
  3. 唯一性校验：匹配多处 → 报错要求更多上下文
重叠校验：多个 edit 区间重叠 → 报错要求合并
应用：按位置逆序替换（offset 稳定）
  ★ fuzzy 命中时行级回贴：被改动行来自归一化内容，
    未动行保留原文件字节——避免归一化污染整个文件
写回：恢复 BOM 与原始行尾
```

并发安全：`withFileMutationQueue` 按 **realpath** 维护全局 Promise 链，同一文件的写操作串行（不同文件仍并行）。abort 的处理方式也讲究：不 reject 队列锁，而是"每个 await 后检查 signal.aborted"——保证锁在 in-flight fs 操作 settle 前不释放（源码注释专门解释这一点）。

返回 details 带 `diff`（自研格式：`+行号/-行号` + 4 行上下文 + 长距离折叠）和标准 unified patch。UI 在**参数流完、执行前**就用 `computeEditsDiff` 算出预览——用户看到 diff 的时刻早于文件被改动的时刻。

### write（`tools/write.ts`）

`{ path, content }`；自动 `mkdir -p` 父目录；同一 mutation queue 串行。指南明说"只用于新文件或整体重写"（改现有文件该用 edit）。

### grep（`tools/grep.ts`）——ripgrep 子进程

- `ensureTool("rg")` 保证二进制存在（第 3 章的自动下载）；
- `rg --json --line-number --hidden ...`，选项映射 ignoreCase/literal/glob；默认尊重 .gitignore；
- readline 逐行解析 rg 的 JSON 事件流；`limit`（默认 100）达到即 `child.kill()` 提前终止——不读完整个仓库；
- 单行截断 500 字符、总量 50KB；超限附 `Use limit=200 for more` 提示。

### find（`tools/find.ts`）——fd 子进程

- `fd --glob --hidden --max-results N pattern path`；
- git 仓库检测：只有在仓库**外**才加 `--no-require-git`（让 .gitignore 在嵌套仓库边界正确停止，源码注释引用了对应 issue）；
- 模式含 `/` 时切 `--full-path` 并自动补 `**/` 前缀。

### ls / powershell

- ls：纯 Node `fs.readdir`，大小写不敏感排序、目录加 `/` 后缀、包含 dotfiles、limit 500；
- powershell：完全复用 bash 的 `createShellToolDefinition`，只换 shell 配置并前置 UTF-8 设置。

## 7.3 截断策略的系统观

把四个工具的截断放一起看，能看到明确的设计语言：

| 工具 | 截断方向 | 理由 | 续读方式 |
|---|---|---|---|
| read | 头部（head） | 文件开头通常足够 | `offset=B+1` |
| bash | 尾部（tail） | 命令输出尾部最有用（错误、最终结果） | `fullOutputPath` 临时文件 |
| grep / find | 数量上限 | 100 / 1000 条 | `limit=2N` 提示 |

统一常量（2000 行 / 50KB）来自 `tools/truncate.ts`。共同点：**每次截断都附带给模型的行动指令**——截断不是错误，是一次带说明的对话。

## 7.4 工具的注册与过滤

`AgentSession._refreshToolRegistry()` 是唯一注册点，合并四个来源：内置工厂、扩展注册、SDK custom 工具、`sendCustomMessage` 临时注入。全部过同一道过滤：

```
_allowedToolNames（--tools / ctx.setActiveTools）
  ∩ 排除 _excludedToolNames（--exclude-tools）
```

第 5 章说过：工具集变化会走 system prompt diff 通知模型（transcript 即真相）。

## 7.5 权限模型：没有内置审批，及它意味着什么

先说结论：**pi 没有内置的 permission modes（default/acceptEdits/yolo）、没有 allow/block/always-allow 审批 UI**。`docs/security.md` 写明这是刻意的：

> 进程内的"部分沙箱"很容易被误解为安全边界。pi 以启动用户的权限运行；文件系统信任边界 = 用户可写的文件。真正的隔离应来自 OS/容器（配套 `docs/containerization.md`）。

实际存在的控制是四层，强度递增的顺序理解：

1. **工具启用名单**（本节上文）——控制"有没有这个能力"；
2. **扩展拦截**：`tool_call` 事件（经 `beforeToolCall` 串到扩展）返回 `{block: true, reason}` 即拦截；批内全部 terminate 可停整个 agent。官方文档给出的"审批"实现就 6 行：

   ```ts
   pi.on("tool_call", async (event, ctx) => {
     if (event.toolName === "bash" && event.input.command?.includes("rm -rf")) {
       const ok = await ctx.ui.confirm("Dangerous!", "Allow rm -rf?");
       if (!ok) return { block: true, reason: "Blocked by user" };
     }
   });
   ```

   `event.input` 还可**原地修改参数**。"always allow" 这类状态由扩展自持（官方示例 `timed-confirm.ts`、`dirty-repo-guard.ts` 就是现成参考）；
3. **项目信任**（第 4 章）：管的是"仓库能不能注入配置/扩展"，不是"模型能不能执行命令"——两者常被混淆；
4. **OS/容器**：官方认可的真正隔离层。

对比 Claude Code 的内置 permission 体系，这是两种哲学：**把审批做成产品功能**（开箱即用、粒度统一、不可绕过）vs **把审批做成扩展事件**（默认无摩擦、行为完全可编程、信任模型诚实）。评价见仁见智，但 pi 的选择与它"业务下沉 SDK、界面只是渲染器"的整体架构自洽——审批 UI 本质上是一种界面，而界面层在 pi 里是可替换的。

## 7.6 本章问题

1. 为什么 bash 用 tail 截断而 read 用 head？如果你新增一个 `logs` 工具（读日志文件），会选哪种？
2. edit 的 fuzzy 匹配命中后为什么要"行级回贴"而不是直接写回归一化后的全文？构造一个会被归一化破坏的真实文件（提示：含智能引号的 markdown）。
3. 不看源码回答：`--tools read,grep` 下模型调用 bash 会发生什么？这个结果如何回到模型？（第 6 章的 prepareToolCall）

下一章：向下进入 ai 包，看 `streamFn` 背后的统一模型层。
