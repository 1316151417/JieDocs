# 构建与工具链：tsc / tsx / esbuild 到底谁干什么

Java 的世界是一条固定流水线：javac 负责检查加编译，Maven 负责打包，看 pom.xml 就知道每一步谁干。TS/Node 生态把这条流水线拆成了独立步骤，每一步都有多个工具可选，没有一个工具全干。后果是：拿到一个项目，看不懂 package.json scripts 里 tsc / tsx / esbuild / vitest 各自站在哪一环，就说不清"源码怎么变成跑起来的进程"。本章用一张阶段图把工具各就各位，之后任何 scripts 都能逐行对号入座。

## 13.1 阶段图：转译 ≠ 类型检查【必须掌握】

```
源码 .ts
   ↓ 类型检查（不产出 JS）      ← tsc --noEmit / tsgo
   ↓ transpile 转译（剥类型，产出 .js，不检查类型） ← esbuild / tsx / swc
   ↓ bundle 打包（多文件合一，可选）  ← esbuild / rollup 等
   ↓
Node.js 运行
```

这张图是全章骨架，先记三个事实：

1. **类型检查与转译是两个独立步骤**。检查只读源码、只报错，不产出任何 JS；转译只把类型语法剥掉、产出 JS，完全不检查类型。
2. **承担者不同**。检查只有 tsc（及其原生移植 tsgo，编辑器里的 tsserver 同引擎）；转译谁都能干——esbuild、tsx、swc、Node 内置 type stripping。
3. **打包是可选步骤**。服务端代码常常只转译不打包；CLI 工具与 agent 前端偏好打成单文件分发。

"转译 ≠ 检查"最具体的形态，就是"tsx 能跑，CI 却挂"：

```ts
const count: number = "not a number"; // 类型错误
```

这行代码 `tsx src/main.ts` 照常运行——转译后它就是 `const count = "not a number"`，类型标注被剥掉，运行时毫无异常；CI 里的 `tsc --noEmit` 才会报错。Java 里这个现象不可能存在：javac 编译即检查，过不了检查就没有 .class，更没有运行。Python 的形态反而更接近：解释器从不检查类型，mypy 是完全旁路的一步。准确说：TS 生态 = Python 的"运行与检查分离"模型 + 事实上强制执行的官方检查器（编辑器实时标红 + CI 门禁）。

| 生态 | 类型检查 | 产出可运行代码 | 两步关系 |
|---|---|---|---|
| Java | javac（同一步） | javac | 编译即检查，一体不可拆 |
| Python | mypy（可选旁路） | 解释器（原生跑 .py） | 完全分离，检查可选 |
| TS/Node | tsc --noEmit / tsgo | esbuild / tsx / swc / Node strip | 分离，但检查事实上强制 |

阶段图是概念全集，具体工作流只执行子集：

| 工作流 | 执行的阶段 | 典型命令 |
|---|---|---|
| dev 循环 | 转译（内存中）+ 运行 | `tsx watch src/main.ts` |
| CI 检查 | 类型检查 + lint + test | `tsc --noEmit && biome check . && vitest --run` |
| 发布 | 全量编译产 dist/（或再 bundle） | `tsc -p tsconfig.build.json`，或 esbuild 打单文件 |

为什么生态会拆成这样——知道动机，一堆工具名就好记了：

- **转译是机械活**：剥类型不需要理解程序语义，可以并行、可以做到极快——esbuild / swc 用原生语言（Go / Rust）把它推到了极致。
- **检查是全局活**：判断一个表达式类型可能要用到另一个文件的定义，需要全程序信息——快不起来，也不需要快（只在保存与 CI 时跑）。
- **dev 循环只要"跑起来"，不需要"证明正确"**——所以 tsx 只做转译；正确性交给编辑器（实时反馈）与 CI（最终门禁）。

## 13.2 tsc 与 tsgo：官方编译器【必须掌握】

tsc 是 TS 官方编译器，身兼两职，配置就是 tsconfig.json（第 01 章有一句话认知）：

