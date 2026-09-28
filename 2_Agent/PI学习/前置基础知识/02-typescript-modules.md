# 模块系统：import / export 与 package

TS 的模块语法就是 ES Modules（ESM）。本章解决读源码时最先撞上的问题：import 的各种写法、为什么路径写 `.js`、为什么同一个仓库里既有 `import` 又有 `require`，以及 `import "@scope/pi-ai"` 是怎么找到代码的。包的构建与发布细节在第 10 章，此处只建认知。

## 1. 一个文件就是一个模块

模块边界是文件：每个 `.ts` 文件天然是独立模块，顶层作用域私有，只有 export 的名字对外可见。

```ts
// src/tools/fs.ts —— 顶层作用域即模块私有作用域
const MAX_SIZE = 1024 * 1024;             // 未 export：模块私有
export function readTool() { /* ... */ }  // named export：对外可见
```

对比：

- Java：package 是命名空间 + classpath 定位，同包内类互相可见（还有 package-private 这档）。
- Python：module = 一个 `.py` 文件，这点和 Node 最像；package 是带 `__init__.py` 的目录。
- Node 差异："同目录"没有任何特殊地位，不 import 就是不可见；可见性只有 export 与不 export 两档。

```
   fs.ts（模块）                      agent.ts（另一个模块）
┌────────────────────────┐          ┌──────────────────────────┐
│ MAX_SIZE   （私有）     │          │ import { readTool }      │
│ readTool() （export）───┼────────▶ │   from "./fs.js"         │
└────────────────────────┘          └──────────────────────────┘
     模块间唯一通道：显式 import / export
```

## 2. import 的四种形态与 named/default 之争

```ts
import { clamp } from "./math.js";    // named：按名导入
import * as math from "./math.js";    // namespace：全部收进一个对象（≈ import module as）
import Calc from "./math.js";         // default：名字随意起
import "./polyfills.js";              // side-effect：只执行模块副作用，不取绑定
```

导出侧对应两种：

```ts
// math.ts
export function clamp(v: number) { /* ... */ }   // named export：可有任意多个
export default class Calculator {}               // default export：每个文件最多一个
```

named import 的名字必须与导出一致，编译器和 Node ESM 运行时都会校验；default import 的名字是纯本地变量：

```ts
import Calc from "./math.js";       // 合法
import Whatever from "./math.js";   // 也合法——同一个人两处用不同名字，没人管
import { clamp as limit } from "./math.js";          // named 也可重命名，但显式且可 grep
import Agent, { type AgentConfig } from "./agent.js"; // default + named + type 混合语法
```

default import 的改名陷阱正是现代项目约定"只用 named export"的直接原因：命名不可校验，搜索、重构、review 都困难，IDE 重命名追不进字符串。default export 只在老代码和个别框架约定（如页面组件）里常见，认得即可。

## 3. re-export 与 barrel file

```ts
export { readTool } from "./tools/fs.js";   // 转手导出，本模块不引入绑定
export * from "./tools/net.js";             // 全量转发（命名冲突会被静默忽略，慎用）
```

常见做法是聚合出一个 `index.ts`（barrel file），让使用方一处导入：

```ts
// tools/index.ts
export * from "./fs.js";
export * from "./net.js";

// 使用方
import { readTool, netTool } from "./tools/index.js";
```

读源码的成本：barrel 让"跳转定义"多跳一层——先落到 index.ts，再跳到真实文件；大型项目里 re-export 链还可能造成循环初始化问题，不少项目正在拆掉 barrel。看到 import 路径以目录（index）结尾 → 中间必有 barrel 在聚合。

## 4. type-only import：import type

```ts
import type { Tool, ToolResult } from "./tool.js";   // 整行只含类型
import { type Tool, runTool } from "./tool.js";      // 混合导入：单个名字标记为 type
```

为什么需要：类型擦除后，这些名字在运行产物里不存在，对应的 import 必须被完整删除。能做全程序分析的编译器会自动删除"只用作类型"的普通 import；但单文件转译器（esbuild/swc、isolatedModules 模式）不做跨文件分析，无法判断，留下的导入在 Node ESM 下会被链接期校验直接拒绝：

```ts
// tool.ts 运行时只真的导出了函数 run；Tool 是纯类型
export interface Tool { name: string }
export function run(t: Tool) { /* ... */ }

// 被 esbuild 转译后如果保留：
import { Tool } from "./tool.js";
// Error: The requested module './tool.js' does not provide an export named 'Tool'

// 正确写法：类型走 import type，值走普通 import
import type { Tool } from "./tool.js";
import { run } from "./tool.js";
```

`import type` 把"这行可安全删除"显式写进语法。规则一句话：名字只出现在类型位置，就用 import type。`verbatimModuleSyntax` 是强制区分两者的编译开关【看懂即可】。

