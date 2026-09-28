# TypeScript 核心：源码阅读所需的最小集

本章面向"读源码"而非"从零写"：只覆盖 Java/Python 工程师在现代 TS 项目（尤其 AI Coding Agent 类）源码里真正会遇到的部分。每个概念先给 Java/Python 的最近对应物，再讲差异与错误类比。`async/await` 在本章当普通语法认即可，运行机制（事件循环、微任务）在第 04 章。

## 0. 先立两个心智模型

模型一：TypeScript = JavaScript + 一层编译期类型标注。

```
   agent.ts                  tsc / esbuild（删除所有类型）          agent.js
┌──────────────────┐     ───────────────────────────────────▶   ┌────────────┐
│ let u: User      │       类型标注、interface、type、泛型       │ let u = …  │
│ interface User {}│       在产物里一点不剩                     │ （纯 JS）  │
└──────────────────┘                                                └────────────┘
```

Java 的类型是运行时事实（`getClass()`、`instanceof`、反射都依赖它）；TS 的类型只活在编译期。这个差异贯穿全章，是读 TS 源码最重要的背景。

模型二：对象由字面量直接构造，类型是事后贴的标签。Java 必须先定义 class 才能造对象；TS/JS 里 object literal 是主角，数据形状随手写，类型系统负责事后描述。

## 1. let / const（var 一句带过）

`const` ≈ Java `final`：锁的是"绑定不可重新赋值"，不锁对象内容（≈ final 引用指向可变对象）。`let` 用于需要重新赋值的变量。两者都是块级作用域。

```ts
const retries = 3;
retries = 5;                      // 编译错误
const tool = { name: "fs" };
tool.name = "read_file";          // OK：绑定没变，对象内容可变

let count = 0;
count = count + 1;                // OK
```

【暂时跳过】`var`：函数作用域的老写法，只有读老代码会遇到，知道存在即可。

## 2. object 与 array：字面量是主角

```ts
// 不定义类，字面量即对象；类型可以事后描述（见第 16 节 typeof）
const request = {
  model: "claude-sonnet-4-5",
  messages: [{ role: "user", content: "hi" }],
  max_tokens: 1024,
};
```

对比 Java：造这个对象得先定义一个类（或用 Record/Map 绕路）；TS 里数据的默认形态就是嵌套字面量，LLM API 的请求/响应结构尤其如此。

array 是动态数组（≈ 内置的 `ArrayList`，写法 `T[]`），主流用法是方法式风格，与 Java Stream / Python 列表推导一一对应，本章不展开：

```ts
const names = tools.map((t) => t.name);            // ≈ stream().map()
const usable = tools.filter((t) => !t.disabled);   // ≈ stream().filter()
```

## 3. function：一等公民 + 函数类型表达式

函数是值：可赋给变量、当参数传、当返回值（≈ Java lambda + 函数式接口，但不必先定义接口；≈ Python def）。函数类型用箭头语法写在类型位置：

```ts
// 函数类型表达式：(参数类型) => 返回类型，不是 Java 的接口方法签名
type ToolHandler = (args: unknown) => Promise<string>;

// 可选参数 / 默认参数 / rest 参数（≈ Java 可变参数）
function buildPrompt(system: string, temperature = 0.7, ...stop: string[]) {
  return system;
}
buildPrompt("agent");                  // temperature=0.7, stop=[]
buildPrompt("agent", 0.2, "END");      // 按位置覆盖
```

看到 `opts?: {...}` 要想到：同样的需求在 Java 里会变成一串重载或 Builder，TS 用可选参数 + 对象参数直接解决。

## 4. arrow function

```ts
const names = tools.map((t) => t.name);              // 单表达式省 return 和花括号
const run = async (input: string) => { /* ... */ };  // async 是函数修饰关键字
```

与普通 `function` 唯一实用的差异是 `this`：arrow function 没有自己的 `this`，捕获外层作用域的值【看懂即可】。老代码里 `const self = this` 的样板由此而来；现代源码几乎全用 arrow function，`this` 陷阱多见于遗留事件/DOM 代码。

## 5. destructuring：源码里极高频

```ts
// 对象解构 + 重命名 + 默认值
const { model, max_tokens: maxTokens = 4096 } = request;

// 数组解构（跳位取值）
const [firstMsg] = messages;
const [, second] = items;

// 参数解构：Agent 源码最常见的函数签名形态
function runAgent({ model, tools = [] }: RunOptions) { /* ... */ }
```

Python 有几乎相同的语法；Java 没有对应物（最接近的是 record 解构模式匹配）。"从对象里抽几个字段"一律用它，读函数签名时先认参数解构再看类型。

