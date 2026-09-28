# Monorepo 与 npm workspaces（重点章）

## 为什么 monorepo

一个 coding agent 通常要拆成多个包：`ai`（模型/provider 抽象、消息类型）、`agent`（agent 循环、工具框架）、`coding-agent`（CLI、编辑器集成、产品逻辑）。多仓库方案下你要面对：跨 repo 的 PR 无法原子合并（先发 pi-ai 再发 pi-agent，中间态不可用）、版本发布有时序地狱、各 repo 各自的 lock 导致依赖版本漂移。

monorepo 一次解决三件事：

- 多包共享代码：直接 import 兄弟包，无需发布中间版本。
- 原子跨包修改：一个 commit 同时改 packages/ai 和 packages/agent，CI 一起验证。
- 单一 lock 统一版本：整个 repo 一次依赖解析，zod 全 repo 一个版本。

对照你熟悉的体系：Maven 多模块 reactor（根 pom `packaging=pom` + `<modules>`）、Gradle 多项目（settings.gradle 的 include）、Python 的 uv/pdm workspaces。npm workspaces 是其中最"薄"的一层：只解决"本地包互链 + 统一安装"，不提供构建编排（并行、缓存、拓扑排序），那部分交给 turbo/nx（本章末尾一句话带过）。

同时明确 workspace 不做什么，防止过度期待：不做版本管理策略（跨包统一升版本要靠 changesets 之类工具）、不做发布编排（每个子包仍是独立的 npm publish）、不做构建缓存。它只回答一个问题："兄弟包之间的依赖解析到本地，而不是 registry"。

## workspace 结构【必须掌握】

```text
repo
├── package.json        ← 根：声明 "workspaces": ["packages/*"]，放共享 devDeps 和总 scripts
├── package-lock.json   ← 整个 repo 一份
└── packages
    ├── ai
    │   └── package.json    ← name: "@earendil/pi-ai"
    ├── agent
    │   └── package.json    ← dependencies: { "@earendil/pi-ai": "^0.12.0" }
    └── coding-agent
        └── package.json    ← dependencies: { "@earendil/pi-ai": "...", "@earendil/pi-agent": "..." }
```

根 package.json 的真实形状：

```json
{
  "name": "pi",
  "private": true,
  "workspaces": ["packages/*"],
  "scripts": {
    "build": "npm run build --workspaces",
    "test": "npm run test --workspaces",
    "check": "npm run check --workspaces"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vitest": "^2.1.0",
    "esbuild": "^0.24.0"
  }
}
```

- `workspaces` 是 glob 数组，npm install 在根目录跑一次，圈定的所有子包一起参与解析。
- 子包的 package.json 形状与第 10 章讲的完全一样——workspace 不引入新字段，只是多了"可以被兄弟包以名字引用"的身份。

packages/agent 的 package.json 真实形状（注意它与普通包唯一的区别：依赖的 `@earendil/pi-ai` 恰好是同 repo 的另一个包）：

```json
{
  "name": "@earendil/pi-agent",
  "version": "0.12.0",
  "type": "module",
  "exports": {
    ".": { "types": "./dist/index.d.ts", "import": "./dist/index.js" }
  },
  "scripts": {
    "build": "tsc -p tsconfig.build.json",
    "test": "vitest run"
  },
  "dependencies": {
    "@earendil/pi-ai": "^0.12.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0"
  }
}
```

## 为什么 `import { xxx } from "@earendil/pi-ai"` 能引用本仓库的包【必须掌握】

这段代码写在 packages/agent/src 里，看起来和引用外部包没有区别，而它确实引用的是隔壁目录的源码。解析顺序：

```text
import { Agent } from "@earendil/pi-ai"
  ↓ ① Node 模块解析：从当前文件目录向上逐级找 node_modules/@earendil/pi-ai
  ↓ ② 命中 repo/node_modules/@earendil/pi-ai —— 但它是个 symlink
  ↓ ③ symlink 指向 ../../packages/ai —— 实体就是本仓库源码
  ↓ ④ 按 packages/ai/package.json 的 exports/main 解析入口文件
```

