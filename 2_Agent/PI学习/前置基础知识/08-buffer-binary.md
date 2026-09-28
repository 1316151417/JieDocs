# Buffer 与二进制：能读懂即可

> 定位：本章 10 分钟速读。目标只有一个——读源码时认出 Buffer 相关代码、分清字节数与字符数、对流式 chunk 的类型不再意外。不要求写二进制解析代码。

## 8.1 为什么需要 Buffer

JS 的 string 是 UTF-16 抽象：下标是 code unit，不是字节，背后也没有"原始内存"。而网络 socket、文件、加密与压缩 API 面对的全是字节。Node 用 Buffer 表示一段定长原始字节，并附带编码转换的便捷方法。一句话对照：Buffer ≈ Java 的 `byte[]` + `Charset` 工具方法的合体（或 ByteBuffer 的简化版），≈ Python 的 `bytes`。

```text
        string 世界                        字节世界
"hello 世界"  ── Buffer.from(s, "utf8") ──►  <Buffer 68 65 6c ...>
  （UTF-16 code unit）                    （原始字节，定长）
              ◄──── toString("utf8") ────
```

Buffer 是全局对象，免 import（现代代码也常写 `import { Buffer } from "node:buffer"`，同一个东西，见到不要困惑）。

## 8.2 Buffer 与 Uint8Array 的关系【看懂即可】

Buffer 是 Uint8Array 的子类：`Buffer.from("x") instanceof Uint8Array` 为 true，任何接受 Uint8Array 的 API（fetch body、WebCrypto）都能直接传 Buffer。关系链一句话：ArrayBuffer 是内存块 → TypedArray / Uint8Array 是它的类型化视图 → Buffer 是 Node 加了编码方法的 Uint8Array 子类。

| 概念 | Java | Python | 备注 |
|---|---|---|---|
| ArrayBuffer | ByteBuffer 背后的内存 | memoryview 指向的块 | 业务源码几乎不直接出现 |
| Uint8Array | byte[]（视图意义） | bytes（只读语义） | Web API 的通用参数类型 |
| Buffer | byte[] + Charset 便捷方法 | bytes | Node I/O 的通用货币 |

## 8.3 源码里最常见的三个方法【必须掌握】

```ts
const buf = Buffer.from("hello 世界", "utf8");   // string → 字节（encoding 缺省 utf8）
const s = buf.toString("utf8");                  // 字节 → string
buf.length;                                      // 字节数
Buffer.byteLength(s);                            // 不构造 Buffer，只数字节
```

encoding 实际会遇到的就三个：utf8（缺省）、hex、base64。API key / token 处理的固定套路：

```ts
const basic = "Basic " + Buffer.from(`${user}:${pass}`).toString("base64");  // HTTP 头
const token = Buffer.from(b64, "base64").toString("utf8");                   // round-trip
const digest = createHash("sha256").update(body).digest();   // Buffer
const hex = digest.toString("hex");                          // 哈希摘要的最终形态
```

### 字节数 vs 字符数：高频坑

```text
"aé界"                  3 个字符
string 下标:  [0]=a   [1]=é   [2]=界      →  "aé界".length === 3
UTF-8 字节:   a(1)   é(2)   界(3)         →  Buffer.byteLength("aé界") === 6

"😀".length === 2     ← 代理对占两个 code unit；UTF-8 里则是 4 字节
```

```ts
const s = "aé界";
s.length;                  // 3 —— UTF-16 code unit 数
Buffer.from(s).length;     // 6 —— Buffer.length 永远是字节数
```

什么时候咬人：按字节预算截断输入（`buf.subarray(0, 100)` 可能切在多字节字符中间，toString 出乱码）；按 `s.length` 估算 token / 流量；把 chunk 的 `length` 当字符数用。

### 源码里 Buffer 从哪来

读 Agent / CLI 源码时，Buffer 几乎总是从这几个入口出现——它们是"这里在处理二进制"的信号：

