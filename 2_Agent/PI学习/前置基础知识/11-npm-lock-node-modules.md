# npm、package-lock.json 与 node_modules

## 三层心智模型【必须掌握】

```text
package.json（意图：我要什么，范围版本）
     ↓ npm install（依赖解析：逐层解析 ^ ~ 范围 → 具体版本）
package-lock.json（结果：整棵树每个包的精确版本+来源+完整性哈希）
     ↓ npm ci / npm install 落盘
node_modules（扁平化目录树，运行时真正 import 的东西）
```

三层各自回答一个问题：

- package.json：我想要什么——范围声明，人类可维护。
- package-lock.json：上次解析出了什么——整棵依赖树的精确快照，机器可复现。
- node_modules：现在磁盘上有什么——真实文件，运行时消费。

与 Java/Python 的对照：

| 层 | Maven 世界 | Python 世界 |
|---|---|---|
| 范围声明 | pom 里的 version range（少见） | pyproject.toml dependencies |
| lock 快照 | 无官方对应（版本通常写死） | uv.lock / poetry.lock |
| 落盘位置 | ~/.m2 仓库 + 运行时拼 classpath | venv 的 site-packages |

关键差异：Maven 把构件缓存在 ~/.m2、构建时拼 classpath，项目目录里没有"依赖实体"；npm 把依赖实体装进每个项目自己的 node_modules，重复占磁盘但项目间隔离彻底。

lock 文件的真实形状（节选）：

```json
{
  "name": "pi",
  "lockfileVersion": 3,
  "packages": {
    "": { "name": "pi", "workspaces": ["packages/*"], "dependencies": { "zod": "^3.23.0" } },
    "node_modules/zod": {
      "version": "3.23.8",
      "resolved": "https://registry.npmjs.org/zod/-/zod-3.23.8.tgz",
      "integrity": "sha512-X1...",
      "dev": false
    },
    "packages/ai": { "name": "@earendil/pi-ai", "version": "0.12.0" }
  }
}
```

读法：`node_modules/zod` 是 key，value 里 `version` 是解析出的精确版本（package.json 只写了 ^3.23.0）、`resolved` 是下载地址、`integrity` 是内容哈希（防篡改 + 缓存寻址）。monorepo 的 workspace 包也记录在 lock 里（`packages/ai`），但不从 registry 下载。lock 的价值就在于：把"解析这一步"的结果固化，任何人任何时候重放都得到同一棵树。

## npm install vs npm ci【必须掌握】

| | npm install | npm ci |
|---|---|---|
| 依赖来源 | 尽量满足 lock，必要时重新解析 | 严格按 lock，一字不改 |
| 写 lock | 会把结果写回 lock | 绝不写 |
| node_modules | 增量更新 | 先整目录删掉再装 |
| lock 与 package.json 不一致 | 重新解析并更新 lock | 直接报错退出 |

记忆法：install 是开发时的"协商"——顺手升级、更新 lock；ci 是部署时的"重放"——精确复现、不容忍偏差。所以 CI、Docker 构建、同事间"我这里装不上"的排查，一律 `npm ci`。对照 `mvn -B` 固定版本的复现构建、`pip install -r requirements.lock` / `uv sync --frozen` 的心智：先有 lock，一切照 lock。

典型工作流：

```bash
git pull        # 同事改了依赖，lock 有更新
npm ci          # 删光 node_modules，按新 lock 精确重放（解决"我这里跑不了"）
```

```dockerfile
FROM node:20
COPY package.json package-lock.json ./
RUN npm ci                      # Docker 层缓存友好：lock 不变就不重新装
COPY . .
```

顺带一句：npm ci 通常比干净 install 快（零解析、纯下载解包），大 repo 上差距明显。

## semver 范围：^、~ 与 exact【必须掌握】

声明写在 package.json：

```json
{
  "dependencies": {
    "zod": "^3.23.0",
    "typescript": "~5.6.2",
    "strip-ansi": "6.0.1"
  }
}
```

- `^3.23.0`：允许 minor + patch 升级，即 `>=3.23.0 <4.0.0`。
- `~5.6.2`：只允许 patch 升级，即 `>=5.6.2 <5.7.0`。
- `6.0.1`：无符号 = 精确锁定这一个版本。

升级矩阵（registry 上存在这些版本时，谁能装到谁）：