## 5. dynamic import【看懂即可】

```ts
// 顶层 import：模块加载时就执行依赖，无论后面用不用
import { buildReport } from "./report.js";

// dynamic import：运行到这行才加载，返回 Promise
async function browser() {
  const { chromium } = await import("playwright-core");  // 真要跑浏览器时才加载
}
```

CLI 子命令按需装载是 Coding Agent 项目里的标准手法，重依赖只在实际执行该命令时加载，显著加快 `--help` 与常用路径的启动：

```ts
const commands: Record<string, () => Promise<void>> = {
  run:     async () => (await import("./cmd/run.js")).run(),
  browser: async () => (await import("./cmd/browser.js")).browser(),
};
```

其他用途：可选依赖（try/catch 包住 import，失败降级）、插件系统（运行时按名字装载）。与顶层 import 的本质区别是"声明即加载"与"运行到才加载"。它返回 Promise 的调度机制在第 04 章，此处认语法即可。

## 6. 说明符的三种形态

import 后面那个字符串叫说明符（specifier），先分清种类，才知道走哪套解析规则：

```ts
import { Tool } from "./tool.js";       // 相对说明符：仓库内文件，必须带扩展名（下一节）
import { Tool } from "@scope/pi-ai";    // 裸说明符：包名，走 node_modules 解析（第 8 节）
import fs from "node:fs";               // node: 前缀：Node 内置模块，优先级最高
```

【看懂即可】绝对路径/URL 说明符与 package.json 里的 `#` 子路径导入（imports 字段），知道存在即可，遇到再查。

## 7.【必须掌握】为什么源码是 .ts，import 却写 .js

```ts
// src/agent/session.ts
import { Tool } from "./tool.js";   // 磁盘上的文件是 tool.ts！
```

三个事实拼出答案：

1. ESM 规范要求相对导入必须带扩展名；不带扩展名的"裸说明符"按包名走另一套解析（第 6 节）。
2. tsc 编译不重写说明符：只删类型，import 路径原样进入产物 JS。
3. 产物目录里 `session.js` 旁边躺着的正是编译出来的 `tool.js`——路径在产物中是对的。

所以结论是：import 写的是编译产物的路径，不是源码路径。`.js` 后缀指向 `.ts` 源文件是所有 ESM 风格 TS 项目的标准形态，不是笔误。【暂时跳过】新编译选项 `allowImportingTsExtensions` / `rewriteRelativeImportExtensions` 允许直接写 `.ts`，知道存在即可。

## 8.【必须掌握】ESM 与 CJS 并存

读源码会同时遇到两套模块语法，它们是两个时代的标准：

```js
// CommonJS（CJS，Node 传统）        // ECMAScript Module（ESM，语言标准）
const fs = require("node:fs");       import fs from "node:fs";
exports.run = run;                   export const run = ...;
module.exports = { run };            export default run;
```

判断一个文件属于哪套（完整决策流程见第 10 章）：`.mjs` / `.cjs` 扩展名最优先；其余看最近一层 package.json 的 `"type"` 字段——`"module"` 按 ESM 解析，缺省按 CJS。

混用规则要点（详见第 10 章，此处建认知）：

- ESM 文件里没有 `__dirname`、`__filename`、`require`、`module.exports`——它们是 CJS 模块包装器注入的变量，ESM 没有这套包装。
- ESM 等价物要自己构造，源码里常见这两段：

```ts
// ESM 中派生 __dirname 的标准写法
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
const here = dirname(fileURLToPath(import.meta.url));

// ESM 中需要 require（加载 CJS 配置文件等）
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
```

- CJS 里 `require()` 一个 ESM 模块长期不可行（ESM 允许顶层 await，无法同步返回）；Node 新版本正在放开，知道即可。
- `import` 是静态结构，可静态分析（tree-shaking 只对 ESM 有效）；`require` 是普通函数调用，动态且同步。

## 9. 包的入口：为什么 import "@scope/pi-ai" 能找到代码

```
import { Tool } from "@scope/pi-ai"
        │  裸说明符：无路径、无扩展名
        ▼
1. 从当前文件所在目录逐级向上查找 node_modules/@scope/pi-ai
   ./node_modules ✗ → ../node_modules ✗ → ../../node_modules ✓
2. 读 node_modules/@scope/pi-ai/package.json
3. exports["."] 指向产物文件；老包没有 exports 时看 main 字段
4. Node 按上一节规则以 ESM/CJS 加载该文件
```

真实的 exports 长这样：

```json
{
  "name": "@scope/pi-ai",
  "type": "module",
  "exports": {
    ".": { "import": "./dist/index.js", "require": "./dist/index.cjs" },
    "./providers": "./dist/providers/index.js"
  }
}
```