```ts
const data: Buffer = await readFile(p);                // 第 05 章：readFile 不传 encoding
const hash: Buffer = createHash("sha256").digest();    // crypto 摘要
spawn("git", [...]).stdout;                            // 子进程输出流，chunk 是 Buffer
resp.arrayBuffer();                                    // fetch 响应体（再包一层 Buffer/Uint8Array）
```

`buf.subarray(start, end)` 返回零拷贝视图（不复制内存，改视图会影响原 Buffer）【看懂即可】；需要独立副本用 `Buffer.from(buf)`。

## 8.4 stream 的 chunk 默认是 Buffer

流式读文件时，`on("data")` 给你的每个 chunk 默认是 Buffer（流的机制见第 07 章）。要得到完整文本，正确姿势是攒 Buffer、最后一次性解码：

```ts
// 有隐患：多字节字符可能正好被 chunk 边界切开，逐段解码再拼接会得到乱码
rs.on("data", (c: Buffer) => parts.push(c.toString("utf8")));

// 正确：拼接字节，最后一次解码
const chunks: Buffer[] = [];
rs.on("data", (c: Buffer) => chunks.push(c));
rs.on("end", () => { const text = Buffer.concat(chunks).toString("utf8"); });
```

或者 `rs.setEncoding("utf8")` 让流替你安全解码，按行处理用 readline——细节都归第 07 章。一句话记住：**攒 Buffer 再 concat，不要逐 chunk toString**。

## 8.5 暂时跳过的近亲【暂时跳过】

- `Buffer.alloc(n)`（零填充，安全）/ `Buffer.allocUnsafe(n)`（复用内部池，快但含旧数据）：看到 allocUnsafe 知道是性能敏感路径即可。
- `Blob`（Node 18+ 全局）：不可变二进制 + MIME 类型，出现在 fetch / FormData 系 API，认得即可。

## 本章只记住这 5 件事

1. Buffer = 原始字节（≈ byte[] / bytes），是 string 与字节世界之间的桥：`Buffer.from` / `toString("utf8")`。
2. `buf.length` 是字节数，`s.length` 是 code unit 数——含中文 / emoji 时两者必不相等。
3. encoding 见面最多的是 utf8 / hex / base64；base64 常见于 API key 与 HTTP 头。
4. stream 的 chunk 默认是 Buffer；拼文本用 `Buffer.concat` 后一次解码。
5. Buffer 是 Uint8Array 子类，能塞进任何要 Uint8Array 的 API。

## 源码识别

- 看到 `Buffer.from(x)` → 字符串转字节或包装数据，看第二参 encoding
- 看到 `.toString("base64" / "hex")` → token / API key / 摘要的处理
- 看到 `chunk.length` → 字节数，不是字符数
- 看到 `Buffer.concat(chunks)` → 流式收集后统一解码（正确姿势）
- 看到 `Buffer.byteLength(s)` → 在做字节预算 / 长度校验（对照 `s.length` 想一下差异）
- 看到 `Buffer.allocUnsafe` → 性能敏感路径的信号
- 看到 `new Blob(...)` → Web 风格二进制（fetch / FormData 生态）

## Java/Python 工程师常见误区

- 错误认知：`buf.length` 与 `s.length` 一样是字符数 → 实际：字节数；常用汉字 UTF-8 下每字 3 字节。
- 错误认知：逐 chunk `toString` 再字符串拼接没问题 → 实际：多字节字符可能被 chunk 边界切断，得到乱码。
- 错误认知：Buffer 与 TypedArray 是两套体系 → 实际：Buffer 是 Uint8Array 的子类，可互换使用。
- 错误认知：`"😀".length === 1` → 实际：2（代理对）；它的 UTF-8 长度是 4 字节。

## 是否值得深入

- from / toString / length / byteLength 与 base64 / hex：当前阶段：建议掌握——读 I/O 与 token 处理代码的最低配置。
- alloc / allocUnsafe / 内存池：当前阶段：不需要深入——性能细节，读到知道意图即可。
- Blob 与 Web Streams 互操作：当前阶段：不需要深入——fetch 生态专用，用到再查。
- ArrayBuffer / SharedArrayBuffer / Atomics：当前阶段：不需要深入——worker 与多线程场景才需要。
