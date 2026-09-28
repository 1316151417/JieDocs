# package.json：项目的唯一事实源

## 定位：一个文件，四份职责

Java 工程里"项目是什么、依赖什么、怎么构建、怎么发布"分散在多个文件：`pom.xml` 管依赖与构建插件，`MANIFEST.MF` 管 JAR 元数据（通常自动生成），发布配置在 distributionManagement。Python 把元数据和构建后端放进 `pyproject.toml`（PEP 621），依赖锁又拆出 `uv.lock` / `poetry.lock`。

Node.js 把这些全部合进一个 `package.json`：

| 职责 | Maven | Python | package.json |
|---|---|---|---|
| 项目元数据 | pom 坐标 | `[project]` 表 | name / version |
| 依赖声明 | `<dependencies>` + scope | `dependencies` | dependencies / devDependencies 等 |
| 构建与任务 | mvn phase + plugin | 无（交给外部工具） | scripts |
| 发布描述 | distributionManagement | build 后端配置 | bin / exports / files |
| 运行时配置 | application.yml | settings.py | 不在这里 |

注意最后一行：package.json 不放业务运行时配置（那是 `.env` / config 文件的事）。它是构建与分发层面的"事实源"。

读源码习惯：拿到任何 Node 项目，第一个读的就是 package.json——它告诉你入口在哪（exports / bin）、依赖什么（dependencies）、命令怎么跑（scripts）。等同于你拿到 Maven 项目先看 pom.xml 的 `<modules>` 和 `<dependencies>`。

## name 与 version：包的身份

```json
{
  "name": "@earendil/pi-ai",
  "version": "0.12.0"
}
```

- name 在整个 npm registry 内唯一，就是 import 时写的说明符（specifier）。
- scoped 命名 `@scope/name`：scope 通常是组织名（GitHub org / npm org），不是文件路径。scope 与目录结构无关——`packages/ai` 目录下的包可以叫 `@earendil/pi-ai`。
- `@earendil/` 是包名的一部分：`import { Agent } from "@earendil/pi-ai"` 里没有任何"目录"含义，Node 把整个字符串当一个包名查 node_modules。
- version 遵循 semver（下一章展开）：MAJOR.MINOR.PATCH。

对照：Maven 坐标是 groupId:artifactId:version 三元组；npm 是 name:version 二元组，scope 吸收了 groupId 的"组织归属"职责。unscoped 名（如 lodash）全网先到先得，组织用 scope 防止撞名——scope 的发布语义第 12 章结合 monorepo 再看。

## private: true：防误发布开关

```json
{
  "name": "pi",
  "private": true
}
```

npm publish 对 `private: true` 的包直接报错。monorepo 根 package.json 必设——根只是容器，不是可发布产物。近似 Maven 里 `packaging=pom` 的聚合 POM"不产出构件"，但机制不同：Maven 是"没配 deploy 就没有发布这回事"，npm 是一个显式布尔开关挡住 publish。

## "type": "module"：决定 .js 的解析方式【必须掌握】

问题：Node 有两代模块系统，都在生产环境大规模使用：

- CJS（CommonJS）：`const x = require("pkg")` / `module.exports = { ... }`
- ESM（ECMAScript Modules）：`import x from "pkg"` / `export ...`

同一个 `.js` 文件按哪套语法解析，由离它最近的 package.json 的 `type` 字段决定：

```json
{ "type": "module" }
```

- `"type": "module"`：该 package.json 管辖目录下所有 `.js` 按 ESM 解析。
- `"type": "commonjs"` 或缺省：按 CJS 解析。缺省是 CJS，这是历史包袱（ESM 落地前 CJS 已统治十年）。
- `.mjs` 强制 ESM，`.cjs` 强制 CJS：扩展名覆盖 type 字段，用于双模块并存的包。

为什么读源码要紧：你在 `packages/ai/src` 下看到 `import { z } from "zod"` 还是 `const { z } = require("zod")`，直接由这个字段决定。现代新项目几乎全是 ESM（Node 18+ 生态成熟，top-level await、静态可分析、tree-shaking 都靠它），但大量存量依赖仍是 CJS，两套系统的互操作噪音贯穿 Node 源码阅读。

Node 解析某个文件用哪套模块系统，决策顺序固定：

```text
import "./foo.js"
  ↓ foo.mjs → ESM（扩展名说了算）
  ↓ foo.cjs → CJS（扩展号说了算）
  ↓ foo.js  → 找离它最近的 package.json
               "type": "module"        → ESM
               "type": "commonjs"/缺省 → CJS
```

