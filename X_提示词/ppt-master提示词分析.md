# Agent 遵从超长流程的提示词技巧

> 从 PPT Master 的 ~2,900 行 Prompt 中提炼出的 Agent 流程控制技术。
> 这些技巧解决了 AI Agent 在执行多步骤、长上下文任务时的三大顽疾：**跳步、漂移、编造**。

---

## 一、问题定义：为什么 Agent 无法遵从长流程？

在没有工程化约束的情况下，让 AI Agent 执行一个 7 步串行流水线（含 30+ 页内容生成），会遭遇三类核心问题：

| 问题 | 表现 | 根因 |
|------|------|------|
| **跳步** | 跳过验证直接执行、合并多步为一步 | AI 倾向于"高效"，认为验证是多余的 |
| **漂移** | 第 20 页的颜色/字体与第 1 页不同 | 上下文压缩导致早期信息被遗忘 |
| **编造** | 声称已完成检查但实际没有、虚构使用了某个模板 | AI 倾向于取悦用户，给出"看起来完成了"的回答 |

PPT Master 的 ~2,900 行 Prompt 几乎全部围绕这三类问题展开。以下逐一拆解其应对技巧。

---

## 二、技巧 1：铁律前置 + 优先级标记

### 做法

将最重要的规则放在文件的**最开头**，使用最高视觉优先级标记：

```markdown
> [!CAUTION]
> ## 🚨 Global Execution Discipline (MANDATORY)
>
> **This workflow is a strict serial pipeline. The following rules have the
> highest priority — violating any one of them constitutes execution failure:**
>
> 1. SERIAL EXECUTION — Steps MUST be executed in order
> 2. BLOCKING = HARD STOP — wait for explicit user response
> 3. NO CROSS-PHASE BUNDLING — FORBIDDEN
> ...
```

### 为什么有效

1. **位置效应**：上下文压缩时，文件开头的内容最后被截断
2. **视觉层级**：`[!CAUTION]` + `🚨` + `MANDATORY` + `HIGHEST PRIORITY` 多重视觉信号叠加，确保 Agent 将其识别为不可违反的约束
3. **等价定义**：`"violating any one of them constitutes execution failure"` ——将违反规则等价为"执行失败"，触发了 Agent 对"任务失败"的回避倾向

### 普适用法

```
在任意长流程 Prompt 的最开头，放置 3-8 条不可违反的铁律。
用视觉标记（emoji、大写、警告框）制造"不可忽视"感。
每条铁律必须对应一种你实际遇到过的 Agent 失效模式。
```

---

## 三、技巧 2：GATE / Checkpoint 链式自校验

### 做法

每一步都定义了**进入门**（GATE）和**完成检查点**（Checkpoint），形成严格的链式结构：

```markdown
### Step 4: Strategist Phase

🚧 **GATE**: Step 3 complete; default free-design path taken, or template files copied.

[... 执行内容 ...]

**✅ Checkpoint — Phase deliverables complete, auto-proceed to next step**:
- [x] Eight Confirmations completed (user confirmed)
- [x] Design Specification & Content Outline generated
- [x] Execution lock (spec_lock.md) generated
- [ ] **Next**: Auto-proceed to [Image_Generator / Executor] phase
```

### 为什么有效

1. **GATE 阻断跳步**：Agent 在进入下一步前必须"验证"前置条件——即使它只是自言自语地确认，也比直接跳入强得多
2. **Checkpoint 提供结构化确认**：`- [x]` 清单格式迫使 Agent 逐项确认，而非笼统地说"我完成了"
3. **Next 消除歧义**：明确告知下一步是什么，消除 Agent 的"猜疑"

### 普适用法

```
每个步骤都定义：
  🚧 GATE: [前置条件列表]
  ... 执行内容 ...
  ✅ Checkpoint: [- [x] 完成项, - [ ] 下一步]
```

---

## 四、技巧 3：外置记忆体 — spec_lock.md 模式

### 做法