- **全量编译**：读 tsconfig，把每个 .ts 编译成 .js（发库时还要产出 .d.ts 类型声明），落进 outDir（通常 dist/）。这一模式 = 检查 + 转译一体，最像 javac。发 npm 库必须走它（消费者要 .d.ts）；无 bundler 的服务端项目也用它，产物目录结构与源码一一对应。
- **只检查**：`tsc --noEmit`（或 tsconfig 里直接写 `"noEmit": true`）只做类型检查，不产出任何文件。现代项目把它当独立质量门，跑在 CI 和编辑器里；转译交给更快的工具。

读源码要知道的一个后果（第 02 章讲过）：tsc 只删类型、不重写 import 说明符，所以 ESM 相对导入要写 `.js` 后缀——写的是产物路径，不是笔误。

顺带回答"编辑器里的红线是谁给的"：不是 tsc 命令在跑，而是同引擎的语言服务 tsserver（LSP 实现），增量分析你打开的文件及其依赖图。所以"IDE 没报错"与"CI 的 `tsc --noEmit` 通过"不等价——前者只查你碰过的部分，后者是全量。这解释了一个日常现象：本地看着干净，push 之后 CI 红。

tsc 的痛点是慢：全项目类型推断，大 monorepo 上分钟级。两个衍生现象都源于此：

- **tsgo**【看懂即可】：TypeScript 团队用 Go 重写的原生移植版，检查语义对齐 tsc，速度快约一个数量级，命令行直接替换。scripts 里看到 `tsgo --noEmit` 读作"更快的 tsc"；也有项目用 `tsgo -p tsconfig.build.json` 做全量编译产出。
- 加速手段（incremental 缓存、project references）【暂时跳过】，知道存在即可，需要时再查。

## 13.3 tsx：开发期运行器【必须掌握】

tsx 解决 dev 循环的问题：改完代码立刻看效果，不想先跑一遍编译。`tsx src/main.ts` 的实际流程：

```
tsx 命令
  → 内部调 esbuild，逐文件在内存中剥类型（转译阶段，不做检查）
  → 转译结果交给 Node 执行
```

三条要点：

- **不做类型检查**。开发期的类型反馈来自编辑器（tsserver 实时标红），CI 里的 `tsc --noEmit` 兜底。tsx 跑通只说明"语法可剥、运行时没炸"，不代表类型正确——见 13.1 的那行坏代码。
- `tsx watch src/main.ts` 监听变更自动重启，定位约等于 spring-boot devtools 的热重载。
- 对照 Python：`python main.py` 直接跑 + mypy 旁路 ≈ `tsx main.ts` + tsc 旁路。差异是 Python 跑的就是源码本身，tsx 每次执行都先过一道转译——只是 esbuild 快到无感。

看到 scripts.dev 是 tsx，就知道该项目开发期不产出 dist/，构建另有命令。

## 13.4 esbuild：转译器 + 打包器【必须掌握】

esbuild 是 Go 写的转译器兼打包器，快的根源：并行编译 + 完全不做类型检查。两种用法对应阶段图的两层：

- **transform（转译）**：单文件剥类型，等价于"极速版 tsc 转译"。tsx 内部就是它；vitest 转译测试文件也是它。
- **bundle（打包）**：从 entry（入口文件）出发，沿 import 语句递归走完整个模块图——包括 node_modules 里的依赖——合成一个 .js 文件。

bundle 的最近对应物是 Maven shade：shade 把依赖 jar 合进一个 uber-jar，esbuild 把模块图合成一个 .js，产物运行时不再需要 node_modules。CLI 工具与 agent 前端偏好 bundle 的理由：单文件分发（`npm i -g` 装得快）、冷启动不用解析几百个模块文件。项目里的 bundle 脚本核心就这几行，见到能认出即可：

```ts
import { build } from "esbuild";

await build({
  entryPoints: ["src/cli.ts"], // 入口：沿 import 图递归走
  bundle: true,                // 打包：依赖一起合入
  platform: "node",            // 目标是 Node，不是浏览器
  format: "esm",
  outfile: "dist/cli.mjs",     // 单文件产物
  external: ["sharp"],         // 含原生二进制的包打不进去，声明为外部依赖
});
```

