# RoFormer：Enhanced Transformer with Rotary Position Embedding（RoPE）学习笔记

> 论文：RoFormer: Enhanced Transformer with Rotary Position Embedding（2021）

---

# 一、论文一句话总结

RoFormer 最大的贡献**不是提出了一个新的 Transformer 架构**，而是提出了一种全新的位置编码方式 **RoPE（Rotary Position Embedding）**。

RoPE 将**位置编码从"加法(Add)"变成了"旋转(Rotate)"**，使得 Attention 在计算 `Q·K` 时天然携带**相对位置信息**，最终成为现代 LLM（LLaMA、Qwen、DeepSeek 等）的事实标准。

---

# 二、论文背景

Transformer 自注意力本身不知道 Token 顺序，因此必须加入位置编码。

主要有三种方案：

| 方法 | 思路 | 优缺点 |
|------|------|---------|
| Absolute Position | Embedding + Position | 简单，但表达相对位置能力弱 |
| Relative Position | 在 Attention 中加入距离信息 | 相对位置表达强，但实现复杂 |
| RoPE | 对 Query / Key 做旋转 | 简洁、高效、天然表达相对位置 |

---

# 三、论文核心创新

## 1、位置编码由"加法"变成"旋转"

传统：

```text
x' = x + p
```

RoPE：

```text
q = Rotate(Wq·x)

k = Rotate(Wk·x)
```

即：

先得到 Query、Key，再根据当前位置旋转对应角度。

---

## 2、Attention 天然得到相对位置

二维情况下：

```text
q = q · e^(imθ)

k = k · e^(inθ)
```

计算 Attention：

```text
q · k
```

最终会自动得到：

```text
e^(i(m-n)θ)
```

位置最终变成：

```text
m - n
```

即：

Attention 天然只依赖：

- Token 内容
- 相对距离

无需人为增加 Relative Position Bias。

---

## 3、高维推广

高维向量按两个维度一组：

```text
(x1,x2)

(x3,x4)

...

(xd-1,xd)
```

每组使用不同频率：

```text
θ_i = 10000^(-2i/d)
```

与 Transformer 正弦位置编码使用相同频率设计。

区别只是：

Transformer：

```text
Embedding + sin/cos
```

RoPE：

```text
Embedding × Rotation Matrix
```

---

# 四、RoPE 的优点

## 1、天然表达 Relative Position

这是最大的创新。

最终 Attention：

```text
Q·K
```

里面已经隐含：

```text
m-n
```

无需额外计算 Relative Position。

---

## 2、不增加可学习参数

RoPE：

没有 Position Embedding 表。

没有 Relative Bias。

全部由固定 sin/cos 构造。

参数量增加：

```text
0
```

---

## 3、保持向量长度

旋转矩阵属于正交矩阵：

```text
||Rotate(x)|| = ||x||
```

因此不会改变：

- 向量长度
- 数值尺度

训练更加稳定。

---

## 4、支持长距离衰减

论文证明：

随着：

```text
|m-n|
```

越来越大，

Attention 会自然减弱。

符合自然语言规律：

距离越远，

关联通常越弱。

---

## 5、适合 Linear Attention

传统 Relative Position：

很多不能直接用于：

- Performer
- Linear Transformer

RoPE：

由于只是旋转 Query / Key，

因此可以直接兼容各种 Linear Attention。

---

# 五、为什么现代 LLM 都选择 RoPE？

论文实验其实提升并不明显。

真正让 RoPE 成为标准的是：

## 1、Decoder-only LLM

论文：

主要验证：

- BERT
- 分类
- 翻译

最长：

```text
512 Token
```

RoPE 真正优势：

是在：

```text
8K

32K

128K

1M Context
```

时代才体现出来。

---

## 2、长上下文能力

Learned Position Embedding：

训练：

```text
2048
```

推理：

```text
4096
```

直接没有对应位置。

RoPE：

不存在 Position Table。

天然支持长度扩展。

后续又出现：

- NTK Scaling
- YaRN
- LongRoPE
- Dynamic NTK

都是基于 RoPE 演化。

---

## 3、KV Cache 非常自然

RoPE：

每个 Key：

```text
Rotate

↓

Cache
```

以后永远不用修改。

生成新的 Token：

```text
Rotate(Query)

↓

Q·K
```

即可。

Cache 无需重新计算。

---

传统 Relative Position：

Attention Score：

```text
QK

+

RelativeBias(distance)
```

每生成一个 Token：

所有距离都会变化。

需要重新：

- Lookup
- Bias
- Offset
- Index

工程复杂很多。

---

一句话：

RoPE 把位置信息提前固化到了 Query / Key 中。

Relative Position 是每次计算 Attention 时临时加入距离信息。

因此：

RoPE 更适合：

- KV Cache
- FlashAttention
- Decoder 推理
- 长上下文

最终成为现代 LLM 默认方案。

---

# 六、论文实验

论文实验整体提升并不大。

## WMT14 翻译

Transformer：

```text
27.3 BLEU
```

RoFormer：

```text
27.5 BLEU
```

提升：

```text
+0.2
```

---

## BERT 预训练

MLM Loss：

收敛更快。

---

## GLUE

部分任务提升。

部分下降。

整体属于：

小幅改进。

---

## 中文长文本

长文本任务优势更明显。

---

# 七、为什么论文影响却如此巨大？

因为：

真正重要的是：

> 提出了一个优秀的基础组件。

很多基础组件：

论文实验都不算惊艳。

例如：

| 技术 | 当年论文效果 | 后来影响 |
|------|-------------|-----------|
| Transformer | BLEU 小提升 | 改变整个 AI |
| GELU | 小提升 | GPT/BERT 标配 |
| RMSNorm | 小提升 | LLaMA 标配 |
| SwiGLU | 小提升 | 主流 LLM 标配 |
| RoPE | 小提升 | 几乎所有现代 LLM 标配 |

这些工作真正价值：

都是后来随着：

- 更大的模型
- 更长 Context
- 更高效推理

逐渐体现出来。

---

# 八、我的疑问

## 问题一

> 论文实验效果是不是并不好？

回答：

是。

论文本身：

属于小幅提升。

真正让 RoPE 成为标准的是：

后来的：

- GPT 类 Decoder-only 模型
- LLaMA
- 长上下文训练
- KV Cache
- FlashAttention

共同推动。

---

## 问题二

> 为什么很多 Relative Position 做不到像 RoPE 那么优雅？

核心区别：

Relative Position：

```text
每次 Attention

↓

重新计算距离

↓

加入 Bias
```

RoPE：

```text
第一次

↓

旋转 Query / Key

↓

以后 Attention 永远还是：

Q·K
```

因此：

RoPE 不需要：

- 重新计算距离
- 修改 Cache
- 修改 Attention Kernel

工程实现远比传统 Relative Position 简洁。

---

# 九、核心结论

> **RoPE 本质不是一种新的 Attention，而是一种新的位置编码方式。**

它最大的创新不是提升论文里的几个百分点，而是：

- 用旋转替代加法；
- 将绝对位置编码转化为 Attention 中天然的相对位置；
- 不增加参数；
- 与 KV Cache、FlashAttention、长上下文天然兼容；

最终成为现代 Decoder-only LLM（LLaMA、Qwen、DeepSeek、Gemma、Mistral 等）的事实标准。