将关键设计参数（颜色、字体、图标、节奏）提取为一份**独立的短文件**，强制 Agent 在每次操作前重新读取：

```markdown
> Before generating **each** SVG page, `read_file <project_path>/spec_lock.md`.
> Use only values from this file, not from memory.
```

`spec_lock.md` 本身只有约 50 行，包含：

```yaml
colors:
  primary: "#005587"
  secondary: "#E8F0FE"
typography:
  body: 18px
  font_family: "Microsoft YaHei, sans-serif"
icons:
  library: chunk-filled
  inventory: [home, chart-bar, users]
page_rhythm:
  P01: anchor
  P02: dense
  P03: breathing
```

### 为什么有效

这是**最核心的防漂移技巧**，原理是：

1. **不信任 Agent 的记忆**：随着对话变长，早期信息会被压缩甚至丢失。与其指望 Agent 记住第 1 步设定的颜色，不如让它每次都从文件重新读取
2. **短文件 < 长文件**：`spec_lock.md` 只有 ~50 行，每次读取的 token 成本极低；而 `design_spec.md` 有 ~300 行，读取成本高且容易被截断
3. **机器可读 > 自然语言**：YAML 格式的参数比嵌在长篇叙述中的描述更容易被 Agent 精确引用
4. **显式禁止记忆引用**：`"Use only values from this file, not from memory"` ——直接堵死了 Agent "我觉得应该是蓝色"的倾向

### 普适用法

```
对于任何需要跨步骤保持一致性的参数（颜色、风格、配置）：
1. 在流程早期生成一份短小的"锁定文件"
2. 强制后续每一步执行前重新读取该文件
3. 显式禁止使用"记忆"中的值
4. 锁定文件中的值就是"真理"，与之冲突则锁定文件胜出
```

---

## 五、技巧 4：禁用清单 + 显式替代方案

### 做法

不只告诉 Agent "不要做什么"，还**同时提供正确的替代方案**：

```markdown
| 禁用写法 | 正确替代 |
|---------|---------|
| `fill="rgba(255,255,255,0.1)"` | `fill="#FFFFFF" fill-opacity="0.1"` |
| `<g opacity="0.2">...</g>` | 在每个子元素上设置 `fill-opacity` / `stroke-opacity` |
| `<image opacity="0.3"/>` | 在图片上方叠加一个带透明度的 `<rect>` 遮罩 |
```

以及更极端的完全禁用列表：

```markdown
| Banned Feature | Description |
|----------------|-------------|
| `mask` | 遮罩 |
| `<style>` | 内嵌样式表 |
| `class` | CSS 选择器属性 |
| `<foreignObject>` | 嵌入外部内容 |
| `textPath` | 沿路径文字 |
| `<animate*>` / `<set>` | SVG 动画 |
| `<script>` | 脚本 |
```

### 为什么有效

1. **正反对照消除歧义**：单独说"不要用 rgba"可能被理解为"不要用透明度"；提供替代方案后语义变得精确——"用 HEX + fill-opacity 代替 rgba"
2. **表格格式易于检索**：Agent 在生成代码时，可以快速对照表格自查
3. **理由内置**：某些禁用项附带了原因（"PPT 不支持"），这比纯粹的禁令更容易被遵守

### 普适用法

```
对于每个约束，提供三列：[禁用写法] [正确替代] [原因]
用表格而非段落呈现，降低 Agent 的理解成本
```

---

## 六、技巧 5：审计追踪 — 证明你真的做了

### 做法

要求 Agent 提供不可伪造的"证据"，证明它确实执行了某个操作：

```markdown
**Read-audit (mandatory, written at the top of section VII)**

Catalog read: <N> templates / <M> categories

Per-page selection:
  P03 bar_chart | summary-quote: "<从 charts_index.json 粘贴的原文>"
  P07 line_chart | summary-quote: "<原文粘贴>"

Runners-up considered (at least 3):
  <key_A> | rejected for P03: <基于本项目具体内容的理由>
```