symlink 是谁建的：npm install 扫描 workspace 时，发现 packages/agent 的 dependencies 声明 `@earendil/pi-ai: ^0.12.0`，而 workspace 内恰好有 name 为 `@earendil/pi-ai`、version 满足该范围的包——于是不去 registry 下载，改为在根 node_modules 创建 symlink 指向 packages/ai。

三个关键推论：

- 源码里 workspace 包和外部包的 import 写法完全一样，没有"本地路径 import"（你不该看到 `import ... from "../../ai/src"`，那是不理解 workspace 的写法）。
- 匹配靠 name + version，是真实匹配。workspace 包 version 是 0.12.0，依赖声明 `^0.12.0` 或 `*` 都能匹配；但如果声明 `^0.13.0` 匹配不上，npm 会把它当成普通外部依赖去 registry 解析——装到的是"上次发布的旧版本"而不是本地代码，且没有任何醒目警告。这是 monorepo 版本漂移的典型事故：改了本地 packages/ai，运行行为却没变。
- pnpm/yarn 提供 `workspace:` 协议显式声明（如 `workspace:^0.12.0`），匹配不上直接报错；npm 只靠裸 semver 隐式匹配。准确性上 workspace: 协议更严格，读 npm 项目时要自己在脑子里做这层校验。

另一个高频疑问：本地改了 packages/ai，packages/agent 那边要"重新安装"吗？不用。symlink 指向 packages/ai 本体，消费方按其 exports 解析到 `./dist`——所以改了 TS 源码要重新 build 生成 dist 才对消费方生效（有些仓库 exports 直接指向 src 省掉这一步）。不存在"install 本地包"这个步骤。

## 安装形态：symlink 树

`npm install` 在根目录跑完后的真实形态：

```text
repo/node_modules/
├── @earendil/
│   ├── pi-ai     -> ../../packages/ai        ← symlink（workspace 包）
│   └── pi-agent  -> ../../packages/agent     ← symlink（workspace 包）
├── zod/                                      ← 外部包，实体目录
└── commander/                                ← 外部包，实体目录
```

workspace 包自己的依赖（zod 等）不装在 packages/ai/node_modules 下，而是同样参与根的提升，落在根 node_modules 里。

自己验证一次（拿到任何 npm monorepo 都可以敲）：

```text
$ ls -l node_modules/@earendil/
pi-ai     -> ../../packages/ai
pi-agent  -> ../../packages/agent

$ readlink node_modules/@earendil/pi-ai
../../packages/ai
```

发布行为：`npm publish packages/agent` 时，dependencies 里的 `"@earendil/pi-ai": "^0.12.0"` 原样写进发布的包——因为 npm 中你声明的本来就是真实 semver 范围；pnpm/yarn 的 `workspace:^0.12.0` 则会在 publish 时被替换为当时的实际版本号。也就是说同一份依赖声明有两个生命周期：monorepo 内是"本地链接"，发布后是"registry 解析"，npm 靠的都是同一条声明。

## hoisting 在 monorepo 里放大 phantom dependency

所有子包的依赖默认提升到根 node_modules，于是每个子包的可 import 面 = 所有包依赖的并集。后果：

- packages/coding-agent 的源码 import packages/agent 的 devDependencies 里的 typescript、或 import packages/ai 的 dependencies 里的 zod，都能"跑"——即使 coding-agent 的 package.json 从未声明它们。
- phantom dependency（第 11 章）在 monorepo 里比单包项目普遍得多，因为提升基座是整个 repo 的并集。

严格项目的两种对策：lint 规则（dependency-cruiser、eslint-plugin-import 的 no-extraneous-import 等）校验"每个 import 必须在本包声明"；或改用 pnpm——默认严格隔离的 node_modules 结构，只有本包声明的依赖可解析。读源码时同样的纪律：import 了本包未声明的包，标记为 phantom，别当成正式依赖关系理解架构。

排查 monorepo 依赖问题的固定套路（按顺序敲）：

```bash
npm ls zod                    # zod 从依赖树哪条路径来、装了哪个版本
npm explain zod               # 多条路径时给出完整解释（谁需要它、为什么是这个版本）
readlink node_modules/@earendil/pi-ai   # 确认 workspace 链接指向本地而非 registry 旧版
```

三个命令分别回答：这个包是谁带来的 / 为什么是这个版本 / 这个 workspace 包是不是真的链接到本地。覆盖了 monorepo 日常九成的依赖疑问。