| 声明 \ 已发布版本 | 3.23.0 | 3.24.1 | 3.30.0 | 4.0.0 |
|---|---|---|---|---|
| `^3.23.0`（minor+patch） | 可装 | 可装 | 可装 | 拒绝 |
| `~3.23.0`（仅 patch） | 可装 | 拒绝 | 拒绝 | 拒绝 |
| `3.23.0`（exact） | 可装 | 拒绝 | 拒绝 | 拒绝 |

0.x 特例一句话：`^0.2.3` 只允许 patch（0.x 阶段 minor 被视为破坏性变更），知道存在即可。

为什么 lock 必须存在：范围声明不可复现。今天装到 3.23.0，半年后新机器装到 3.30.0——你没改任何声明，行为却可能漂移。npm 生态默认范围声明，因此 lock 才是复现的事实源；Maven 文化相反，pom 里默认写死精确版本，range 是少数派。npm update 一句话：把范围内的依赖刷新到最新可满足版本并写回 lock，日常很少主动用。

## node_modules 结构：嵌套 + 提升【必须掌握】

理论模型是真树：每个包的依赖放在自己名下的 node_modules 里。npm 实际做法是提升（hoisting）：默认把所有包尽量提到根 node_modules 形成扁平结构，只有版本冲突时才嵌套：

```text
repo/node_modules/
├── zod/                        ← 被提升到根，全 repo 共用一份
├── commander/
└── pi-internal/
    └── node_modules/
        └── zod/                ← 版本冲突时，嵌套第二份 zod
```

提升的好处：同版本只装一份，磁盘和安装时间都省。代价是下面这个 Node 特有的坑。

先看清 Node 找包的规则（这决定了提升为什么有效）：

```text
packages/coding-agent/src/cli.ts 里 import "commander"
  → packages/coding-agent/src/node_modules/     没有
  → packages/coding-agent/node_modules/         没有
  → packages/node_modules/                      没有
  → repo/node_modules/commander                 命中（被提升上来的）
```

每一级目录只要没有，就向上一层找。提升把大部分包放到最顶层，于是"我自己的"和"别人的"在这一步混在一起了。

### phantom dependencies【必须掌握】

```ts
// packages/coding-agent/src/cli.ts
import { Command } from "commander";   // 本包 package.json 里并没有 commander
```

这段代码能正常运行——因为 packages/agent（或其他某个依赖）声明了 commander，npm 把它提升到了根 node_modules，coding-agent 的 import 按"从当前目录向上逐级查 node_modules"的规则命中了它。

风险：这是借道可见，不是你自己的声明。换 pnpm（隔离解析）、某天 commander 因版本冲突变成嵌套安装、或把这个包抽出去独立发布时，import 立刻解析失败。

排查命令与输出形态：

```text
$ npm ls commander
pi@0.12.0 /repo
└─┬ @earendil/pi-agent@0.12.0
  └── commander@12.1.0
```

读法：commander 是 pi-agent 的依赖（被提升到根），coding-agent 自己没声明。`npm explain commander` 会给出更完整的多路径解释。

读 monorepo 源码的实操要点：见到一个 import，先判断"这是谁提供的"——先查本包 package.json 的 dependencies / devDependencies；查不到就 `npm ls commander` 看它从依赖树哪条路径来的。import 了未声明的包 = phantom dependency，读代码时要意识到"这份代码依赖了一个它没承认的东西"。

对照 Java：JVM 的 import 必须命中 classpath 上的类，而 Maven 保证每个 groupId:artifactId 只有一个胜出版本，未声明的依赖编译期就找不到。TypeScript/JS 的模块解析只看文件系统（node_modules 目录里有没有这个文件夹），不看 package.json 声明——所以"没声明也能跑"是 Node 独有的现象。

## 传递依赖：npm 允许多版本共存

两个依赖分别要 zod@3.23 和 zod@3.30 时，三种生态的处理：

- Maven：nearest-wins——离根近的声明胜出，classpath 上只有一份（另一版本被裁剪，可能埋下运行时 NoSuchMethodError）。
- pip：解析器为整个环境求一个可行解，全局只有一个 zod 版本（解不出来就装不上）。
- npm：两份都装——一份提升到根，一份嵌套在请求方名下，各 import 各的。