关键约束：`summary-quote` 必须**逐字粘贴**自索引文件，不允许改写或总结。

### 为什么有效

1. **不可伪造**：如果 Agent 没有真的读过 `charts_index.json`，它无法提供逐字的 `summary-quote`
2. **必须可 grep**：所有引用的 key 必须能在索引文件中 grep 到——拼错或编造的 key 会立即暴露
3. **Runner-up 机制**：要求列出"被拒绝的备选项"和"拒绝理由"，迫使 Agent 做了真正的比较而非随手选一个

### 普适用法

```
要求 Agent 在做出选择时：
1. 提供原文引用（不可改写）作为证据
2. 列出被拒绝的备选项及理由
3. 确保所有引用可在源文件中验证
```

---

## 七、技巧 6：决策树替代开放式提问

### 做法

每当需要 Agent 做出判断时，不问开放性问题，而是提供**文本决策树**：

```
Content characteristics?
  ├── Heavy imagery / promotional ──→ A) General Versatile
  ├── Data analysis / progress report ──→ B) General Consulting
  └── Strategic decisions / persuading executives ──→ C) Top Consulting

Audience?
  ├── Public / clients / trainees ────→ A) General Versatile
  ├── Teams / management ────────────→ B) General Consulting
  └── Executives / board / investors → C) Top Consulting
```

再比如画布格式选择：

```
Content purpose?
  ├── Presentation ──→ Audience size?
  │     ├── Large audience ──→ ppt169 (16:9)
  │     └── Traditional setting ──→ ppt43 (4:3)
  ├── Social sharing ──→ Platform?
  │     ├── Xiaohongshu ──→ xhs (3:4)
  │     └── WeChat ──→ wechat (宽屏)
  └── Marketing ──→ Story / poster format
```

### 为什么有效

1. **消除自由度**：开放性问题（"请选择合适的风格"）给 Agent 过大的自由度，容易选错；决策树将多维度判断分解为二叉选择
2. **可追溯**：Agent 可以引用决策路径证明其选择的合理性
3. **两个维度交叉验证**：上面的"风格选择"同时从"内容特征"和"受众"两个维度出发——如果两个维度指向不同答案，说明需要向用户确认

### 普适用法

```
将多维度判断转化为树状结构，用 └─┬─ 字符树呈现。
每层只做二选一或三选一，避免"请综合考虑以下 N 个因素"。
```

---

## 七、技巧 7：参数化约束 — 比例尺而非固定值

### 做法

字体大小不写死"24px"，而是用**锚定于基线的比例区间**：

```markdown
| Level | Ratio to body | 24px baseline | 18px baseline |
|-------|---------------|---------------|---------------|
| Cover title | 2.5-5x | 60-120px | 45-90px |
| Chapter opener | 2-2.5x | 48-60px | 36-45px |
| Page title | 1.5-2x | 36-48px | 27-36px |
| **Body** | **1x** | **24px** | **18px** |
| Annotation | 0.7-0.85x | 17-20px | 13-15px |
```

并附加强约束：

```markdown
> Sizes outside every band remain forbidden — surface the need and extend
> spec_lock.md typography rather than invent a one-off value.
```

### 为什么有效

1. **适配不同场景**：基线 18px（密集信息）和 24px（宽松排版）都能适用，不需要为每种场景写一套固定值
2. **保留有限灵活性的同时设定硬边界**：Agent 可以在比例区间内选择中间值（如 40px），但不得越界（不能出现 200px 的标题）
3. **异常值暴露机制**：超出所有区间的值必须"先扩展 spec_lock.md 再使用"，而不是偷偷使用

### 普适用法

```
将固定值改为 [锚定值] × [比例区间] 的形式。
提供一个参考换算表（两列基准值）。
超出比例区间的值需要显式声明并更新锁定文件。
```

---

## 八、技巧 8：负向约束 > 正向指令

### 做法

PPT Master 的 Prompt 中，**禁令的数量远多于指令**。以下是一些典型模式：