## 6. spread：展开、合并、浅拷贝

```ts
const merged = { ...defaults, ...userConfig };   // 合并，后者覆盖前者 ≈ Python **
const allMsgs = [{ role: "system", content: sys }, ...messages];  // ≈ Python *
const copy = [...items];                          // 浅拷贝
const next = { ...state, status: "done" };        // 不可变更新的标准写法
```

注意浅拷贝只复制第一层，嵌套对象仍共享引用。Agent 的状态流转、配置合并几乎都是这两个写法的变体。

## 7. 三个高频操作符：`?.`、`??`、模板字符串

```ts
const fn = msg.tool_calls?.[0]?.function?.name;  // 链上任一是 null/undefined → 整体 undefined
const retries = config.retries ?? 3;             // 只对 null/undefined 兜底
const label = config.label || "default";         // 陷阱："" 和 0 也会被换掉
const url = `${baseUrl}/v1/chat/completions`;    // ≈ Python f-string，Java 无
```

`?.` ≈ Java `Optional.map` 链的轻量版，语义是"短路到 undefined"而非抛 NPE。`??` 与 `||` 的区别只在 falsy 值：`0`、`""`、`false` 对 `||` 触发兜底、对 `??` 原样通过——数字/字符串字段上误用 `||` 是真实的高频 bug。

## 8. class：prototype 的语法糖

```ts
class Agent {
  #history: Message[] = [];          // 真 private：# 是 JS 语法，运行时也不可访问
  private name: string;              // TS private：编译期检查，擦除后等于没有
  constructor(name: string) {
    this.name = name;                // 字段要么声明处初始化，要么构造器里赋值
  }
  get history() { return this.#history; }          // getter 是属性描述符
  static create(cfg: AgentConfig) { /* ... */ }    // 静态成员挂在类上
}
```

与 Java class 的关键差异：

- 本质是 `prototype + constructor 函数` 的语法糖；class 本身也是值，可以赋值、传递、比较。
- 无方法重载：一个名字一个实现，"多签名"用可选参数 / union 模拟。
- 可见性只有两档：`#x` 运行时真私有；`private`/`protected` 是类型标注，产物里任何代码都能访问。
- 没有包级可见性，模块私有靠"不 export"（第 02 章）。

现代 Agent 源码里 class 密度远低于 Java 项目：函数 + 对象 + union 是默认建模工具。

## 9. interface vs type

两者都是纯类型层工具，90% 场景可互换，团队约定决定用哪个：【必须掌握】的是认形状，不是背差异。

```ts
interface Tool {
  name: string;
  run(args: unknown): Promise<string>;
}
type ToolName = string | null;   // type 还能表达 union/原始类型/映射类型；interface 只描述对象形状
```

细微差别【看懂即可】：interface 支持"声明合并"——同名 interface 自动合并为一个，所以老代码里同一 interface 分散多处声明不是错误；type 不允许重复定义。

## 10.【必须掌握】结构化类型：按形状匹配，不按名字

TS 是 structural typing：兼容性只看"有没有这些成员"，不看类名与继承链。一句话：鸭子类型，但检查提前到编译期（Python 的鸭子检查在运行时以 `AttributeError` 暴露，TS 在你写错的那行报红）。

```ts
class FileRead  { path: string; }
class FileWrite { path: string; }

const w: FileWrite = new FileRead();
// TS：OK，形状一致即可
// Java：编译错误——nominal typing，没有继承/实现关系不能赋值
```

对读源码的影响：

- 参数要什么，答案是一个形状，不是一串实现类；不需要沿 implements/extends 找族谱。
- `implements` 只是显式请求编译器检查，不是赋值合法的前提；大量对象字面量根本不写 implements。
- Java 的"面向接口 + DI 容器"在 TS 里通常坍缩为"传一个形状相符的字面量"。

## 11.【必须掌握】类型完全擦除：运行时没有类型

模型一的直接推论，也是 LLM 相关代码写法的决定性背景：

```ts
interface User { name: string; }
const raw = '{"name": 42}';

const u = JSON.parse(raw) as User;   // 运行时零检查：name 其实是 42
u.name.toUpperCase();                // 编译通过，运行时才炸

if (x instanceof User) { }           // 编译错误：User 运行时不存在
if (x instanceof Array) { }          // 只能用 JS 自带的运行时判别手段
```