共存的具体形态：

```text
repo/node_modules/
├── zod/                                  ← zod@3.30.0（根，多数包用这份）
└── pi-internal/
    └── node_modules/
        └── zod/                          ← zod@3.23.0（只有 pi-internal 用这份）
```

pi-internal 里 `import { z } from "zod"` 命中嵌套的 3.23.0（先查自己名下），其他包命中根的 3.30.0。运行时它们是两个完全独立的模块实例，连全局符号都不共享。

允许共存是 npm 与前两者的关键差异。好处是"两个库永远无法共存"这类依赖地狱基本消失；代价是磁盘体积、提升带来的 phantom 副作用、以及"同一段代码在不同包里可能跑不同版本"的调试成本。

## npm cache【看懂即可】

一句话：npm 在 ~/.npm 维护内容寻址缓存（按 tarball 哈希存储），装过的包不再重新下载，加速 install 与 ci。知道存在即可，需要时再查。

## node_modules 为什么不进 git

两个硬理由：

- 体积：中型项目上万包、十万级文件、GB 级占用。
- 平台二进制：esbuild、better-sqlite3 等 native 模块按平台编译产物，macOS 上提交的文件对 Linux 无用。

所以 .gitignore 永远排除 node_modules，clone 后第一件事是 npm ci 重放。对照 vendored 依赖的心智（Go 的 vendor/、早年 Rails 的 vendor/）：那套思路是"把依赖源码提交进仓库，换取绝对可复现"；Node 生态选择"package.json 声明意图 + lock 记录结果，node_modules 随时可重放"。读别人的 repo 时，node_modules 不存在是常态，不要当成缺文件。

## 本章只记住这 5 件事

- 三层模型：package.json 是意图（范围），lock 是结果（精确树），node_modules 是落盘（运行时实体）。
- 本地开发用 npm install（会更新 lock），CI/复现用 npm ci（严格按 lock、先删 node_modules、绝不改 lock）。
- ^ 允许 minor+patch，~ 只允许 patch，无符号是精确锁定；lock 存在就是因为范围声明不可复现。
- node_modules 是提升 + 嵌套的混合体；npm 允许多版本共存，这是与 Maven nearest-wins / pip 单版本的关键差异。
- phantom dependency：import 未声明的包也能跑，因为被提升到了可见范围——读源码先判断这个 import 是谁提供的。
- node_modules 不进 git（体积 + 平台二进制），clone 后 npm ci 重放。

## 源码识别

- 看到 dependencies 里全是 `^x.y.z` → 想到意图声明，真实安装版本要看 lock
- 看到 package-lock.json → 想到可复现构建的凭据，CI 里应配 npm ci
- 看到 node_modules 内同名包多层嵌套 → 想到版本冲突共存，不是装坏了
- 看到 import 了本包 package.json 未声明的包 → 想到 phantom dependency，用 npm ls 查来源
- 看到 lock 里 `integrity: sha512-...` → 想到完整性哈希，防篡改与缓存寻址都靠它
- 看到 .npmrc 里 engine-strict=true → 想到 engines 从警告升级为硬约束

## Java/Python 工程师常见误区

- 错误认知：npm install 等价 mvn install（装的是本地构件） → 实际更像 mvn dependency:resolve，装的是外部依赖
- 错误认知：像 Maven 一样全树一个胜出版本 → 实际 npm 多版本嵌套共存，各自隔离
- 错误认知：删掉 lock 重新 install 结果一样（反正有 semver 约束） → 实际范围会重新解析到新版本，构建悄然漂移
- 错误认知：能 import 到的包一定在 package.json 里声明过 → 实际扁平化后有大量"借道可见"的未声明包
- 错误认知：npm ci 会顺带把过时依赖升上去 → 实际它只重放 lock，更新要靠 npm update / npm install

## 是否值得深入

- semver 预发布与 build metadata 规则：当前阶段：不需要深入，知道预发布版本默认不进任何范围即可
- npm 的依赖解析算法（arborist）内部：当前阶段：不需要深入，掌握"提升 + 嵌套"的结果模型即可
- npm cache 结构与故障排查：当前阶段：不需要深入，出问题时先 npm cache verify 再查文档
- overrides 强制传递依赖版本：当前阶段：不需要深入，真遇到版本冲突再查，用法见第 10 章