## 根 package.json vs 子 package.json 职责分工【必须掌握】

| 内容 | 根 package.json | 子 package.json |
|---|---|---|
| workspaces 声明 | 有 | 无 |
| private: true | 必有 | 视该包是否发布 |
| 共享工具链 devDeps（tsc/vitest/esbuild） | 放这里 | 可省（提升后子包内也能用） |
| 总控 scripts（全量 build/test） | 放这里 | 各自的 build/test |
| 运行时 dependencies | 不放 | 放这里，一包一份 |
| bin / exports / files / description | 无 | 有（对外发布的门面） |

判断口诀：根描述"这个 repo 怎么开发"，子包描述"这个包是什么、依赖什么、对外长什么样"。读项目时，想知道工具链看根，想知道架构分层看子包的 dependencies。

## --workspace 与 --workspaces 标志【必须掌握】

```bash
npm run build -w packages/agent          # 在指定子包跑 build（-w 是 --workspace 缩写）
npm run build -w @earendil/pi-agent      # 也可以用包名定位
npm run build --workspaces               # 所有子包依次跑 build
npm install zod -w packages/ai           # 给 ai 子包添加依赖（版本写入其 package.json，lock 在根更新）
npm ls --workspaces                      # 列出所有 workspace 包
```

- `-w` 接目录路径或包名，把命令的执行上下文切到那个子包（等价于 cd 进去再跑，但不需要真 cd）。
- `--workspaces` 全量执行：按 workspaces 声明的 glob 展开顺序依次跑，不感知依赖拓扑——如果 coding-agent 排在 pi-ai 前面，它 build 时可能读到过期的 dist。两种朴素缓解：根 scripts 写成显式串行链（先 build 底层包再 build 上层包），或依赖 tsc 的 project references；要求按依赖图并行执行、带构建缓存的正规方案是 turbo/nx 这类任务编排器【暂时跳过】，知道它们解决"拓扑排序 + 并行 + 缓存"即可。
- 给子包装依赖推荐在根目录用 `-w`，而不是 cd 进子包裸 npm install——后者同样会更新根 lock，但容易漏掉 workspace 上下文。一个易踩的坑：在子包目录里跑 `npm run xxx` 而该子包没定义这个脚本时，npm 会回落执行根 package.json 的同名脚本（根脚本常常是全量构建）。

## 单一 package-lock 的意义

整个 repo 只在根有一份 package-lock.json（子包没有自己的 lock）。意义：

- 全 repo 依赖只解析一次：zod 的版本由一条解析结果统一决定，不存在 packages/ai 用 3.23、packages/agent 用 3.30 各自锁各自的情况。
- 复现以 repo 为单位：根目录 `npm ci` 一条命令重放全部子包的依赖。
- 子包没有独立 lock：看到 packages/ai 下没有 package-lock.json 不是遗漏，是设计如此。
- 对照 Maven：多模块项目靠根 pom 的 dependencyManagement 统一版本靠人维护；npm workspace 是解析器天然统一，lock 是唯一结果。

## scoped 命名规则：@scope/package

- scope 是组织名（npm org / GitHub org），注册后独占，如 `@earendil/pi-ai`。
- 作用一：避免命名冲突——unscoped 名全网先到先得，scoped 名只在自己的组织内竞争。
- 作用二：整体私有性——发布私有包、按 scope 配置 registry/权限（`@earendil:registry=...`），都是 scope 级操作。
- import 路径中 `@earendil/` 是包名的一部分，不是目录。目录叫 `packages/ai` 还是 `packages/pi-ai` 与包名无关——workspace 匹配只看子包 package.json 的 name 字段，不看目录名。

scope 级 registry 配置放在根目录 `.npmrc`（企业内部源常见）：

```ini
@earendil:registry=https://npm.pkg.github.com
//npm.pkg.github.com/:_authToken=${NPM_TOKEN}
```

读法：所有 `@earendil/*` 包从这个 registry 拉取与发布，其余包走默认 npmjs.org。对照 Maven 的 `<repositories>` / `<distributionManagement>` 按 repoId 分流，npm 按 scope 分流。

## 对照：Maven reactor / Gradle / Python

