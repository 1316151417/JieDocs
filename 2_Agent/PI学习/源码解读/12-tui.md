# 第 12 章 tui 包：终端界面

> 本章回答：pi 的终端 UI 为什么不用 React/Ink 而自己造框架；`render(width): string[]` 这个极简协议如何撑起 6600 行的交互界面；差分渲染、流式 Markdown、中文输入法（IME）这些硬问题怎么解。
>
> 主要文件：`tui/src/tui.ts`（核心抽象）、`tui-main-screen.ts` / `tui-alt-screen.ts`（两个渲染器）、`components/editor.ts`（2462 行）、`autocomplete.ts`、`components/markdown.ts`。运行时依赖只有 2 个：marked、get-east-asian-width。

## 12.1 定位：保留式组件树 + 立即模式渲染

先给结论性的对比：

| | React/Ink 类方案 | pi-tui |
|---|---|---|
| 组件模型 | VDOM + reconciler + hooks | 组件树自持状态 |
| 更新触发 | 状态变更自动响应式 | 改完状态**手动** `tui.requestRender()` |
| 布局 | Yoga（flexbox 完整实现） | 宽度自外向内传、行数组自内向外拼；alt-screen 有精简 flex |
| 渲染 | diff 组件树 → patch | **diff 字符串行** → 只写变化行 |
| 依赖 | 数十 | 2 |

核心协议只有一个必须实现的方法：

```ts
interface Component {
  render(width: number): string[];   // 返回一行一个元素的字符串数组，行内可含 ANSI 转义
  handleInput?(data: string): void;  // 有焦点时收到原始终端输入
  handleMouse?(event): …;
  invalidate(): void;                // 清渲染缓存
}
```

宽度由外向内传递，行数组由内向外拼接（`Container.render()` = 顺序拼接子组件行）。TUI 每帧把整棵树拼成完整行数组，与上一帧做**行级字符串比较**。没有 measure/render 两阶段（除了 alt-screen 的布局节点）——因为"测量即渲染"：直接调 `render()` 缓存结果取行数。

这不是"作者不会用 React"：换来的是可预测性（没有 reconcile 时序问题）、极小运行时、以及对终端这种"全字符串介质"的直接性。代价是一切更新要手动请求——但 pi 的数据流本来就是事件驱动的（第 5 章），事件到达 → 组件改状态 → requestRender，模型完全吻合。

## 12.2 渲染：差分 + 同步输出

`TuiMainScreen.doRender()` 每帧：

```
1. render(width) 拼出 newLines
2. 有 overlay → compositeOverlays() 按列合成弹层
3. 扫 CURSOR_MARKER（IME 用，见 12.5）并剥离，算出硬件光标位置
4. 每行追加 SEGMENT_RESET（SGR 全重置 + OSC 8 链接重置）——样式不跨行泄漏
5. 三条路径：
   首帧              → 直接全量输出
   尺寸变化/变化区在视口上方 → 清屏全量重绘
   常规              → 线性比较求 firstChanged..lastChanged 区间，
                        光标移过去，逐行清行重写，只写到 lastChanged
6. 整个输出包在 \x1b[?2026h … \x1b[?2026l 里（CSI 2026 同步输出：
   终端在序列结束前不呈现中间状态——防闪烁的第二支柱）
```

细节见功力：`BoundedTerminalWriter` 按 1MiB 分块写（防 V8 单字符串上限，不拆代理对）；渲染超宽行直接 crash 并落盘完整诊断日志（`pi-tui-crash.log`）而不是渲染乱码；spinner 只改一行时 diff 天然只重写一行。

### 两种屏幕模式

- **TuiMainScreen（regular）**：保留终端 scrollback 的"追加式"聊天体验；
- **TuiAltScreen（fullscreen）**：进备用屏、固定高视口、应用自管滚动 + 鼠标 + flex 布局（`v-stack/h-stack/scroll-view`，basis/grow/shrink）；启动时关闭终端自动换行保证精确列控制，退出时把最终文档打印回主屏保留记录。

两个渲染器共享 `TuiBase`（焦点、overlay 栈、输入分发、16ms 渲染节流）。键盘路径用 `requestImmediateRender()` 绕过节流 timer（Windows 的 setTimeout(0) 可能吃掉整个 tick，键盘延迟敏感）。

## 12.3 Editor：终端里的文本编辑器

2462 行的 `components/editor.ts` 是包内最大组件，三个模型支柱：

**逻辑行/视觉行双模型**。状态是 `{lines, cursorLine, cursorCol}` 逻辑坐标；渲染时 word-wrap（基于 `Intl.Segmenter` 字素粒度，CJK 字符间允许断行）生成视觉行，`buildVisualLineMap()` 建立映射；点击、上下键、翻页都经映射换算。编辑操作永远在逻辑行上 O(1) 进行。

**大段粘贴折叠**。括号粘贴协议收到超 10 行/1000 字符的粘贴时，只插入 `[paste #N +123 lines]` 原子 marker（原文存 `pastes` 注册表）；marker 作为原子字素段参与分词/折行/删除；提交时 `expandPasteMarkers()` 还原全文。编辑器永远只看见"一行"，模型上下文和渲染都不会被打爆。

**历史与 undo**。100 条历史上限（去连续重复）；首次上翻存草稿；undo 栈 fish 风格合并（连续 word 字符一个单元）；Emacs kill-ring（Ctrl+Y/Alt+Y）。