- 没有反射，没有 `getClass()`；连 `instanceof Promise<string>` 这种写法都不存在。
- 运行时校验必须手写（`typeof`/`in`/比较 tag 字段），或用 zod 这类库——schema 同时是校验器和类型来源【看懂即可，用到再学】。
- 对照 Java：泛型虽擦除但 `Class` 对象、字段、注解保留，所以 Jackson 能反射反序列化；TS 什么都没保留，`JSON.parse` 返回 `any`。这正是 LLM API 响应解析代码里到处是手写判别的原因（第 22 节）。

## 12. union 与 intersection

```ts
type FinishReason = "stop" | "length" | "tool_calls";     // union：合法值集合
type ConfiguredTool = BaseTool & { config: ToolConfig };  // intersection：同时满足两侧
```

union ≈ 不需要继承体系的多态取值集合，是 TS 建模的主力；intersection 少得多，常见于给已有类型叠字段（mixin 风格）。

## 13. literal type 与 as const

字符串/数字/布尔字面量本身可以作为类型：

```ts
type Status = "success" | "error";
let a: Status = "success";       // 只能是这两个字符串之一

const s = "success";             // const 推断保持字面量类型："success"
let t = "success";               // let 推断拓宽为 string

const ROUTES = { list: "/tools", run: "/run" } as const;
// 类型固化为 { readonly list: "/tools"; readonly run: "/run" }
```

`as const` 把整个字面量的每个属性固化为 readonly + 最窄字面量类型。用途：命令表/路由表/配置表定义一次，其类型自动成为合法值集合，再配 `keyof` 派生 union（第 16 节）。这也是它取代 enum 的基础。

## 14. enum【看懂即可】

```ts
enum Role { System = "system", User = "user", Assistant = "assistant" }
```

会编译出一个运行时对象。现代项目普遍用 `type Role = "system" | "user" | "assistant"` 替代 enum（含 const enum），原因一句话：字面量 union 零运行时产物、序列化即字符串、与 as const/keyof 无缝衔接，而 enum 生成运行时对象、const enum 在单文件转译（isolatedModules/esbuild）下不可靠。读老代码认得 enum 即可。

## 15. 泛型：调用点推断的编译期 duck typing

```ts
function first<T>(xs: T[]): T | undefined { return xs[0]; }

// extends 是约束（≈ Java 的 <K extends ...>），但右边可以是任意形状
function getConfig<K extends keyof AppConfig>(key: K): AppConfig[K] { /* ... */ }

first(["a", "b"]);   // T 在调用点推断为 string，无需显式写 <string>
```

对比 Java：Java 泛型是名义体系内的参数化，约束靠显式声明；TS 泛型基于结构化类型，T 不需要预先声明任何关系，编译器在调用点按实际形状推断——效果上更像"每个调用点自动做一次编译期 duck typing"。读源码时把 `<T>` 读作"此处的类型由使用处决定"即可，读懂签名比会写重要。

## 16. keyof / typeof / indexed access：源码高频三件套

```ts
const config = { model: "gpt-5", retries: 3 };   // 值

type Config = typeof config;         // 从值取类型：{ model: string; retries: number }
type ConfigKey = keyof Config;       // "model" | "retries"：类型的字段名 union
type RetryType = Config["retries"];  // number：indexed access，按 key 切出字段类型
```

`typeof config` 极高频：一处默认配置/注册表字面量让全项目共享其类型，改值类型自动跟着变。对比 Java：类型只能来自声明，"从值反推类型"不存在。`T["foo"]`、`T[K]` 用于从大类型上切局部类型，读工具函数签名时常见。

## 17. 常用 utility types

全部是纯类型层变换，擦除后消失。认出用途即可，不必背全量：

```ts
type Patch = Partial<Config>;                 // 全字段变可选 → 覆盖/更新场景
type ToolSummary = Pick<Tool, "name">;        // 挑字段 → 提取公共子集
type PublicTool = Omit<Tool, "run">;          // 去字段 → 隐藏内部实现
type Registry = Record<string, ToolHandler>;  // 字典类型 → 注册表/路由表

async function load(): Promise<{ data: string }> { /* ... */ }
type R = ReturnType<typeof load>;             // Promise<{ data: string }>
type D = Awaited<ReturnType<typeof load>>;    // { data: string }：unwrap Promise
```

`ReturnType<typeof fn>` + `Awaited` 的组合让你不 import 类型也能引用某工厂函数产物的类型，源码里非常常见（Promise 的运行时调度归第 04 章，这里只涉及类型层的 unwrap）。

## 18. type assertion（as）：说服编译器，不是转换

```ts
const data = JSON.parse(text) as ChatResponse;  // 编译期视角切换，运行时零动作
const s = x as unknown as string;               // 双重断言：绕过一切检查
```

