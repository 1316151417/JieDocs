# MQA 与 GQA 论文学习笔记

> 学习顺序：
>
> 1. Fast Transformer Decoding: One Write-Head is All You Need（MQA，2019）
> 2. GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints（GQA，2023）

---

| **缩写**  | **全称**                      | **中文**       | **核心含义**                     |
| ------- | --------------------------- | ------------ | ---------------------------- |
| **MHA** | **Multi-Head Attention**    | 多头注意力        | 每个 Query Head 都有自己的 K/V Head |
| **MQA** | **Multi-Query Attention**   | 多 Query 注意力  | 多个 Query Head，共享一组 K/V       |
| **GQA** | **Grouped-Query Attention** | 分组 Query 注意力 | 多个 Query Head 分组共享 K/V       |

# 一、为什么会出现 MQA/GQA？

## Transformer 推理真正的瓶颈

最开始大家认为：

> Transformer 推理慢，是因为 Attention 计算量太大。

后来发现真正瓶颈其实不是 FLOPs，而是：

> **KV Cache 的内存带宽（Memory Bandwidth）。**

LLM 推理（Decoder）流程：

```text
输入 token
      │
生成 Q
      │
读取所有历史 KV Cache
      │
Attention
      │
生成下一个 Token
```

每生成一个 Token：

- 都要重新读取所有历史 Key
- 都要重新读取所有历史 Value

随着上下文越来越长：

```text
KV Cache 越来越大
↓

GPU 显存读取越来越慢

↓

推理速度下降
```

所以：

> **推理阶段主要瓶颈不是计算，而是不断读取 KV Cache。**

---

# 二、Multi-Head Attention（MHA）

标准 Attention：

假设：

```text
d_model = 1024
num_heads = 8
head_dim = 128
```

则：

```text
Q:
8 ×128

K:
8 ×128

V:
8 ×128
```

对应投影矩阵：

```text
Wq:
1024 ×1024

Wk:
1024 ×1024

Wv:
1024 ×1024
```

KV Cache：

```text
batch × seq ×8×128
```

优点：

- 表达能力最强
- 每个 Head 都拥有独立记忆空间

缺点：

- KV Cache 最大
- 推理最慢

---

# 三、MQA（Multi-Query Attention）

论文：

> Fast Transformer Decoding:
> One Write-Head is All You Need

核心思想：

> **多个 Query Head，共享一组 Key/Value。**

即：

```text
Q:
8 个

K:
1 个

V:
1 个
```

而不是：

```text
8 个 Query

↓

8 个 K
```

而是：

```text
8 个 Query

↓

共享 1 个 K
```

---

## 实现方式

很多人误以为：

```text
Wk:

1024×1024

↓

1024×1024
```

实际上：

Wk、Wv 输出维度直接缩小：

普通：

```text
Wk:
1024 ×1024
```

MQA：

```text
Wk:
1024 ×128
```

同理：

```text
Wv:
1024 ×128
```

所以：

```text
KV Cache：

1024

↓

128
```

减少：

```text
8 倍
```

（一般来说减少 Head 数倍。）

---

## 为什么还能工作？

虽然：

```text
K

只有一份
```

但是：

```text
Query

仍然有多个
```

即：

```text
Head1

↓

Head2

↓

Head3

↓

同一个 K
```

每个 Head：

> 用不同 Query 去查询同一份历史记忆。

---

## 我的理解

> MQA 本质可以理解成：

> **Wk/Wv 的输出维度缩小了 Head 数倍。**

更准确地说：

> **因为所有 Head 共用 K/V，所以 Wk/Wv 可以缩小。**

而不是：

> 为了减少参数才缩小 Wk/Wv。

---

## 推理提升

KV Cache：

减少：

```text
Head 倍
```

例如：

```text
8 Heads

↓

KV Cache 减少约8倍
```

论文实验：

Decoder：

```text
46 μs/token

↓

3.8 μs/token
```

约：

```text
12 倍
```

Beam Search：

约：

```text
6 倍
```

---

## 训练提升

几乎没有。

原因：

训练：

```text
整个序列一次算完
```

KV Cache：

几乎不用反复读取。

因此：

MQA：

主要优化：

> **推理。**

---

## MQA 的缺点

所有 Head：

```text
共享一份 K/V
```

意味着：

不同 Head：

不能拥有独立记忆空间。

因此：

模型容量下降。

质量：

略下降。

训练：

容易不稳定。

---

# 四、GQA（Grouped Query Attention）

论文：

> GQA:
> Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints

一句话：

> **不是所有 Head 共用一组 K/V，而是分组共享。**

例如：

8 个 Head：

MQA：

```text
8

↓

1
```

GQA：

```text
8

↓

4
```

或者：

```text
8

↓

2
```

例如：

```text
Head1 Head2

↓

KV1

Head3 Head4

↓

KV2

Head5 Head6

↓

KV3

Head7 Head8

↓

KV4
```