**"禁止"格式**：
```markdown
> ❌ **NEVER** combine them into a single code block or shell invocation.
> ❌ **NEVER** substitute `cp` for `finalize_svg.py`
> ❌ **NEVER** export from `svg_output/` — MUST use `-s final`
> ❌ **NEVER** add extra flags like `--only`
```

**"DO NOT"格式**：
```markdown
> Do NOT preload any index file
> Do NOT silently switch paths based on perceived host capability
> Do NOT halt the pipeline
> Do NOT use regex / bulk replacement -- coordinates are positional
> Do NOT create new placeholder families such as {{CHAPTER_01_TITLE}}
```

**"FORBIDDEN"格式**：
```markdown
> Cross-phase bundling is FORBIDDEN
> Delegating page SVG generation to sub-agents is FORBIDDEN
> Grouped page batches (for example, 5 pages at a time) are FORBIDDEN
```

### 为什么有效

1. **LLM 的"热心"倾向**：Agent 天生倾向于"多做一些"来表现效率——负向约束直接堵死这条路径
2. **消除解释负担**：正向指令（"请按顺序执行"）需要 Agent 理解"顺序"的含义；负向约束（"禁止跨阶段打包"）直接定义了违规行为的边界
3. **视觉标记增强感知**：`❌ NEVER`、`FORBIDDEN`、大写字母 —— 这些都是 Agent 训练数据中高频出现且与"绝对禁止"强关联的标记

### 普适用法

```
对于每种你观察到的 Agent "多此一举"的行为：
  写一条显式的 "❌ NEVER / FORBIDDEN / Do NOT" 规则
  附带一个具体的违规示例
```

---

## 九、技巧 9：受控词汇 + 白名单

### 做法

限制 Agent 只能使用预定义的值，禁止"发明"新值：

**图标白名单**：
```markdown
> inventory lists approved icon names; Executor may only use icons from this list.
> library MUST be exactly one of [chunk-filled | tabler-filled | tabler-outline |
> phosphor-duotone] — mixing is forbidden.
```

**节奏标签受控词汇**：
```markdown
page_rhythm:
  P01: anchor    # 只能是 anchor / dense / breathing 之一
  P02: dense
  P03: breathing
```

**占位符受控词汇**（模板设计）：
```markdown
> Do NOT create new placeholder families such as {{CHAPTER_01_TITLE}}
> for new templates. Only the canonical set is allowed.
```

### 为什么有效

1. **缩小搜索空间**：Agent 在受限词汇中选择，比在无限空间中创造，出错概率低几个数量级
2. **可验证**：事后可以 grep 检查是否有不在白名单中的值出现
3. **防止"创意"**：Agent 的"创意"在需要精确性的场景中是危险的——受控词汇直接关闭了创意通道

### 普适用法

```
对任何需要一致性的维度（颜色、字体、标签、状态值）：
1. 定义一个明确的允许值列表
2. 显式禁止使用列表外的值
3. 提供"发现需要新值时的升级路径"（如扩展 spec_lock.md）
```

---

## 十、技巧 10：有限重试 + 优雅降级

### 做法

不为每个失败点设计完美的恢复方案，而是设定**有界重试 + 标记降级**：

```markdown
# 图片生成失败时：
> Retry once. If the retry also fails, stop attempting that image.
> Do NOT halt the pipeline.
> Mark the affected rows as Needs-Manual, report to user, and continue.

# 图表校准无法自动化时：
> If a stack page's segment positions don't reduce to this recipe...
> mark it manual-verify... do not silently pass.

# 模板匹配失败时：
> Mark the page `no-template-match` with the fallback chosen and why.
> Do NOT silently substitute a close-but-wrong chart.
```

### 为什么有效

1. **防止死循环**：`Retry once` 限定最多重试一次，避免 Agent 陷入无限重试
2. **防止流程中断**：`Do NOT halt the pipeline` 确保一个局部失败不会拖垮整体
3. **诚实标记**：`Needs-Manual` / `manual-verify` / `no-template-match` 这些状态不是"掩盖失败"，而是**显式告知用户需要人工介入**——这比 Agent 假装成功要好得多

