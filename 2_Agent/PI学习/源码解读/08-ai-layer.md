# 第 8 章 ai 包：模型统一层

> 本章回答：40+ 家模型厂商如何被收敛到一套消息/事件模型；流式归一化协议长什么样；鉴权、缓存、计费这三个"脏活"如何被组织。读完你应该能评估：给一个新厂商接进来要写多少代码。
>
> 主要文件：`ai/src/types.ts`（全部统一类型）、`models.ts`（Models/Provider/calculateCost）、`api/`（按 API 家族的适配器）、`providers/`（厂商工厂 + 生成的模型目录）、`auth/`。

## 8.1 三层结构：Models → Provider → API 适配器

先建立全局图。调用侧（Agent 的 streamFn）只认识 `Models.stream(model, context, options)`，它下面是三层：

```
Models（集合，models.ts）
  │  入口统一流程：normalizeContext → 查 provider → applyAuth → provider.stream
  ▼
Provider（厂商，providers/*.ts，41 个工厂）
  │  { id, baseUrl, auth, getModels(), stream: <按 model.api 分派> }
  ▼
API 适配器（api/*.ts，10 个家族）
  anthropic-messages / openai-completions / openai-responses /
  google / bedrock / mistral / …
  每个 export stream(model, context, options) —— 真正干翻译活的地方
```

**关键洞察：适配器按"API 家族"而不是"厂商"划分。** DeepSeek、Moonshot(Kimi)、OpenRouter、Groq…全都复用 `openai-completions` 适配器。厂商差异被压进每个模型的 `compat` 标志对象（openai-completions 家族有 30+ 个开关：`thinkingFormat` 11 种 reasoning 字段方言、`maxTokensField`、`requiresReasoningContentOnAssistantMessages`…），适配器读标志分支处理。

新增一个 OpenAI 兼容厂商的代价因此只有十几行：一个 provider 工厂 + 一段 JSON 模型目录。看 `providers/deepseek.ts` 的全部实质：

```ts
createProvider({
  id: "deepseek",
  baseUrl: "https://api.deepseek.com",
  auth: { apiKey: envApiKeyAuth("DeepSeek API key", ["DEEPSEEK_API_KEY"]) },
  models: Object.values(DEEPSEEK_MODELS),
  api: openAICompletionsApi(),      // ← 复用整个适配器
})
```

## 8.2 统一消息模型

`types.ts` 定义了四类消息（内核层已见过形状，这里补模型层视角）：

- **SystemMessage**：`content` + `sections`（命名段落）+ `toolsAdded/toolsRemoved`。多个 system 消息**按序回放**得到当前提示词与工具集——回放逻辑就在本包 `utils/transcript.ts`；
- **AssistantMessage**：`content: (TextContent | ThinkingContent | ToolCall)[]`，附 `api/provider/model/responseModel?/usage/stopReason/rawStopReason?/providerThinkingLevel?` 等。`responseModel` 与 `model` 不同时说明厂商做了服务端 fallback（计费要用前者对应的价目）；
- **ThinkingContent** 的 `thinkingSignature` 是 provider 不透明回放载荷（Anthropic 的加密签名 / OpenAI Responses 整个 reasoning item 的 JSON）——多轮对话中 reasoning 必须原样带回；
- **Usage**：`input/output/cacheRead/cacheWrite/cacheWrite1h?/reasoning?/totalTokens + cost{...}`。约定 `reasoning` 是 output 的子集。

`Context { systemPrompt?, messages, tools? }` 是公共入口形态，`normalizeContext()` 把 systemPrompt/tools **折叠为首条 system 消息**，产出带品牌符号类型的 `TranscriptContext`——类型系统保证未经归一化的裸 Context 不可能到达 provider。这是一个纯类型层面的防御，值得学：构造函数私有 + `declare const brand: unique symbol`。

## 8.3 流式归一化协议

所有厂商的流式响应收敛为一种事件（`AssistantMessageEvent`）：

```
start { partial }
text_start / text_delta / text_end          （contentIndex 定位）
thinking_start / thinking_delta / thinking_end
toolcall_start / toolcall_delta / toolcall_end
done   { reason: stop|length|toolUse|deferred, message }
error  { reason: aborted|error, error: AssistantMessage }
```