不能类比的地方：它不是 Maven 的什么编译开关，更像 Python 2/3 的方言选择——同一个运行时、两套语法，靠文件扩展名 + 元数据切换。TypeScript 侧的对应物是 tsconfig 的 `module` 字段（决定 TS 编译产物的模块格式）。

## main / module / browser【看懂即可】

旧入口字段三件套，读老包会碰到：

```json
{
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "browser": "./dist/index.browser.js"
}
```

`main` 是 Node 的入口（最老的标准）；`module` 是打包器（webpack/rollup 时代）约定的 ESM 入口，Node 本身不认识；`browser` 是浏览器环境的替换入口。现代包用 exports 统一取代三者，知道存在即可，需要时再查。

## exports：现代入口与门禁【必须掌握】

解决的问题：`main` 只能声明一个入口，且包内任意文件都能被外部 `require("pkg/lib/internal/util")` 引到——作者无法控制公开面。exports 把"哪些路径可导入、什么运行环境用哪个文件"变成显式声明：

```json
{
  "name": "@earendil/pi-ai",
  "exports": {
    ".": {
      "types": "./dist/index.d.ts",
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs"
    },
    "./models": {
      "types": "./dist/models.d.ts",
      "default": "./dist/models.js"
    }
  }
}
```

- `"."` 是主入口：`import { Agent } from "@earendil/pi-ai"` 命中这里。
- `"./models"` 是子路径导出：`import { listModels } from "@earendil/pi-ai/models"` 命中；没列出的路径（如 `./internal`）一律报 `ERR_PACKAGE_PATH_NOT_EXPORTED`。
- 条件对象按声明顺序匹配，第一个命中的生效：`types` 给 TypeScript（必须放第一位，否则 TS 会先命中 import/require 而拿不到类型声明）、`import` 给 ESM、`require` 给 CJS、`default` 兜底。

门禁语义：exports 字段一旦存在，包就变成"封闭式"——只有列出的路径可被外部导入。没有 exports 字段的包是"开放式"：任何深度的文件都能按相对路径 import 到。这与 Java 相反：Java 包默认全可见（除 package-private 成员访问控制外没有包级屏障），要收敛公开面得上 JPMS 的 `module-info.java`（用 exports 指令声明哪些包公开）。而 npm 的 exports 是"出现即默认全封闭"，比 JPMS 更激进——JPMS 不写 module-info 时一切照旧。

三种 import 写法对照着记：

```ts
import { Agent } from "@earendil/pi-ai";              // bare specifier → 命中 exports "."
import { listModels } from "@earendil/pi-ai/models";  // 子路径 → 命中 exports "./models"
import { util } from "@earendil/pi-ai/dist/util.js";  // 深路径 → 未声明，被门禁拒绝
```

读源码触发点：`import { X } from "@earendil/pi-ai/models"` 报错或编辑器提示找不到类型，第一反应是去 `node_modules/@earendil/pi-ai/package.json` 查 exports——有没有这个子路径？types 条件写了吗？反过来看一个陌生包，exports 列了什么，就是作者承认的公开 API 面。

## bin：CLI 命令的诞生机制

```json
{
  "name": "@earendil/pi-coding-agent",
  "bin": { "pi": "./dist/cli.js" }
}
```

bin 是"命令名 → 可执行脚本"的映射，目标文件首行是 `#!/usr/bin/env node`（内核按 shebang 用 node 执行）。三种安装形态：

- `npm install -g`：npm 往全局 bin 目录（nvm 环境在 nvm 目录下，否则通常是 /usr/local/bin）创建名为 `pi` 的 symlink，之后直接敲 `pi`。
- `npm install`（项目内）：在项目 `node_modules/.bin/pi` 创建链接，scripts 里可按名调用。
- `npx pi` / `npx @earendil/pi-coding-agent`：不全局安装，临时解析并执行同一入口。

这就是 coding agent 发布成 CLI 的机制：用户 `npm install -g @earendil/pi-coding-agent` 之后直接得到 `pi` 命令：

```bash
npm install -g @earendil/pi-coding-agent   # 全局 bin 目录出现 pi → .../dist/cli.js
pi --version
npx @earendil/pi-coding-agent --help       # 临时解析执行，不落地全局
```

对照：pip 的 entry_points console_scripts 几乎同构（声明入口，安装器生成命令）；Maven 没有等价物——exec-maven-plugin 只是跑 mainClass，不会往 PATH 装命令。

## scripts：任务入口表

```json
{
  "scripts": {
    "build": "tsc -p tsconfig.build.json",
    "test": "vitest run",
    "check": "npm run lint && npm run typecheck",
    "dev": "node --watch dist/cli.js"
  }
}
```