- Maven reactor：根 pom 用 `<modules><module>../ai</module></modules>` 按相对路径显式列出模块，reactor 根据模块间依赖计算构建顺序；模块间引用是 `groupId:artifactId` + 完全相同的 version，Maven 明确知道"这是本地的另一个模块"。npm workspaces：glob 圈地 + name/semver 匹配，npm"假装它是外部包"——安装期用 symlink 冒充 registry 包，发布后声明原样生效无缝切换。这是根本设计差异：Maven 的 workspace 是构建期概念，npm 的 workspace 是安装期概念。
- Gradle：settings.gradle 的 `include` 显式声明子项目，依赖用项目引用 `implementation(project(":ai"))`——本地性和外部依赖在语法上就不同，与 npm 相反。
- Python：uv/pdm workspaces 用 `[tool.uv.sources] pi-ai = { workspace = true }` 之类显式声明"这个依赖取本地成员"，介于两者之间。一句话知道即可。

日常操作的命令对照：

| 语义 | Maven | npm workspaces |
|---|---|---|
| 构建单个模块（含其依赖） | `mvn install -pl packages/agent -am` | `npm run build -w packages/agent` |
| 构建全部模块 | `mvn install`（reactor 排序） | `npm run build --workspaces`（固定顺序） |
| 给模块加依赖 | 编辑 pom 后 `mvn install` | `npm install pkg -w packages/agent` |
| 统一传递依赖版本 | dependencyManagement / BOM | 根 package.json 的 overrides |
| 查依赖来源 | `mvn dependency:tree` | `npm ls <pkg>` / `npm explain <pkg>` |
| 干净复现安装 | `mvn -B` + 固定版本 | `npm ci` |

## 阅读 monorepo 项目的入口流程【必须掌握】

拿到一个陌生 monorepo（比如 pi），按这个顺序建立地图：

```text
① 根 package.json
     ├─ workspaces: ["packages/*"]   ──→ 枚举出所有子包
     ├─ scripts.build / test / check ──→ 知道全量命令怎么跑
     └─ devDependencies              ──→ 知道工具链（tsc? vitest? esbuild?）
② 子包 package.json（packages/coding-agent）
     ├─ bin: { pi: "./dist/cli.js" } ──→ CLI 入口，源码对应 src/cli.ts
     ├─ exports: { ".": ... }        ──→ 库入口，对应 src/index.ts
     └─ dependencies                 ──→ 分层线索
③ 依赖方向图（从各子包 dependencies 汇总）

@earendil/pi-ai            底层：模型/provider 抽象、消息与工具协议类型
        ↑
@earendil/pi-agent         中层：agent 循环、工具执行框架
        ↑
@earendil/pi-coding-agent  顶层：CLI、编辑器集成、产品功能
```

具体步骤：

1. 根 package.json 看 workspaces 与根 scripts，确定包清单和命令体系。
2. 找产品入口：顶层包的 bin 指向 cli，从 cli.ts 开始读启动路径（参数解析 → session 构建 → agent 循环）。
3. 顺着 dependencies 画分层图：谁依赖谁是理解架构的第一张图。pi 的方向是 ai 被 agent 依赖、agent 被 coding-agent 依赖——依赖箭头永远从"产品"指向"基础设施"，反向出现（ai 里 import coding-agent）就是架构异常或 phantom。
4. 进入单包内部后，再从 exports "." 对应的 index.ts 读公开面。

第 2 步落到代码上的样子——bin 指向的 cli 文件，开头三类 import 一眼分清：

```ts
// packages/coding-agent/src/cli.ts（节选）
import { readFileSync } from "node:fs";                  // Node 内置（node: 前缀，永不进依赖）
import { Agent, type Tool } from "@earendil/pi-agent";   // workspace 兄弟包（symlink）
import { z } from "zod";                                 // 外部包（根 node_modules 实体）
import { renderHelp } from "./ui/help.js";               // 包内相对路径

const agent = new Agent({ model: resolveModel(), tools: builtinTools });
```

读 monorepo 源码时，每个 import 都归入这四类之一：内置、workspace、外部、包内。分类错了，对架构的理解就错了——尤其是把 phantom 的外部包误当成 workspace 包。