代价一句话：动态 require、运行时拼路径加载无法静态分析，bundle 会漏——发布产物缺模块时再查。

服务端常驻进程则常常只转译不打包：`dist/` 镜像 `src/` 结构，跑 `node dist/main.js`。看 scripts.build 属于哪种形态，就知道产物是单文件还是目录树。

## 13.5 Node 原生跑 TS：type stripping【看懂即可】

Node 22.6 引入类型剥离（需 `--experimental-strip-types`，23.6 起默认开启）：`node src/main.ts` 直接执行 .ts，原理与 tsx 同类——只删类型、零检查，只是内建在 runtime 里。它有一条硬约束：只支持**可擦除语法**（erasable-only）——enum、parameter properties、namespace 这类"需要编译器生成额外运行时代码"的语法一律拒绝。这正是部分现代项目在规范里禁用 enum 的工程理由（第 01 章从建模角度给出的理由是字面量 union 更好用）。知道存在即可，需要时再查。

## 13.6 lint 与 format：eslint / prettier / biome【看懂即可】

两个正交职责，先分清再认工具：

- **lint 找问题代码**：未用变量、`any` 滥用、裸调 async 函数不接错误（no-floating-promises，直击第 04 章的 fire-and-forget 坑）。
- **format 统一风格**：缩进、引号、分号、换行，纯文本形态，不碰语义。

| 生态 | lint | format |
|---|---|---|
| Java | Checkstyle | Spotless |
| Python 传统 | flake8 / pylint | black |
| Python 现代 | ruff（Rust 重写，检查+格式一体） | ruff format |
| JS/TS 传统 | eslint | prettier |
| JS/TS 现代 | biome（Rust 写，lint+format 一体） | biome format |

ruff 之于 flake8+black ≈ biome 之于 eslint+prettier：一个二进制、一份配置、一个命令干两件事。读项目只需要认得出：`biome check .` 是 lint+format 检查（`--write` 顺带修复），配置文件 biome.json / eslint.config.\* / .prettierrc 的存在告诉你项目用哪套。lint/format 与类型检查互不替代，所以质量门常写成串联：`tsc --noEmit && biome check .`。

## 13.7 读 package.json scripts 定位管线【必须掌握】

真实风格的 scripts 段（取材自 monorepo 型 coding agent 项目）：

```json
{
  "scripts": {
    "dev": "tsx watch src/main.ts",
    "build": "tsgo -p tsconfig.build.json",
    "bundle": "node scripts/build-bundle.mjs",
    "check": "tsgo --noEmit && biome check .",
    "test": "vitest --run"
  }
}
```

逐行对号入座：

| script | 命令 | 处于哪个阶段 | 产出 |
|---|---|---|---|
| dev | `tsx watch src/main.ts` | 转译（内存中）+ 运行 | 无产物，dev 循环 |
| build | `tsgo -p tsconfig.build.json` | 检查 + 全量转译 | dist/ 目录树 + .d.ts |
| bundle | esbuild 构建脚本 | 转译 + 打包 | 单文件发布产物 |
| check | `tsgo --noEmit` + `biome check .` | 类型检查 + lint/format 检查 | 无产物，只报错 |
| test | `vitest --run` | 测试（自带转译管线） | 测试报告 |

两个容易误判的点：

- **vitest 不做类型检查**。它内置 esbuild 转译，测试文件不经 tsc 产出也能跑——"测试全绿"不代表"类型正确"，所以 check 与 test 是两道独立的门。
- `&&` 串联即 shell 语义：前者失败后者不跑。check 把 `--noEmit` 放在最前，含义是类型错误优先于风格问题暴露。

拿到陌生项目的 30 秒流程：看 `dev` 知道开发循环形态（tsx / node --watch / 直跑 dist）；看 `build` 知道产物形态（目录树 / 单文件 bundle）；看 `check` 知道质量门构成；看 `test` 知道测试框架。monorepo 里这套通常每个 package 各有一份，再由根 scripts 聚合编排（第 12 章）。

