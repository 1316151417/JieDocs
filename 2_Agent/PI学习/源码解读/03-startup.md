# 第 3 章 入口与启动流程

> 本章回答：敲下 `pi` 回车之后、看到输入框之前，程序做了什么；三种运行模式如何决定；为什么新会话输入 `/` 之前会先看到 fd 的加载提示（你曾经问过的那个体验问题，答案就在本章）。

## 3.1 入口链：从 bin 到 main()

```
packages/coding-agent/src/cli.ts          # 入口：setupCli() + main(argv)
  └─ cli/setup.ts setupCli()              # process.title、环境变量、静默 emitWarning、
                                          #   configureHttpDispatcher()（undici 配置必须在任何
                                          #   provider SDK 发请求之前完成）
       └─ cli/args.ts parseArgs()         # 手写参数解析器
            └─ main.ts main()             # 总编排
```

## 3.2 手写 CLI 解析器与"扩展 flag"机制

`parseArgs()`（`cli/args.ts`）是一个纯手写的 for 循环逐 token 解析器——**没有用 commander/yargs**。支持的关键参数：

| 参数组 | 例子 |
|---|---|
| 模型选择 | `--provider anthropic --model sonnet`、`--model anthropic/claude-...`、`--model sonnet:high`（冒号后是 thinking 档位） |
| 模式 | `-p/--print`、`--mode text\|json\|rpc` |
| 会话 | `-c`（继续最近）、`-r`（选择恢复）、`--session <path\|id>`、`--fork`、`--no-session` |
| 工具 | `--tools read,grep`（allowlist）、`--exclude-tools`、`--no-builtin-tools` |
| 资源 | `-e/--extension`、`--skill`、`--prompt-template`、`--theme` |
| 其他 | `@file`（文件参数拼进首条消息）、`--offline`、`--approve/--no-approve` |

最有意思的设计：**未知 `--flag` 不报错**，而是收进 `unknownFlags` 交给扩展系统认领。`pi --plan` 里的 `--plan` 就是 plan-mode 扩展注册的。这使扩展无需 fork 主程序就能注册 CLI 选项，`--help` 文本也动态拼接扩展 flag 的说明。

## 3.3 main() 时序

`main.ts` 的 `main()`（约 L561 起）按序做这些事，理解顺序很重要：

1. **auth 子命令**：`pi auth print-api-key` 等直接处理后返回；
2. **环境准备**：`cwd`、`agentDir`（默认 `~/.pi/agent`，`PI_CODING_AGENT_DIR` 可覆盖）；先用一个不信任项目的 bootstrap SettingsManager 读全局 HTTP 代理（翻墙场景下代理必须最先生效）；
3. **包管理子命令**：`pi package install/remove/...`（技能/扩展包管理）；
4. **迁移**：`runMigrations()`（旧版本数据升级）；
5. **首次启动引导**：主题选择 + telemetry opt-in（仅首次）;
6. **会话定位**（`createSessionManager`，分支较多）：

   | CLI 参数 | 行为 |
   |---|---|
   | 无 | `SessionManager.create()` 新会话 |
   | `-c` | `continueRecent()` 最近会话 |
   | `-r` | TUI 选择器挑一个 |
   | `--session <id/path>` | id 可前缀匹配；先在当前项目 sessions 找，找不到**全局跨项目搜索**，跨项目命中会询问是否 fork 到当前目录 |
   | `--fork` | 从既有会话分叉出新文件 |
   | `--no-session` | `inMemory()`，不落盘 |

7. **模式判定**（`resolveAppMode()`）：
   - `--mode rpc` → rpc；`--mode json` → json；
   - `-p` 指定，或 **stdin/stdout 任一不是 TTY** → print；
   - 否则 interactive。
   - 还有一个自动降级：想交互但 stdin 是管道（`cat file | pi`）→ 降级 print；
8. **Runtime 工厂**：`createRuntime` 闭包（约 L712 起）负责按目标 cwd 组装全部 cwd 绑定服务并 `createAgentSession()`。**注意时序**：`--session` 可能选中其他项目的会话，所以 cwd 绑定的服务必须等会话 cwd 确定后才能创建——这就是工厂是闭包、而非立即执行的原因（第 4 章展开）；
9. **stdin 管道读取、`@file` 参数加工、主题初始化**；
10. **分发**：

```ts
if (mode === "rpc")          runRpcMode(runtime);
else if (interactive)        new InteractiveMode(runtime, {...}).run();
else                         runPrintMode(runtime, { mode: "text" | "json", ... });
```

## 3.4 三种模式共享一个 runtime

启动分发的三分支背后是同一个 `AgentSessionRuntime`（持有当前 session + services）。三种模式只是三种"外设"：