三条关键约定（不遵守会写出 bug）：

1. **`partial` 不是快照，是共享的可变对象**。provider 持续原地 mutate 它，每个事件都带着当前累计态；消费者靠 `contentIndex` 归属块，不能假设各块事件连续；
2. usage/cost 没有独立事件——provider 在拿到 usage 的时机直接更新 `partial.usage` 并就地调 `calculateCost`；
3. `done/error` 之前必有 `start`；失败也产出带 partial 内容的 AssistantMessage（第 6 章的"错误是数据"在模型层的起点）。

工具参数的流式解析用 partial-json：`toolcall_delta` 边流边解析，`toolcall_end` 时给出最终 `arguments` 对象。

### 两个代表适配器的映射（示意）

Anthropic（`api/anthropic-messages.ts`，自写 SSE 解码器）：

| 厂商事件 | 统一事件 |
|---|---|
| message_start | 记录 id/model/初始 usage（含 cache 读写）并计费 |
| content_block_start(text/thinking/tool_use) | text_start / thinking_start / toolcall_start |
| content_block_delta(text_delta/thinking_delta/input_json_delta) | 对应 *_delta |
| content_block_stop | 对应 *_end（toolcall 的 arguments 最终定稿） |
| message_delta | 映射 stopReason；更新 usage |

请求方向：连续 toolResult 合并为**一条 user 消息里的多个 tool_result 块**（Anthropic 要求 tool_result 紧跟 tool_use）；中途 system 消息挂起到下一条 assistant 前 flush。

OpenAI Responses（`api/openai-responses.ts`）：

- 核心是 `outputSlots: Map<outputIndex, slot>`——`response.output_item.added` 建 slot，各类 delta 事件归属到 slot，`output_item.done` 权威收尾（reasoning 的整个 item JSON 存入 thinkingSignature，实现无状态回放，配合 `store:false` + `reasoning.encrypted_content`）；
- stopReason 有个务实修正：状态是 stop 但 content 里有 toolCall → 改判 toolUse。

usage 归一化最能体现方言问题：**OpenAI 把缓存 token 计入 input**（要减掉），Anthropic 分列（直接用），DeepSeek 叫 `prompt_cache_hit_tokens`，Kimi 把 usage 放在 choice 里——`parseChunkUsage` 一个函数里处理全部方言，统一为 `input = prompt_tokens - cacheRead - cacheWrite`。

## 8.4 模型目录：生成管线

`Model` 类型携带：`id/name/api/provider/baseUrl/reasoning/thinkingLevelMap/input(模态)/cost/contextWindow/maxTokens/compat`。这些数据不是手维护的：

```
scripts/generate-models.ts（npm run generate-models，构建时强制运行）
  数据源：models.dev API（主源）+ OpenRouter + NVIDIA NIM + AI Gateway
    → 多源合并（models.dev 优先）
    → 人工勘误层（上下文窗口修正、价格锁定、排除表、thinkingLevelMap 推导）
    → 产出 src/providers/data/<provider>.json（带精确 JSON 类型）
    → <provider>.models.ts 薄壳（import json + flattenModelCatalog 泛型）
    → 汇总 src/models.generated.ts + .manifest.json（生成时间戳）
```

`thinkingLevelMap` 把 pi 的统一档位（minimal/low/medium/high/xhigh/max）映射到厂商原生档位，null 表示不支持该档——上层 `clampThinkingLevel` 据此就近降档。AGENTS.md 规定永远不要手改 `models.generated.ts`，改生成器再重新生成。

## 8.5 鉴权：凭证所有权模型

结构（`auth/` 目录）：

- `Credential = ApiKeyCredential | OAuthCredential`——"这就是 auth.json 的形状"，每 provider 一条，存 `~/.pi/auth.json`（0600 权限、proper-lockfile 锁，由 coding-agent 注入实现）；
- `CredentialStore.modify()` 是**唯一写路径**（串行化 read-modify-write，跨进程互斥）——OAuth 刷新必须发生在 modify 里，防止并发双重刷新；
- 解析优先级（`resolve.ts`，注释原文值得读）：

