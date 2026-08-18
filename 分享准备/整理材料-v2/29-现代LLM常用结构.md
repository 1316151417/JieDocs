# 现代 LLM 常用结构

## 1. 解决的问题

在不改变 Decoder-only 自回归主线的前提下，提高训练稳定性、参数效率、长序列速度和推理效率。

---

## 2. 核心机制：RMSNorm

### 2.1 定义

**RMSNorm 是只根据均方根缩放隐藏向量、不减去均值的归一化方法。**

$$
\operatorname{RMS}(x)
=
\sqrt{
\frac{1}{d}\sum_{i=1}^{d}x_i^2+\epsilon
}
$$

$$
\operatorname{RMSNorm}(x)
=
g\odot
\frac{x}{\operatorname{RMS}(x)}
$$

其中 $g$ 是可学习缩放参数。

它比 LayerNorm 少了均值中心化步骤，常用于现代 Decoder LLM。

### 2.2 核心本质

**RMSNorm 通过控制隐藏向量的均方根尺度稳定深层训练。**

---

## 3. SwiGLU

### 3.1 定义

**SwiGLU 是使用两路线性投影和门控乘法构成的 Transformer FFN。**

可抽象写为：

$$
\operatorname{SwiGLU}(x)
=
\left[
\operatorname{SiLU}(xW_g)
\odot
(xW_u)
\right]W_d
$$

其中：

- $W_g$：门控投影。
- $W_u$：内容投影。
- $W_d$：降维投影。

### 3.2 核心本质

**SwiGLU 让一条特征分支动态控制另一条分支的信息通过程度。**

---

## 4. RoPE

RoPE 根据位置旋转 Query 和 Key，使注意力点积包含相对位置信息。

它通常应用在每层 Attention 中，是现代 Decoder LLM 常见的位置方案。

### 核心本质

**RoPE 把相对位置关系编码进 Query 与 Key 的点积。**

---

## 5. MHA、MQA 与 GQA

### 5.1 MHA

每个 Query 头都有独立的 Key 和 Value 头。

### 5.2 MQA

**Multi-Query Attention 让多个 Query 头共享同一组 Key 和 Value。**

它显著减少推理时 KV Cache 大小，但共享程度较高。

### 5.3 GQA

**Grouped-Query Attention 把多个 Query 头分组，每组共享一组 Key 和 Value。**

它处于 MHA 与 MQA 之间：

- 保留多个 KV 组。
- 减少 KV Cache。
- 兼顾模型能力和推理效率。

### 5.4 核心本质

**MQA/GQA 通过共享 Key 和 Value 头减少 KV Cache，而不减少 Query 头数量。**

---

## 6. FlashAttention

### 6.1 定义

**FlashAttention 是通过分块和面向 GPU 内存层次的计算顺序，减少 Attention 中间结果读写的精确实现。**

它仍然计算：

$$
\operatorname{Softmax}
\left(
\frac{QK^\top}{\sqrt{d_k}}
\right)V
$$

并没有把 Attention 的数学定义换成近似模型。

### 6.2 作用

- 避免把完整注意力矩阵反复写入高带宽显存。
- 降低实际显存占用。
- 提高训练和 Prefill 速度。

标准 Attention 的理论平方计算量仍然存在，只是实现更高效。

### 6.3 核心本质

**FlashAttention 不改变注意力结果，而是通过减少昂贵的显存读写提高实际速度。**

---

## 7. MoE

### 7.1 定义

**Mixture of Experts 是把 FFN 替换为多个专家网络，并由 Router 为每个 Token 选择少量专家参与计算的结构。**

设有多个专家：

$$
E_1(x),E_2(x),\ldots,E_M(x)
$$

Router 产生选择权重，只激活其中 Top-$k$ 个：

$$
y
=
\sum_{i\in\operatorname{TopK}(g(x))}
g_i(x)E_i(x)
$$

### 7.2 优点

总参数量可以很大，但每个 Token 只使用少数专家，因此单 Token 计算量低于同规模稠密模型。

### 7.3 代价

- 专家负载需要平衡。
- 跨设备路由产生通信。
- 总参数显存和部署复杂度仍然较高。
- 路由与训练稳定性更复杂。

### 7.4 核心本质

**MoE 用条件激活让模型拥有更多总参数，但每个 Token 只经过少量专家计算。**

---

## 8. 总结

|结构|主要解决的问题|
|---|---|
|RMSNorm|训练稳定性与简化归一化|
|SwiGLU|提高 FFN 表达与门控能力|
|RoPE|注入相对位置信息|
|GQA/MQA|减少 KV Cache|
|FlashAttention|减少 Attention 内存读写|
|MoE|扩大参数容量而控制单 Token 计算|

---

## 9. 核心本质

**现代 LLM 仍以因果 Transformer 为骨架，这些结构分别优化归一化、FFN、位置、KV Cache、Attention 实现和条件计算。**