### 普适用法

```
每个可能失败的环节：
1. 最多重试 N 次
2. 重试失败后标记为"需人工"
3. 继续执行后续步骤
4. 在最终输出中汇总所有"需人工"的项
```

---

## 十一、技巧 11：确定性路径选择 — 消除"自作主张"

### 做法

当存在多条执行路径时，用**确定性触发条件**消除 Agent 的"自作主张"：

```markdown
| Situation | Action |
|-----------|--------|
| Default — no explicit override | Path A (built-in tool) |
| User explicitly names the host's native image tool | Path B (native tool) |

> Agent must NOT silently switch paths based on perceived host capability.
```

模板选择也是同理：

```markdown
**Template flow is opt-in.** Enter it only when an explicit trigger appears:
1. Names a specific template (e.g., "用 mckinsey 模板")
2. Names a style that maps to a template (e.g., "McKinsey 那种")
3. Asks what templates exist (e.g., "有哪些模板可以用")

When NO trigger fired → proceed to free design. Do NOT ask the user.
```

### 为什么有效

1. **消除 Agent 的"好心办坏事"**：Agent 可能觉得"用户大概想用模板"，就主动问一嘴——这在长流程中是致命的，因为每个额外的确认点都是流程停滞的风险
2. **触发条件可审计**：Agent 可以引用触发条件证明其路径选择的合理性
3. **默认路径无交互**：最常用的路径（自由设计）完全不需要用户介入

### 普适用法

```
为每条可选路径定义：
1. 精确的触发条件（用户说了什么 / 内容特征是什么）
2. 默认路径（无触发时的行为）
3. 禁止自作主张的显式规则
```

---

## 十二、技巧 12：阶段性自检清单

### 做法

在每个角色/阶段的末尾，放置一份**自检清单**：

```markdown
## Self-Check Supplement (Consultant Top)

### Content Level
- [ ] Every data point has comparison context (golden rule)
- [ ] Titles are assertion-style, not descriptive
- [ ] SCQA narrative arc is traceable through page sequence

### Visual Level
- [ ] No more than 3 primary colors used
- [ ] Accent color appears at most 2-3 places globally
- [ ] Every breathing page has a clear independent message

### Notes Level
- [ ] Key points follow conclusion-first structure
- [ ] Flex items are annotated where applicable
- [ ] Total duration sums to expected range
```

### 为什么有效

1. **结构化自省**：清单比"请检查你的工作"有效得多——它告诉 Agent **检查什么**、**怎么检查**
2. **分级维度**：Content / Visual / Notes 三个维度确保不遗漏任何一个方面
3. **可勾选格式**：`- [ ]` 格式暗示 Agent 需要逐项确认

### 普适用法

```
在每个阶段结束时提供分类自检清单。
每个检查项都是一个可验证的是/否判断。
按维度分组，避免"大杂烩"式清单。
```

---

## 十三、技巧 13：文件分离的分层 Prompt 架构

### 做法

不是把所有规则写在一个巨大的 Prompt 中，而是**按职责分离为多个文件**，按需读取：

```
CLAUDE.md（入口 - 50 行）
  └→ SKILL.md（流程 - 339 行）
       ├→ strategist.md（策略师 - 458 行）
       ├→ executor-base.md（执行基础 - 320 行）
       ├→ executor-{style}.md（风格特定 - 125~223 行，只读一个）
       ├→ shared-standards.md（技术约束 - 697 行）
       ├→ image-generator.md（图片 - 503 行，条件读取）
       └→ canvas-formats.md（画布 - 73 行，需要时读取）
```

### 为什么有效

1. **降低单次上下文负担**：Agent 不需要一次性读入 2,900 行——它只读取当前角色需要的文件。生成封面页时不需要读图片生成器的 503 行
2. **按需加载**：`image-generator.md` 只在用户选择"AI 生成图片"时才读取；`verify-charts.md` 只在有图表页时才读取
3. **避免冲突**：三种 Executor 风格（general / consultant / consultant-top）互斥，只读一种，避免了相互矛盾的指令