按键处理的优先级链值得读原码（`handleInput`）：jump 模式 → 括号粘贴 → Ctrl+C 透传 → 补全激活态 → Tab → 删除类 → kill-ring → 历史 → 移动 → 换行（shift+enter 及其一堆终端兼容 fallback；光标前是 `\` 时 Enter 变换行——无 Shift+Enter 终端的逃生门）→ 提交 → 上下键（第一视觉行 + 特定条件才触发历史）→ 可打印字符。

## 12.4 自动补全：Provider 协议与异步治理

`autocomplete.ts` 的接口刻意不含 UI（展示由 Editor 内嵌 SelectList 负责）：

```ts
interface AutocompleteProvider {
  triggerCharacters?: string[];    // token 边界自然触发（@、#…）
  getSuggestions(lines, cursorLine, cursorCol, {signal, force}): Promise<Suggestions|null>;
  applyCompletion(...): {lines, cursorLine, cursorCol};
}
```

`CombinedAutocompleteProvider` 分发四类：`@` 前缀模糊文件补全（**外部 fd 子进程**，`fdPath` 为 null 时静默禁用——这就是第 3 章 fd 检查的下游）、`/` 斜杠命令（fuzzy 子序列匹配）、命令参数（`getArgumentCompletions` 钩子）、路径前缀补全（同步 readdirSync，目录结尾不加空格以便连续补全）。

异步防竞态做了四层：`@` 类 20ms debounce → Promise 链**串行化**（await 前一个任务）→ startToken 递增丢弃过期响应 → AbortController + 请求前快照校验。补全请求永远不与过期输入配对——这套治理模式在任何异步 UI 里都通用。

## 12.5 流式 Markdown 与代码高亮

`components/markdown.ts`：marked 解析 token 流 → 逐 token 生成 ANSI 行 → `wrapTextWithAnsi` 换行（用 AnsiCodeTracker 跟踪每行活动 SGR 状态，折行补前缀、行尾只 reset 该 reset 的）→ padding/背景。结果按 (text, width) 缓存。

流式输出的策略不是"增量 parse"，而是**重渲染 + 三层缓存兜住**：

1. 组件缓存：文本没变直接命中；
2. 16ms 渲染节流：token 到达频率远高于帧率；
3. 行级差分：前文渲染结果不变就不写终端。

两个流式专用的防抖动细节：`trimPartialClosingFences()` 处理代码块闭合 fence 逐字符到达时的"缩小再恢复"闪烁；未闭合的 LaTeX token 标记 `pending` 按原文显示而非渲染一半。代码高亮是注入点（`MarkdownTheme.highlightCode`），tui 本身不带高亮器——coding-agent 的主题系统注入实现。

## 12.6 键盘三协议与 IME（中文输入）

**键盘**：`keys.ts` 的 `matchesKey(data, "ctrl+c")` 一次匹配三种编码——legacy 转义序列（`\x1b[A`）、Kitty CSI-u、xterm modifyOtherKeys。协议协商发 `\x1b[>7u\x1b[?u\x1b[c`，尾随的 DA 查询作为哨兵：不支持的终端立刻回 DA，**无需启动超时**即可回退。`StdinBuffer` 处理转义序列跨 chunk 分片、孤立 ESC 等 10ms（SSH 自动放宽到 100ms）、Kitty 双发文本去重等真实脏细节。全部键位经 `KeybindingsManager` 可配置（`~/.pi/agent/keybindings.json`），无硬编码键检查（AGENTS.md 明文规定）。

**IME（输入法）**是终端 TUI 的经典难题：候选窗跟随硬件光标，但 TUI 通常隐藏硬件光标、自绘假光标，位置对不上。pi-tui 的方案值得整段学：

```
1. 组件在"假光标"（反白 \x1b[7m 的字符格）前输出
   CURSOR_MARKER = "\x1b_pi:c\x07"     ← APC 零宽序列，终端渲染时忽略
2. 每帧渲染后，框架扫描 marker：
   列号 = visibleWidth(marker 前缀)
   剥离 marker，把【硬件光标】移到该位置（\x1b[{row};{col}H）
3. 终端（macOS Terminal 等）用硬件光标位置摆放 IME 候选窗
```

假光标负责样式自由，marker 让框架"事后知道"假光标在哪——两个需求解耦。配套约定：含 Input/Editor 的容器组件必须实现 `Focusable` 并传播 `focused`，否则候选窗位置错误。宽度计算用 get-east-asian-width（emoji、组合附标、区域指示符、泰文 AM 元音都有处理），换行支持 CJK 字符间断行。

## 12.7 可测试性

`Terminal` 是接口（`start/write/moveBy/…`），生产用 `ProcessTerminal`，测试用 `VirtualTerminal`（`@xterm/headless`）——渲染结果可以在 node:test 里逐行断言。tui 的 48 个测试文件覆盖 overlay CJK 边界、区域指示符宽度等回归。这也解释了为什么 tui 是全仓库唯一用 node:test（而非 vitest）的包：零依赖直接执行 TS，从而要求全仓 erasable TypeScript 语法（AGENTS.md 的语法约束即源于此）。

## 12.8 本章问题

1. "测量即渲染"省掉了独立 measure API。什么情况下它会变贵？（提示：一个高度依赖内容的长列表，同帧多宽度渲染）pi 用什么机制兜住？（renderCache 按 (component,width) 键）
2. 流式 Markdown 为什么选择"整段重渲染 + 缓存"而不是"增量 parse 增量 append"？（从行级差分的存在推导：重渲染的真实成本是什么？）
3. 把 CURSOR_MARKER 方案迁移到 GUI：对应物是什么？（提示：合成窗口位置 vs 系统光标）

下一章：这么多层如何被测试钉住。