与 Java 强转的根本区别：Java 转换失败抛 `ClassCastException`，是运行时检查；`as` 运行时什么都不做，错了照样错，只是编译器闭嘴。`as unknown as X` 出现处 = 作者放弃类型安全，读代码时标记为人工审查区。

## 19. satisfies：既检查又保留推断

现代 TS（4.9+）用它取代"给对象字面量写类型标注"，config/注册表定义的标配：

```ts
import { promises as fs } from "node:fs";

const tools = {
  readFile: (path: string) => fs.readFile(path, "utf-8"),  // Promise<string>
  listDir:  (dir: string)  => fs.readdir(dir),             // Promise<string[]>
} satisfies Record<string, (arg: string) => Promise<unknown>>;

// 检查：任一字段不符合"收 string、返回 Promise"的形状 → 编译报错
// 保留：tools 仍精确推断为 { readFile: (path: string) => Promise<string>; … }
```

对比写标注 `const tools: Record<string, …> = {…}`：检查同样发生，但类型被拓宽为宽泛 Record，`tools.readFile` 的精确签名丢失。satisfies = 校验形状 + 保留最窄推断，常与 `as const` 组合出现。

## 20. unknown / any / never / void

```ts
const parsed: unknown = JSON.parse(raw);  // unknown：类型安全的 any
parsed.foo;                               // 编译错误：必须先 narrow 才能用

const x: any = JSON.parse(raw);           // any：逃生舱
x.foo.bar.baz;                            // 编译通过且结果仍是 any——会传染

function fail(msg: string): never { throw new Error(msg); }  // never：永不正常返回
function log(msg: string): void { console.log(msg); }        // void ≈ Java void
```

- `unknown`：外部数据边界（JSON、stdin、LLM 响应）的正确标注，强迫调用方 narrow。
- `any`：放弃检查且传染——与 any 运算的结果也是 any；满屏 any 的模块 = 类型安全局部失效区。
- `never`：空类型，没有值属于它；主要用途是 exhaustive check（下一节）。
- `void`：与 Java void 语义近似，知道即可。

## 21. type narrowing：类型的控制流分析

编译器沿控制流收窄类型："当前变量的类型"取决于执行到了哪条路径：

```ts
function handle(x: string | number) {
  if (typeof x === "string") {
    x.toUpperCase();        // 此分支 x: string
  }
  x.toUpperCase();          // 编译错误：此处回到 string | number
}

if ("tool_calls" in msg) { /* msg 收窄为含该字段的分支 */ }
if (err instanceof ApiError) { /* err 收窄为 ApiError */ }

// 自定义 type guard：返回布尔 + 向编译器声明 narrowing 效果
function isToolCall(m: Message): m is ToolCall {
  return typeof m === "object" && m !== null && "tool" in m;
}
if (isToolCall(msg)) { /* msg: ToolCall */ }
```

`typeof`/`instanceof`/`in` 都是 JS 自带运算符，TS 只是利用其语义做类型收窄；早返回、三元、switch 同样触发。手写运行时判别（第 11 节）与 narrowing 是同一件事的两面：判别代码写出来，类型跟着收窄。

## 22.【必须掌握】discriminated union + exhaustive switch

现代 TS 项目最核心的建模手法。为什么大量出现这种代码：

```ts
type Result =
  | { type: "success"; value: string }
  | { type: "error"; error: Error };
```

TS 没有 ADT / sealed class。要同时拿到 (a) 运行时能区分变体、(b) 编译期穷尽性检查，手段就是：object 的 union + 一个公共字面量字段当 tag（判别字段 discriminant）。

```
 { type: "success", value: … } ──┐
                                  ├──▶  switch (r.type)：运行时按 tag 分发
 { type: "error",  error: … }  ──┘           +
                                             never 检查：编译期穷尽性
 tag 是"值"：擦除后仍然存在         结构差异是"类型"：编译期检查用
 两者配合，在动态 JS 之上拼出 sealed class 的完整语义
```

运行时侧：`r.type` 是普通字段访问，不受类型擦除影响——恰好补上第 11 节"类型不可运行时判别"的缺口。编译期侧：switch 命中某分支时 `r` 自动收窄为该变体；漏处理某个变体时，它的类型流进 default，赋给 `never` 报错：

```ts
type SSEEvent =
  | { type: "message_start"; message: Message }
  | { type: "content_block_delta"; delta: string }
  | { type: "message_stop" };

function render(e: SSEEvent): string {
  switch (e.type) {
    case "message_start":       return e.message.role;   // e 收窄：有 message
    case "content_block_delta": return e.delta;          // e 收窄：有 delta
    default: {
      const unhandled: never = e;   // 若漏写 "message_stop"，此行编译报错
      throw new Error(`unhandled: ${JSON.stringify(unhandled)}`);
    }
  }
}
```