对照你读 Java 多模块的习惯：reactor 的模块顺序约等于 `--workspaces` 的执行顺序（理想情况）；看子 pom 的 dependencies 理解分层，等价于看子包 package.json 的 dependencies。差别在于 npm 的依赖声明在"本地/外部"上不做区分，分层图要靠 name 对号入座。

## 本章只记住这 5 件事

- 根 package.json 用 workspaces glob 圈定子包，整个 repo 一份 lock，安装只在根跑一次。
- workspace 包互引的原理：name + version 匹配后，npm 在根 node_modules 建 symlink 指向本地包，import 写法与外部包完全一样。
- 版本必须真的匹配：匹配不上 npm 会静默去 registry 装旧版本——monorepo"改了本地代码却没生效"的头号事故来源。
- hoisting 让根 node_modules 成为全 repo 依赖的并集，phantom dependency 在 monorepo 里比单包更普遍。
- 读 monorepo 的固定路线：根 package.json → 子包 bin/exports 定位入口 → dependencies 画分层图（ai ← agent ← coding-agent）。
- 每个 import 归入四类之一：Node 内置（node: 前缀）、workspace 兄弟包、外部包、包内相对路径——分类错误等于架构理解错误。
- `-w` 指定子包跑脚本，`--workspaces` 全量顺序跑且不感知依赖拓扑，编排靠 turbo/nx。

## 源码识别

- 看到根 package.json 的 `"workspaces": ["packages/*"]` → 想到 monorepo，子包都在 packages/ 下，lock 只有根一份
- 看到 node_modules/@earendil/pi-ai 是 symlink → 想到 workspace 本地链接，实体在 packages/ai
- 看到依赖声明匹配不上 workspace 包的 version → 想到 npm 装的是 registry 上的旧版本，不是本地代码
- 看到 `import ... from "../../ai/src"` → 想到错误的跨包引用写法，workspace 应按包名 import
- 看到 `npm run build -w packages/agent` → 想到在 agent 子包上下文执行 build
- 看到 turbo.json / nx.json → 想到任务编排器接管了跨包构建的拓扑排序、并行与缓存
- 看到子包里 import 它未声明、但兄弟包声明了的库 → 想到 monorepo 版 phantom dependency
- 看到子包目录没有 package-lock.json → 正常，lock 只存在于根
- 看到根 .npmrc 里 `@scope:registry=...` → 想到该 scope 的包走专用 registry（企业内部源）

## Java/Python 工程师常见误区

- 错误认知：workspace 互引像 Maven reactor 的模块引用，构建期特判 → 实际 npm 把它当普通 registry 依赖，靠 symlink 冒充，发布后声明原样生效
- 错误认知：子包目录名决定包名 → 实际 name 字段决定，packages/ai 可以叫 @earendil/pi-ai
- 错误认知：`--workspaces` 会按依赖拓扑排序执行 → 实际按声明/glob 展开顺序跑，构建顺序要自己保证或用 turbo
- 错误认知：monorepo 里能 import 到的包一定在本包 dependencies 里 → 实际根 node_modules 的并集都可见，phantom 更普遍
- 错误认知：给子包装依赖要 cd 进子包 npm install → 实际推荐根目录 `npm install pkg -w packages/ai`，统一维护根 lock
- 错误认知：改了本地 packages/ai 的源码兄弟包立刻用上新代码 → 实际消费方解析的是 dist，需要先 build（除非 exports 指向 src）

## 是否值得深入

- exports/bin 与 workspace 的组合细节（子包入口设计）：当前阶段：建议掌握，定位 monorepo 源码入口的日常操作
- turbo/nx 任务编排：当前阶段：不需要深入，知道它解决拓扑排序 + 并行 + 构建缓存即可
- pnpm 的严格 node_modules 模型：当前阶段：建议掌握其隔离原理（对照 phantom dependency），工具本身用到再学
- workspace: 协议（yarn/pnpm）：当前阶段：不需要深入，读 npm 项目遇不到，换工具链时再查
- npm 发包时 workspace 依赖的完整处理（pack 与 publish 差异）：当前阶段：不需要深入，知道"声明原样发布"即可
- lerna：当前阶段：不需要深入，新一代项目已被 npm workspaces + turbo 取代