```
请求显式 apiKey
  > 存储凭证（OAuth → 双检锁刷新：剩余 <5min 才加锁，锁内复查，15s 超时；
             失败抛错保留旧凭证，绝不静默回退）
  > 环境变量（envApiKeyAuth(name, ["DEEPSEEK_API_KEY"]) 声明式注册，
             约 35 个厂商映射表）
```

核心原则一句话：**存储凭证独占 provider，无静默 env 回退**。这与第 2 章你问过的"到底用了 env 还是保存的 key"直接相关：保存过的凭证优先，环境变量只在无存储凭证时咨询；UI 里 `getAuth()` 的 `source` 字段会显示来源（"ANTHROPIC_API_KEY" / "OAuth" / "stored credential"）。

请求头的合并顺序固定：provider auth headers → model.headers → options.headers → transformHeaders，大小写不敏感、null 可删下层头。

## 8.6 Context Caching：两种厂商范式

统一偏好由 `StreamOptions.cacheRetention: "none"|"short"|"long"` 表达，适配器自行翻译：

- **Anthropic（显式断点型）**：三处插 `cache_control: {type:"ephemeral"}`——system 块、**最后一个工具定义**、**最后一条消息的最后一个内容块**。中途加载工具时用 `DEFERRED_TOOL_PLACEHOLDER` 占位保证前缀稳定（实测缺它全量 miss）；
- **OpenAI（自动缓存 + 路由键型）**：无断点，发 `prompt_cache_key = clamp(sessionId)`（64 字符上限）做会话亲和路由；
- usage 回读各不相同：`cache_read_input_tokens`（Anthropic）/ `cached_tokens`（OpenAI）/ `cachedContentTokenCount`（Google），全部归一为 `cacheRead`，且 OpenAI 系要从 input 里减掉。

会话亲和还体现为 header：anthropic 的 `x-session-affinity`、openai 系的 `session_id`——让同会话请求落同一缓存分片。

## 8.7 费用估算

`calculateCost(model, usage)`（`models.ts`）是唯一入口，规则：

```
inputTokens = input + cacheRead + cacheWrite        // 用于匹配价格档
按 tiers 的 inputTokensAbove 阈值取费率（长上下文分级计价）
cost 各项 = 费率/1e6 × 对应 token 数
cacheWrite 特殊：短写按 cacheWrite 费率，1h 长写按 2× input 费率（Anthropic 规则）
total = 四项之和
```

两个补充：服务端 fallback 时用 `allowedFallbackModels` 里的本地价目换 `responseModel` 计价；OpenAI 服务档位乘数（flex 0.5×、priority 2×）在响应处理里应用。UI 右下角 `$0.008` 就来自这里——**估算值**，实际计费以厂商账单为准。

## 8.8 值得带走的四个设计

1. **按 API 家族适配 + compat 标志收纳方言**：适配器数量 O(API 家族)，厂商数量 O(工厂行数)。你自己的 agent 项目接第三家厂商时若发现自己在 copy-paste 适配器，就该抽出家族层了；
2. **品牌类型守住归一化边界**：`TranscriptContext` 无法被手写构造，"忘了 normalize"这类错误在编译期消失；
3. **partial 作为共享可变对象**：反直觉但高效——避免了每个 delta 事件复制整条消息；代价是协议文档必须写清"不是快照"。权衡值得记住；
4. **凭证所有权 + 唯一写路径**：把并发安全（双检锁、串行化 modify）做进鉴权层而不是散在各调用点。

## 8.9 本章问题

1. 为什么 ThinkingContent 需要 signature 而文本不需要？如果丢掉 signature 会发生什么（分别在 Anthropic 和 OpenAI Responses 上）？
2. `cacheRead` 在 OpenAI 语义里为什么要从 input 中减掉？不减会导致什么显示错误（联系 UI 的 ↑输入 ↓输出 R缓存读）？
3. 给一个虚构的 "acme" 厂商（OpenAI 兼容、reasoning 字段叫 `thought`）接入：列出你要写的全部文件。如果它连 SSE 事件名都改了，答案变吗？

下一章：数据侧的第一站——会话如何落盘、如何分叉。