`"."` 是包根入口；条件键 `import`/`require` 分别服务 ESM 与 CJS 两种消费方；子路径 `"./providers"` 显式开放，未列出的深路径（如 `@scope/pi-ai/dist/internal`）会被拒绝。解析优先级一句话：`node:` 内置模块 → 相对/绝对路径说明符 → 逐级向上的 node_modules。深讲在第 10 章。

## 10. 对照 Java 与 Python

```
              Java                  Python                Node/TS
定位单位       class（全限定类名）    module（.py 文件）      文件 + package.json
查找机制       classpath + jar       sys.path 顺序查找       node_modules 逐级向上
版本解析       全局一份（Maven 调解）  venv 内一份            每棵依赖树可各有副本
说明符形态     org.acme.Foo          org.acme.foo           URL 风格：./x.js、pkg、node:x
```

- Java：classpath + Maven 坐标，同一 `groupId:artifactId` 在一个 classloader 里只有一份；类型与 jar 绑定，编译期解析到底。
- Python：`sys.path` 顺序查找 site-packages，一个虚拟环境一份依赖，运行时可改 path。
- Node：每个包从使用处逐级向上找 node_modules，不同子树可并存同一依赖的不同版本（这解释了 node_modules 的巨大体积与扁平 + 嵌套混合结构）。

对读源码的直接影响：看到 import 先分清相对路径（仓库内代码）还是裸包名（外部依赖，去 node_modules 或 package.json 确认）；排查"找不到模块"时，沿目录逐级向上走一遍就是 Node 的查找过程本身。

## 本章只记住这 5 件事

- 一文件一模块；模块私有 = 未 export，没有 Java 式的可见性层级。
- 现代项目只用 named export：default import 名字随意且不可校验，是维护性陷阱。
- 名字只出现在类型位置就用 `import type`：擦除后不能留下运行时导入。
- 相对导入写 `.js` 写的是编译产物路径；ESM 规范要求 + tsc 不重写说明符，不是笔误。
- ESM/CJS 靠 package.json `"type"` 与 `.mjs`/`.cjs` 判断；ESM 里没有 `__dirname`/`require`。
- 裸包名解析 = 逐级向上找 node_modules + package.json 的 exports/main。

## 源码识别

- 看到 `import { x } from "./foo.js"` 而磁盘上是 foo.ts → ESM 风格 TS 项目，写的是产物路径
- 看到 `import type { … }` → 这些名字只用于类型，编译后整行消失
- 看到 `require(` / `module.exports` → CJS 文件（构建脚本、遗留代码）
- 看到 `import.meta.url` / `createRequire` → ESM 里补 `__dirname`/`require` 的等价物
- 看到 `export * from "./xxx.js"` 的 index.ts → barrel，跳转定义会多一跳
- 看到 `export default` → 老式或框架约定代码，import 侧名字可能是任意的
- 看到 `"type": "module"` → 该包内 `.js` 文件按 ESM 解析
- 看到 `await import("…")` → 按需加载（启动加速/插件），返回 Promise
- 看到 `import fs from "node:fs"` → Node 内置模块，不走 node_modules

## Java/Python 工程师常见误区

- 错误认知：import 路径写错了（.ts 文件写成 .js）→ 那是 ESM 标准形态，写的是编译产物路径。
- 错误认知：default export 是主要的导出方式 → 现代约定只用 named export，default 是改名陷阱来源。
- 错误认知：模块像 Java package 一样有可见性层级 → 只有 export 与不 export 两档。
- 错误认知：`import type` 只是风格偏好 → 它承担"擦除后不能留下运行时导入"的正确性职责。
- 错误认知：依赖像 Maven 一样全局一份 → node_modules 逐级向上解析，可多版本并存。
- 错误认知：`require` 和 `import` 可以随意互换 → 分属 CJS/ESM 两套体系，混用有硬性规则限制。

## 是否值得深入

- named/default export 与 re-export/barrel：当前阶段：建议掌握——读任何文件的第一眼。
- import type 与 verbatimModuleSyntax：当前阶段：建议掌握——改动含类型导入的文件时必用。
- `.js` 扩展名规则与说明符种类：当前阶段：建议掌握——新建文件第一次写 import 就会遇到。
- ESM/CJS 互操作细节（createRequire、顶层 await、双格式包发布）：当前阶段：不需要深入，第 10 章打包与发布时再学。
- package.json exports 子路径映射与条件导出：当前阶段：不需要深入，能定位包入口即可，深讲在第 10 章。
- dynamic import 与懒加载策略：当前阶段：不需要深入，认出用途与场景即可。