### 普适用法

```
将 Prompt 分为三层：
1. 入口层（必读）：流程定义 + 全局铁律
2. 角色层（按需读）：当前角色的行为规范
3. 参考层（查阅用）：技术规范、模板目录
入口层 < 400 行，角色层 < 500 行，参考层按需加载。
```

---

## 十四、技巧 14：强制串行 + 反并行声明

### 做法

显式禁止 Agent 的"并行优化"倾向：

```markdown
> Run the three sub-steps **one at a time** — each must complete
> successfully before the next.
>
> ❌ **NEVER** combine them into a single code block or shell invocation.
```

```markdown
> SVG pages MUST be generated sequentially page by page in one continuous
> pass. Grouped page batches (for example, 5 pages at a time) are FORBIDDEN.
```

```markdown
> Execute only one generation command at a time; wait for file confirmation
> before the next.
```

### 为什么有效

1. **对抗 Agent 的"效率倾向"**：Agent 天然倾向于并行执行以提高效率——但在需要前后依赖的场景中，并行会导致上下文丢失
2. **❌ 符号的警示作用**：红色 X 标记 + `NEVER` 大写让这条规则无法被忽视
3. **给出具体的违规示例**：`"for example, 5 pages at a time"` —— 告诉 Agent 什么样的行为算违规

### 普适用法

```
在必须串行的环节，用三种手段同时约束：
1. 正向："必须逐个执行"
2. 负向："禁止批量/合并"
3. 示例："例如 5 个一批是违规的"
```

---

## 十五、技巧 15：一致性锚点（Deck Style Anchor）

### 做法

在需要生成多个相关输出时，定义一个**共享锚点**作为每个输出的前缀：

```markdown
**Deck Style Anchor**: A 15-25 word shared prefix prepended to every image
prompt in a deck. Example:

"Minimalist corporate illustration, navy and white color scheme, clean
geometric shapes, professional and modern, flat design"

This anchor ensures all generated images for one deck are visually coherent.
```

### 为什么有效

1. **共享前缀 > 独立描述**：如果每张图片独立描述，AI 图片生成器会产出风格迥异的图片。共享前缀确保所有图片在风格上对齐
2. **一次定义，多次引用**：锚点只需在策略师阶段定义一次，后续每张图片的 Prompt 自动继承
3. **可审计**：可以检查每张图片的 Prompt 是否包含锚点

### 普适用法

```
当 Agent 需要生成多个风格一致的输出时：
1. 在流程早期定义一个共享"风格锚点"（一段固定描述）
2. 要求每个输出必须以锚点开头
3. 锚点写入锁定文件，确保跨步骤一致
```

---

## 十六、技巧 16：范围守卫 — 显式声明规则的适用边界

### 做法

不仅定义规则，还**显式声明规则不适用的情况**：

```markdown
> This spec applies to side-by-side intent only. Other intents (hero /
> full-bleed, atmosphere / background, accent / inline) use full-bleed
> placement where ratio alignment is not a constraint -- the ratio/split
> table below does NOT apply.
```

```markdown
> **When to use shadow**: Only when the element genuinely floats above another
> layer.
>
> **When NOT to use shadow**:
> - Equal peer cards in a 2/3/4-up grid — keep all flat
> - Pages with only one content container — no second layer to lift above
> - Dark backgrounds — black shadows vanish
```

### 为什么有效

1. **防止规则过度泛化**：Agent 倾向于将规则应用到所有场景——范围守卫阻止了"因为规则说要加阴影，所以每页都加阴影"
2. **反例比正例更有效**：告诉 Agent "不要在这些场景使用"比"在这些场景使用"更容易遵守
3. **减少"灰色地带"**：显式列出适用/不适用的场景，消除了 Agent 的"大概适用"判断