- `npm run <name>` 用 shell 执行该字符串；`&&` 串行组合；裸 `npm run` 列出全部脚本。
- 传参用 `--` 分隔：`npm run test -- src/foo.test.ts` 相当于 `vitest run src/foo.test.ts`。
- 关键机制：脚本执行时 PATH 前置了 `./node_modules/.bin`。tsc、vitest、eslint 都没有全局安装——npm install 时，npm 把每个依赖包 bin 字段声明的可执行文件链接进 `node_modules/.bin`，scripts 里按裸名调用。
- 对照 Maven：mvn 的构建能力来自 pom 里声明的 plugin，由 Maven 统一调度生命周期；npm 本身没有任何构建能力，它只是"包安装器 + 带 PATH 注入的脚本运行器"，工具链全部来自 devDependencies。理解了这点，就不会去找"npm 的编译命令"——编译是 tsc，测试是 vitest，npm 只负责叫它们。

pre/post 钩子一句话：`npm run test` 前后自动执行 `pretest` / `posttest`，install 类生命周期同理（preinstall / postinstall）。现代项目倾向在 scripts 里显式组合而非依赖隐式钩子，【看懂即可】。

## 依赖四类：dependencies / devDependencies / peerDependencies / optionalDependencies

### dependencies 与 devDependencies

```json
{
  "dependencies": {
    "@earendil/pi-ai": "^0.12.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  }
}
```

- dependencies：运行时需要，下游安装你的包时会一并装上（传递依赖的来源）。
- devDependencies：仅本包开发需要（编译器、测试器、linter），下游装你时完全不装。

近似与差异：Maven compile scope 近似 dependencies；provided + test 的组合近似 devDependencies 的"只在本项目可见"。关键差异在传递性——Maven 的 test scope 依赖不传递但仍在你的编译 classpath；npm 的 devDependencies 根本不进入下游依赖图，下游 node_modules 里不存在它。所以"放哪边"的判断标准只有一条：装你的用户运行时需不需要它。

### peerDependencies：声明"宿主自己提供"

```json
{
  "name": "@earendil/pi-plugin-lint",
  "peerDependencies": {
    "@earendil/pi-agent": ">=0.10.0 <0.13.0"
  }
}
```

语义：本包与宿主的这个依赖协同工作，但要求宿主环境自己提供，本包不携带。插件式生态（React 组件库、ESLint 插件、coding agent 扩展）的标准做法。

为什么必须这样：假设插件自带一份 pi-agent，宿主代码里的 pi-agent 实例与插件内部 import 到的 pi-agent 是两个模块实例——`instanceof` 判断失败、全局状态（事件总线、注册表）分裂。peer 声明保证整棵树只有一份。

对照：最接近 Maven provided scope（"编译期可见，运行期由环境提供"），但方向相反——provided 描述"部署容器会给"，peer 描述"安装我的人会给"。另注意 npm 7+ 会自动安装缺失的 peerDependencies（把它当普通依赖补一份），行为更宽容也更容易掩盖问题。

### optionalDependencies 一句话

安装失败不报错、平台不符就跳过（典型如 macOS 专用的 fsevents），知道存在即可，需要时再查。

四类依赖一张表收口：

| npm 字段 | Maven 近似 | 关键差异 |
|---|---|---|
| dependencies | compile | 传递安装，来源真实 |
| devDependencies | provided + test | 完全不进下游依赖图 |
| peerDependencies | provided | 方向相反："安装我的人提供"，强制单实例 |
| optionalDependencies | 无直接对应 | 安装失败静默跳过 |

## engines / files / overrides

```json
{
  "engines": { "node": ">=20" },
  "files": ["dist"],
  "overrides": { "strip-ansi": "6.0.1" }
}
```

- engines：Node 版本约束。默认 npm 只发警告不拦截（除非 .npmrc 里 `engine-strict=true`），声明的意义大于强制力——比 Maven enforcer plugin 软得多。
- files：npm publish 时只打包列出的目录/文件（package.json、README、LICENSE 自动包含）。对照 Maven assembly 的打包选择或 Python wheel 只打包声明包。
- overrides：只能写在根 package.json，强制整棵依赖树里某个传递依赖采用指定版本。类比 Maven dependencyManagement 的强制力，但方向相反：dependencyManagement 是"为自己家声明版本优先级"，overrides 是"穿透修改别人家依赖的版本"。只对 npm 生效，yarn/pnpm 各有等价字段（resolutions / pnpm.overrides），一句话知道即可。

## 完整走读：一个 coding-agent 子包