default 的检查通常封装成一行 helper：

```ts
function assertNever(x: never): never {
  throw new Error(`Unhandled variant: ${JSON.stringify(x)}`);
}
// 用法：default: assertNever(e)
```

对照你熟悉的栈：

- Java 17+：sealed interface + switch pattern matching 是语言级等价物（穷尽性 + 收窄内建）；TS 没有语言级支持，靠"字面量 union + never 检查"手工拼出同等保证，纯类型层实现。
- Python：手写 `{"type": "error", ...}` tag dict 最常见，但穷尽性完全没保障——漏分支只在运行时 KeyError 或漏测时暴露；mypy 的 Literal 检查强度远不及。

天然应用场景（Coding Agent 源码里到处都是）：LLM API 的 `finish_reason`、工具调用成功/失败结果、SSE 流事件（`message_start` / `content_block_delta` / `message_stop`）、agent 状态机状态流转。共性：变体有限且已知、各变体字段不同、漏处理一个就是 bug。

## 23. tsconfig 一句话认知【看懂即可】

`tsconfig.json` 是类型检查/编译配置，现代项目默认 `strict` 全开：`null`/`undefined` 进入类型系统（`strictNullChecks`）、隐式 any 报错。源码里常见的 `!`（非空断言："我保证此处非 null"）和大量 `?.` 由此而来。读源码不必动配置，知道它决定了这些写法即可。

## 本章只记住这 5 件事

- TS 类型只活在编译期，产物 JS 里完全不存在；运行时判别只能靠值本身（tag 字段、typeof）。
- 结构化类型：按形状赋值不按类名，找参数要求时看形状，不必找继承链。
- object literal + union + 字面量类型是默认建模工具；class 和 enum 都退居配角。
- discriminated union（tag + switch + never）是 TS 版 sealed class，Agent 源码最高频模式。
- `typeof config` / `keyof` / utility types 让值驱动类型：改一处配置，全项目类型跟着变。
- 边界数据用 unknown + narrowing；`as` 是说服编译器，不是运行时转换。

## 源码识别

- 看到 `{ type: "success" } | { type: "error" }` → 想到 discriminated union，去找对应 switch 和 assertNever
- 看到 `default: assertNever(e)` → 想到穷尽性检查：新增变体时这里会编译报错
- 看到 `satisfies Record<…>` → 想到"校验形状但保留精确推断"的 config/注册表定义
- 看到 `keyof typeof CONFIG` → 想到从常量表生成合法 key union
- 看到 `x is Foo` 的布尔函数 → 想到自定义 type guard，调用后类型收窄
- 看到 `as unknown as X` → 想到类型安全被绕过，标记为人工审查区
- 看到 `??` 与 `||` 并存 → 想到 0/""/false 的语义差异，检查是否用错
- 看到 `#field` → 运行时真私有；看到 `private` → 编译期标注，擦除后可访问
- 看到 `msg.tool_calls?.[0]?.function` → optional chaining，短路到 undefined

## Java/Python 工程师常见误区

- 错误认知：`as` 相当于 Java 强转，转换失败会抛异常 → 实际运行时零动作，错了照样错。
- 错误认知：两个同字段的类不能互赋（Java nominal 直觉）→ 结构化类型下形状一致即可互赋。
- 错误认知：`JSON.parse(raw) as User` 之后数据就是 User → 类型擦除，运行时零校验，字段可能是任何值。
- 错误认知：看到 interface 就要找实现类 → 不需要 implements，形状相符的字面量直接传。
- 错误认知：`||` 适合做默认值 → 对 0/""/false 误伤，默认值场景应该用 `??`。
- 错误认知：enum 是常量集合的正规写法 → 现代主流是字面量 union + as const。

## 是否值得深入

- 结构化类型：当前阶段：建议掌握——读任何 TS 签名都在隐式使用它。
- discriminated union + assertNever：当前阶段：建议掌握——Agent 源码核心建模手法。
- utility types：当前阶段：建议掌握——认出常用几个即可，不必背全量。
- satisfies：当前阶段：建议掌握——认读新代码的标配写法，自己改 config 时直接用。
- 泛型高级技巧（条件类型 / infer / 映射类型）：当前阶段：不需要深入，读工具库时遇到再查。
- zod 与运行时校验：当前阶段：不需要深入，知道"必须手写或用库"，改到边界解析模块时再学。
- class 继承与 this 陷阱：当前阶段：不需要深入，现代源码以函数 + 对象为主。
- enum：当前阶段：不需要深入，认得即可。