## 本章只记住这 5 件事

1. 转译 ≠ 类型检查：esbuild / tsx / swc 只剥类型不检查；类型检查是独立步骤，只有 tsc / tsgo（及编辑器的 tsserver）承担。
2. "代码跑得起来、CI 却挂了"的永久解释就是上一条——tsx 跑通只证明语法可剥、运行时没炸。
3. tsc 两种模式：全量编译产 dist/ + .d.ts（发库、javac 同构的一体模式）；`--noEmit` 纯检查（现代质量门）。tsgo 是官方原生移植，快一个数量级，可替换。
4. bundle ≈ Maven shade：沿 import 图把含 node_modules 依赖的模块合成单文件；服务端常只转译不打包。
5. lint（找问题）与 format（统一风格）正交；biome = Rust 一体化工具，eslint + prettier = 传统组合——ruff 之于 flake8+black 就是 biome 之于 eslint+prettier。
6. 读 scripts 先问命令处于哪个阶段：dev = 转译 + 运行、build = 产出、check = 检查门、test = vitest 自带转译且不做类型检查。
7. Node 原生 type stripping 只剥类型且要求可擦除语法——现代项目禁用 enum / parameter properties 的工程理由。

## 源码识别

- 看到 `tsc --noEmit` / `tsgo --noEmit` → 纯类型检查步骤，不产出任何 JS。
- 看到 scripts.dev 里的 `tsx`（尤其 `tsx watch`）→ 开发期内存转译直跑，无 dist 产物。
- 看到 `-p tsconfig.build.json` → 全量编译产 dist，通常伴随 .d.ts。
- 看到 tsconfig 里 `"noEmit": true` → 这份配置只服务检查，不发产物。
- 看到 esbuild 脚本 / `bundle: true` → 模块图合成单文件的发布产物。
- 看到 `biome check .`（含 `--write`）→ lint + format 一体化检查（修复）；配 biome.json 而非 .prettierrc 说明项目用一体化工具。
- 看到 `vitest --run` → CI 单次跑测试；默认不含类型检查。
- 看到 scripts 里 `&&` 串联的 check → 多道质量门的执行顺序与短路语义。

## Java/Python 工程师常见误区

- 错误认知："esbuild / tsx 是新一代编译器，产出类型安全的代码" → 它们不检查类型；类型安全完全取决于 `tsc --noEmit` 这一步有没有跑。
- 错误认知："像 javac 一样，能运行的 TS 就是类型正确的 TS" → 运行与检查分离，类型错误的代码能一路跑到底。
- 错误认知："esbuild 会取代 tsc" → 职责不同：esbuild 接管转译与打包，类型检查只能 tsc / tsgo；现代项目两者共存各干一段。
- 错误认知："build 就是打包成单文件" → 服务端项目常只转译成 dist 目录树；bundle 是 CLI 分发偏好，不是通用要求。
- 错误认知："lint 报错约等于类型错误" → lint、format、类型检查三个正交维度，各有各的工具与门槛。
- 错误认知："测试通过说明编译没问题" → vitest 用 esbuild 转译后直接跑，不做类型检查。

## 是否值得深入

- 阶段图与 scripts 判读：当前阶段：建议掌握 —— 读任何 Node 项目的第一步。
- tsc / tsgo 双模式与 tsconfig 常见字段：当前阶段：建议掌握 —— 改构建配置前的最低配置量。
- tsconfig 全量编译选项（paths / baseUrl / project references…）：当前阶段：不需要深入 —— 读懂项目现有配置即可，要加构建需求时再查。
- esbuild 插件机制与各 bundler 对比（rollup / tsup / bundler 特性矩阵）：当前阶段：不需要深入 —— 改构建脚本时再查。
- tsgo / swc / oxc 等原生工具的内部实现：当前阶段：不需要深入 —— 知道定位与速度量级即可。
- Node type stripping 的版本矩阵与 transform 类 flag：当前阶段：不需要深入 —— 知道存在即可，需要时再查。