```json
{
  "name": "@earendil/pi-coding-agent",
  "version": "0.12.0",
  "private": true,
  "type": "module",
  "bin": { "pi": "./dist/cli.js" },
  "exports": {
    ".": { "types": "./dist/index.d.ts", "import": "./dist/index.js" },
    "./agents": "./dist/agents/index.js"
  },
  "files": ["dist"],
  "scripts": {
    "build": "tsc -p tsconfig.build.json",
    "test": "vitest run",
    "check": "npm run lint && npm run typecheck"
  },
  "dependencies": {
    "@earendil/pi-ai": "^0.12.0",
    "@earendil/pi-agent": "^0.12.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "typescript": "^5.6.0",
    "vitest": "^2.1.0"
  },
  "engines": { "node": ">=20" }
}
```

翻译成人话：这是 ESM 包（type），对外提供 `pi` 命令（bin）和两个可导入入口（exports：主入口 + `./agents` 子路径），发布只带 dist（files），运行依赖两个兄弟 workspace 包加 zod，开发工具 typescript + vitest，要求 Node 20+，private 挡发布（实际项目里要么 private 要么走发布流程，此处示范字段全貌）。90% 的 package.json 就这点信息量。

拿到陌生 package.json 的固定阅读顺序：

```text
① name + private   → 这是谁？发布物还是内部包？
② type             → 源码是 ESM 还是 CJS？
③ bin / exports    → 入口在哪？（CLI 看 bin，库看 exports）
④ dependencies     → 运行时依赖了什么（= 架构分层线索）
⑤ scripts          → build / test / check 怎么跑
⑥ devDependencies  → 工具链是什么（tsc？vitest？esbuild？）
```

## 本章只记住这 5 件事

- package.json 一个文件承担 pom.xml + pyproject.toml + 脚本 + 发布描述四份职责，读 Node 项目永远从它开始。
- `"type": "module"` 决定 .js 按 ESM 还是 CJS 解析，缺省 CJS，`.mjs`/`.cjs` 覆盖它；源码里 import 还是 require 由它决定。
- exports 是现代包入口兼门禁：字段一旦存在，未列出的路径外部无法 import。
- bin 声明 CLI 命令，npm install -g / npx 靠它把包装成 PATH 上的命令。
- scripts 直接调用 node_modules/.bin 里的可执行文件；npm 是脚本运行器 + 包安装器，不是构建系统。
- peerDependencies 声明"宿主自己提供"，核心目的是整棵树只保留一份实例。

## 源码识别

- 看到 `@scope/pkg` → 想到包名整体，scope 是组织名，不是目录
- 看到 `"type": "module"` → 想到该包 .js 全按 ESM 解析，源码应是 import/export
- 看到 `.mjs` / `.cjs` → 想到强制指定模块系统的文件，覆盖 package.json 的 type
- 看到 `exports: { ".": { ... } }` → 想到现代包入口，未列出的子路径 import 不到
- 看到 `ERR_PACKAGE_PATH_NOT_EXPORTED` → 想到 exports 门禁拦截，去查那个包的 exports
- 看到 `bin: { pi: "./dist/cli.js" }` → 想到 CLI 包，全局安装后命令叫 pi
- 看到 `peerDependencies` → 想到插件式包，宿主必须提供该依赖且版本要匹配
- 看到 scripts 里的裸命令 tsc / vitest → 想到来自 node_modules/.bin，由 devDependencies 提供

## Java/Python 工程师常见误区

- 错误认知：devDependencies 会像 Maven test scope 一样参与传递 → 实际完全不进入下游依赖图，下游根本不装
- 错误认知：有没有 exports 字段只影响入口写法 → 实际没有它包全路径开放，有它未声明即禁止
- 错误认知：name 里的 `@scope/` 是目录路径 → 实际是包名的一部分，scope 是组织命名空间
- 错误认知：npm scripts 等价 Maven phase，npm 会编排构建生命周期 → 实际 npm 只是注入 PATH 跑 shell 命令，顺序自己写
- 错误认知：engines 像 maven-enforcer 一样硬约束 → 实际默认只是警告，除非 engine-strict
- 错误认知：private: true 是私有权限控制 → 实际只是禁止 npm publish 的开关

## 是否值得深入

- exports 条件匹配顺序与自定义 conditions：当前阶段：建议掌握，读现代包的类型解析与报错必备
- CJS/ESM 互操作细节（default 导出互转、import 属性）：当前阶段：建议掌握，教材后续章节结合实例展开
- npm 发包流程（npm publish、provenance、deprecate）：当前阶段：不需要深入，会读 package.json 的发布字段即可
- overrides / resolutions 跨包管理器差异：当前阶段：不需要深入，遇到传递依赖版本冲突再查
- semver 完整规范（预发布、build metadata）：当前阶段：不需要深入，掌握 ^ ~ exact 够用