### 普适用法

```
每条规则都附带：
1. 适用条件（When to use）
2. 不适用条件（When NOT to use）
3. 不适用时的替代方案
```

---

## 十七、技巧 17：格式化完成确认 — 结构化输出模板

### 做法

每个阶段完成时，Agent 必须输出**固定格式的确认信息**：

```markdown
## ✅ Executor Phase Complete
- [x] All SVGs generated to svg_output/
- [x] svg_quality_checker.py passed (0 errors)
- [x] Speaker notes generated at notes/total.md
```

```markdown
## ✅ Image_Generator Phase Complete
- [x] Prompt document created
- [x] Each image: status is either `Generated` or `Needs-Manual`
- [x] No row remains `Pending`
```

### 为什么有效

1. **结构化输出 > 自由叙述**：固定格式让 Agent 无法含糊地说"大概完成了"，必须逐项确认
2. **自然形成流程日志**：这些确认信息串联起来就是完整的执行日志，便于回溯问题
3. **"0 errors" / "No row remains Pending"**：这些是**可量化**的完成标准——不能有歧义

### 普适用法

```
为每个阶段定义固定的完成确认模板：
- 使用 - [x] 格式的清单
- 包含量化标准（"0 errors", "No X remains Y"）
- 指明下一步操作
```

---

## 十八、总结：18 条技巧速查表

| # | 技巧 | 解决的问题 | 核心做法 |
|---|------|-----------|---------|
| 1 | 铁律前置 | 规则被遗忘 | 最高优先级标记放在文件最开头 |
| 2 | GATE/Checkpoint 链 | 跳步 | 每步定义前置条件和完成确认 |
| 3 | 外置记忆体 (spec_lock) | 上下文漂移 | 关键参数写入短文件，每步强制重读 |
| 4 | 禁用清单 + 替代方案 | 格式错误 | 正反对照表格 |
| 5 | 审计追踪 | 编造 | 要求提供不可伪造的原文引用 |
| 6 | 决策树 | 选择困难 | 将多维度判断分解为二叉选择 |
| 7 | 参数化约束 | 固定值不通用 | 锚定基线的比例区间 |
| 8 | 负向约束 > 正向指令 | Agent "多此一举" | ❌ NEVER / FORBIDDEN / Do NOT |
| 9 | 受控词汇 + 白名单 | Agent "发明"新值 | 限制允许值列表，禁止列表外值 |
| 10 | 有限重试 + 优雅降级 | 失败时死循环 | 重试 N 次后标记为需人工 |
| 11 | 确定性路径选择 | Agent 自作主张 | 精确定义触发条件，禁止主观判断 |
| 12 | 阶段自检清单 | 质量遗漏 | 分类清单逐项自查 |
| 13 | 分层 Prompt 架构 | 上下文过载 | 按职责分离文件，按需读取 |
| 14 | 强制串行声明 | Agent 并行优化 | 三重约束（正向+负向+示例） |
| 15 | 一致性锚点 | 多输出不一致 | 共享前缀确保风格对齐 |
| 16 | 范围守卫 | 规则过度泛化 | 显式声明适用/不适用边界 |
| 17 | 格式化完成确认 | 模糊完成 | 固定模板 + 量化标准 |

---

## 十九、设计哲学

这些技巧的背后是同一个核心哲学：

> **不信任 Agent 的记忆、判断和诚实度，但充分利用它的推理和创造力。**

- 不信任记忆 → 外置记忆体 + 强制重读
- 不信任判断 → 决策树 + 受控词汇 + 确定性触发
- 不信任诚实 → 审计追踪 + 格式化确认 + 量化标准
- 利用推理 → 参数化约束 + 分层架构 + 优雅降级
- 利用创造力 → 角色切换 + 比例区间 + 风格锚点

这套 Prompt 不是在"命令"AI，而是在**设计一个让 AI 不容易犯错的执行环境**——就像好的 API 设计不是强迫用户正确使用，而是让错误用法变得不可能。