---

# 五、MHA、MQA、GQA 对比

## MHA

```text
Q
8

K
8

V
8
```

速度：

最慢

质量：

最好

---

## MQA

```text
Q
8

K
1

V
1
```

速度：

最快

质量：

下降一点

---

## GQA

例如：

```text
Q
8

K
4

V
4
```

速度：

接近 MQA

质量：

接近 MHA

---

## 三者关系

```text
MHA

↓

GQA

↓

MQA
```

或者：

```text
num_key_value_heads

=

num_attention_heads

↓

...

↓

1
```

现代 LLM：

基本采用：

```text
1

<

num_key_value_heads

<

num_attention_heads
```

即：

> GQA。

---

# 六、为什么 GQA 更合理？

MQA：

压缩：

```text
64 Heads

↓

1 Head
```

过于激进。

GQA：

例如：

```text
64 Heads

↓

8 Heads
```

压缩：

```text
8 倍
```

质量：

明显更好。

速度：

几乎不变。

---

# 七、Uptraining（论文第二个贡献）

论文提出：

已有 MHA 模型：

不用重新训练。

步骤：

## 第一步

把多个 K/V：

做平均。

例如：

```text
K1

K2

K3

...

↓

Mean

↓

K_new
```

即：

```text
Mean Pooling
```

而不是：

随机初始化。

---

## 第二步

继续预训练：

约：

```text
5%
```

原始训练量。

效果：

几乎恢复质量。

10%：

提升已经不明显。

---

# 八、为什么 Mean Pooling？

论文比较：

```text
Mean

First

Random
```

结果：

```text
Mean

最好
```

原因：

Mean：

保留所有 Head 信息。

First：

只保留一个。

Random：

几乎全部丢失。

---

# 九、实验结论

论文：

T5 XXL：

| 模型 | 推理速度 | 质量 |
|------|----------|------|
| MHA | 最慢 | 最好 |
| MQA | 最快 | 略下降 |
| GQA | 接近 MQA | 接近 MHA |

GQA：

真正实现：

> **质量几乎不变。**

同时：

> **推理速度接近 MQA。**

---

# 十、为什么现代 LLM 全都选择 GQA？

因为：

MQA：

```text
速度最好

但是：

容量下降。

训练不稳定。

质量下降。
```

MHA：

```text
质量最好

但是：

KV Cache 太大。
```

GQA：

两边都兼顾。

因此：

LLaMA

Qwen

DeepSeek

Gemma

等现代模型：

基本都采用：

```text
GQA
```

---

# 十一、论文贡献总结

## MQA（2019）

贡献：

> 首次指出：

Transformer Decoder：

真正瓶颈：

不是计算。

而是：

> KV Cache 内存带宽。

创新：

> 所有 Head 共用一组 K/V。

结果：

- KV Cache 大幅减少
- 推理速度提升巨大
- 长上下文更友好

代价：

- 模型容量下降
- 质量略下降

---

## GQA（2023）

贡献：

提出：

> MHA 与 MQA 之间的连续形态。

即：

```text
多个 Query

↓

分组共享 K/V
```

创新：

- 保留更多表达能力
- 推理速度仍然很快
- 更稳定

并提出：

> Uptraining：

已有 MHA

↓

Mean Pooling

↓

继续训练 5%

↓

直接得到 GQA 模型。

无需重新训练。

---

# 十二、我的问题记录

## Q1

MQA 为什么内存减少？

一开始误区：

```text
8×128

=

1×1024
```

感觉：

内存一样。

后来理解：

MQA：

不是：

```text
1×1024
```

而是：

```text
1×128
```

Wk/Wv：

输出维度：

直接缩小：

```text
1024

↓

128
```

因此：

KV Cache：

真正减少：

Head 倍。

---

## Q2

MQA 是否可以理解为：

> Wk/Wv 投影矩阵缩小了 Head 倍？

答案：

**可以。**

但更准确：

> 因为所有 Head 共享 K/V，所以 Wk/Wv 才可以缩小。

不是：

为了减少参数。

---

## Q3

MQA：

推理：

减少什么？

答案：

主要减少：

> KV Cache。

而不是：

整个模型参数。

---

## Q4

MQA：

为什么训练提升不明显？

因为：

训练：

整个序列：

一次计算。

KV Cache：

不会像推理一样：

不断读取。

因此：

MQA：

几乎只优化：

推理阶段。

---

# 十三、一句话总结

> **MQA 的本质是：多个 Query Head 共享同一组 Key/Value，大幅减少 KV Cache，解决 Transformer 推理的内存带宽瓶颈；GQA 则进一步提出按组共享 K/V，在保持接近 MQA 推理速度的同时，大幅恢复模型表达能力，因此成为现代 LLM（LLaMA、Qwen、DeepSeek 等）的主流 Attention 结构。**