| 模式 | 输入 | 输出 | 典型用途 |
|---|---|---|---|
| interactive | 键盘（tui Editor） | 终端 UI | 人用 |
| print (`-p`) | 参数 / stdin 管道 | 最终文本（text）或逐事件 JSON 行（json） | 脚本、管道 |
| rpc | stdin 逐行 JSON 命令 | `{type:"response"}` + 流式事件 | 嵌入其他应用（编辑器插件、WebUI） |

`print --mode json` 的输出协议值得一记（第 5 章会看到它的实现 `toJsonEvent`）：先输出一行 session header，然后每个事件一行 JSON；`message_update` 事件被剥掉累积快照只留增量——协议设计是"start 给初始、delta 增量构建、end 给权威终态"。

## 3.5 交互模式初始化：你问过的"fd 加载"

`InteractiveMode.init()`（`interactive-mode.ts` 约 L856 起）的时序：

1. 注册信号处理、解析 changelog（新版本时显示）；
2. 构建 fullscreen 布局并挂载 TUI（`mountInteractiveTui()`）；
3. **先启动 UI，再初始化扩展**（源码注释明确：`ui.start()` 之后扩展的 `session_start` handler 才能用交互式 dialog）；
4. 此阶段编辑器只绑定一个"启动仍在进行"的占位 submit handler；
5. **fd / rg 工具检查**：`await Promise.all([ensureTool("fd"), ensureTool("rg")])`；
6. 工具就绪后才 `setupKeyHandlers()` + `setupEditorSubmitHandler()`，完整输入启用；
7. `rebindCurrentSession()`：绑定扩展、订阅 agent 事件、渲染历史消息；
8. 异步收尾：主题 watcher、git 分支 watcher、语法高亮语言补齐、模型目录刷新、新版本检查。

**第 5 步就是你观察到的现象**：新会话启动后输入 `/` 没反应、先看到 fd 相关加载——实际是启动流程尚未走到第 6 步，输入处理还没启用。补充三个事实：

- slash 命令候选**早就在内存里**（`BUILTIN_SLASH_COMMANDS` + 扩展命令 + 模板命令），`/` 菜单本身不依赖 fd；
- fd 是给 `@` 文件路径补全用的（第 12 章），rg 是给 grep 工具用的；
- `ensureTool()`（`utils/tools-manager.ts`）先查 pi 管理目录（`~/.pi/agent/bin/`）→ 再查系统 PATH → 都没有才从 GitHub Releases 下载（用 `releases/latest` 重定向解析版本号，规避 GitHub API 匿名配额）。**已安装时检查很快返回，不会重复下载**；如果你每次都看到"Downloading"，那是异常，值得提 issue。

把这两件事放一起就能评价这个设计：fd 检查放在 TUI 挂载之后（慢下载不阻塞界面出现）是对的；但输入处理放在 fd 检查之后，导致 `/` 菜单这种不依赖 fd 的功能也被拖住——这就是你感觉体验差的根因。改进方向很明确：输入处理先行，fd 就绪只影响 `@` 补全。

## 3.6 主循环：编辑器与执行的解耦

interactive 模式的主循环极简（`run()` 约 L1136 起）：

```ts
while (true) {
  const userInput = await this.getUserInput();
  await this.session.prompt(userInput);
}
```

`getUserInput()` 的实现是"回调或队列"双通道：

- 空闲时，编辑器 submit 回调直接 resolve 挂起的 Promise；
- 主循环正忙于 `session.prompt()` 时，submit 进 `pendingUserInputs` 数组等下一轮。

这个解耦让"用户在模型流式输出期间还能打字提交"成为自然结果：提交路径判断 `session.isStreaming`，走 steering 分支（第 2 章 2.2 的分流表、第 5 章的队列语义），主循环则永远只消费"空闲输入"。

## 3.7 启动性能工程

这个 6600+ 行的交互模式在启动上做了不少事，值得注意的手法：

- `time()` 全链路打点（`core/timings.ts`），`PI_STARTUP_BENCHMARK=1` 打印分段耗时；
- 一切非关键路径异步化：changelog 解析、语法高亮语言加载、版本检查、模型目录刷新（15s 超时兜底）；
- "UI 先可见、能力后到位"的次序（上文第 3/5 步）；
- print 模式 `takeOverStdout()`（`core/output-guard.ts`）接管 stdout，防止依赖库的 console.log 污染 JSON 输出流。

## 3.8 本章问题

1. 为什么 `createRuntime` 是闭包而不是启动时直接执行一次？（联系 `--session` 跨项目恢复的场景）
2. `cat bug.log | pi -p "解释这个日志"` 和在终端里运行 `pi` 再粘贴内容，走的模式判定有何不同？
3. 如果要修复"`/` 菜单被 fd 检查拖住"，你会调整 3.5 节时序图的哪两步顺序？需要连带改动什么？

下一章：进入 `createRuntime` 闭包内部，看会话是如何被组装出来的。
