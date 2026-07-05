
> 论文：**Switch Transformers: Scaling to Trillion Parameter Models with Simple and Efficient Sparsity**
>
> 作者：William Fedus、Barret Zoph、Noam Shazeer（Google）
>
> 时间：2021（JMLR 2022）

---

# 一、论文一句话总结

> **将 Transformer 中的 FFN 替换为 MoE（Mixture of Experts），并将传统 Top-2 Routing 简化为 Top-1 Routing，在几乎不增加每个 Token 计算量的情况下，大幅增加模型参数量，实现更高效的大模型 Scaling。**

一句话理解：

> **Dense Transformer：所有 Token 使用同一套 FFN。**
>
> **Switch Transformer：每个 Token 根据 Router，只激活一个 FFN Expert。**

---

# 二、论文背景

近年来，大模型能力不断提升：

```
GPT
↓

模型越来越大

↓

效果越来越好
```

但 Dense Transformer 有一个问题：

```
参数 ↑

↓

计算量 ↑

↓

训练成本 ↑
```

作者提出一个新的扩展方向：

> **能不能增加模型参数，而计算量几乎不增加？**

答案就是：

> **MoE（Mixture of Experts）**

---

# 三、核心创新

## 创新一：Transformer 引入 MoE

普通 Transformer：

```
Self-Attention

↓

FFN
```

Switch Transformer：

```
Self-Attention

↓

Router

↓

多个 FFN Expert

↓

选择一个 Expert
```

即：

```
一个 Token

↓

Router

↓

Expert 17

↓

输出
```

而不是：

```
一个 Token

↓

所有 FFN
```

因此：

```
总参数很多

但是

每次 Forward 只计算一个 Expert
```

---

## 创新二：Top-2 Routing → Top-1 Routing（最大创新）

之前的 MoE：

```
Token

↓

Expert A
Expert B

↓

加权求和
```

Switch：

```
Token

↓

Expert A

↓

结束
```

即：

```
Top-2

↓

Top-1
```

论文发现：

- 效果几乎不下降
- Router 更简单
- 通信减少
- 训练更稳定
- 推理更快

这是整篇论文最大的创新。

---

## 创新三：参数增加，但计算基本不增加

假设：

Dense：

```
1 个 FFN
```

Switch：

```
64 个 FFN Expert
```

但是：

```
一个 Token

↓

只计算其中 1 个
```

因此：

```
参数

64×

计算

≈1×
```

实现：

```
Parameter Scaling

≠

Compute Scaling
```

---

# 四、Switch Layer 工作流程

```
Token

↓

Router（Linear + Softmax）

↓

计算所有 Expert 概率

↓

选择最大的 Expert

↓

发送过去

↓

Expert 输出

↓

乘 Gate Value

↓

返回 Transformer
```

数学表达：

```
Router(x)

↓

Softmax

↓

argmax

↓

Expert(x)

↓

Gate × Output
```

---

# 五、为什么需要 Router

如果没有 Router：

```
随机选 Expert
```

不同 Expert 学不到专业能力。

Router 的作用：

> **学习哪个 Token 应该交给哪个 Expert。**

例如：

```
数学

↓

Expert 8

代码

↓

Expert 21

英文

↓

Expert 3
```

虽然论文没有监督这些能力，但训练过程中会自然形成一定程度的专家分工。

---

# 六、负载均衡（Load Balancing）

最大的工程问题：

```
所有 Token

↓

Expert 1
```

其它 Expert：

```
闲置
```

因此需要：

```
Auxiliary Loss
```

目标：

```
所有 Expert

处理 Token 数量

尽量均衡
```

论文增加：

```
Load Balance Loss
```

保证：

```
每个 Expert

≈

1/N Token
```

否则：

```
训练失衡

↓

性能下降
```

---

# 七、Expert Capacity

每个 Expert 都有容量限制：

```
Capacity

=

Tokens / Experts

×

Capacity Factor
```

例如：

```
Batch

6400

Expert

64

Capacity Factor

1.25
```

则：

```
100 ×1.25

=

125 Token
```

超过：

```
125

↓

Overflow

↓

Token Drop
```

论文发现：

```
Capacity Factor

≈1~1.25

效果最好
```

---

# 八、训练稳定性优化

论文提出三项技巧：

## 1、Router 使用 Float32

其它部分：

```
bfloat16
```

Router：

```
float32
```

这样：

```
速度

≈

bfloat16

稳定性

≈

float32
```

---

## 2、更小初始化

初始化：

```
Scale

1.0

↓

0.1
```

效果：

- 更稳定
- 更少训练崩溃
- 更低方差

---

## 3、Expert Dropout

Fine-tuning 时：

普通 Layer：

```
Dropout

0.1
```

Expert：

```
Dropout

0.4
```

减少过拟合。

---

# 九、实验结果

论文最重要结果：

## 1、训练速度

Switch-Base（64 Experts）

达到同样效果：

```
T5-Base

约 1/7 时间
```

即：

> **约 7× 预训练速度提升。**

---

## 2、Scaling 更优秀

增加 Expert：

```
2

↓

4

↓

8

↓

16

↓

32

↓

64

↓

128

↓

256
```

参数越来越大：

```
Loss

持续下降
```

证明：

> **MoE 是一种有效的 Scaling 方向。**

---

## 3、甚至超过更大的 Dense Model

论文比较：

```
Switch-Base

VS

T5-Large
```

结果：

Switch：

- 更快
- Sample Efficiency 更高

即使：

```
T5-Large

FLOPs

≈3.5×

Switch
```

依然：

```
Switch

≈2.5×

速度优势
```

---

## 4、多语言任务

论文：

```
101 Languages
```

相比：

```
mT5
```

几乎全部语言：

```
提升
```

说明：

MoE 很适合：

- 多语言
- 多任务

---

## 5、蒸馏

论文还验证：

```
Sparse Teacher

↓

Dense Student
```

能够：

```
减少

≈99%

参数

保留

≈30%

收益
```

---

# 十、论文贡献

真正贡献不是提出 MoE。

MoE：

2017 年已经有。

真正贡献：

> **证明 MoE 可以真正用于超大规模 Transformer。**

主要贡献：

- Top-1 Routing
- 更简单 Router
- 更稳定训练
- 更快训练
- 万亿参数可训练

推动：

```
MoE

↓

真正进入工业界
```

---

# 十一、局限

论文也存在不足：

## 1、通信成本

Token：

```
GPU1

↓

GPU7

↓

GPU2
```

大量跨卡通信。

---

## 2、Router 易失衡

如果：

```
Router

↓

全部选择一个 Expert
```

效果很差。

因此：

需要：

```
Load Balance Loss
```

---

## 3、部署复杂

Dense：

```
Forward
```

即可。

MoE：

```
Dispatch

↓

通信

↓

Expert

↓

Gather
```

工程复杂很多。

---

## 4、收益不是无限

参数增加：

```
并不会

无限提升效果
```

后续：

- 数据
- Token 数
- Router

都会成为瓶颈。

---

# 十二、与现代 LLM 的关系

Switch 是现代 MoE 的起点之一。

影响了：

- GLaM
- Mixtral
- DeepSeek MoE
- DeepSeek V2
- DeepSeek V3
- Qwen MoE

现代模型：

虽然很多重新使用：

```
Top-2
```

但核心思想一致：

```
大量 Expert

↓

每个 Token

↓

少量激活
```

---

# 十三、回答我的问题

## Q1：MoE、Switch Transformer 实际效果怎么样？

结论：

**非常成功。**

已经成为现代大模型的重要路线之一。

代表模型：

- Mixtral
- DeepSeek-V2
- DeepSeek-V3
- Qwen MoE

优势：

- 更高参数容量
- 更低 FLOPs
- 更好的 Scaling

缺点：

- 通信复杂
- Router 难训练
- 部署复杂
- 小模型收益有限

---

## Q2：T5 是什么？为什么和它对比？

T5（Text-To-Text Transfer Transformer）：

Google 于 2019 年提出的 Encoder-Decoder Transformer，是当时最强、最成熟的通用 NLP 基线之一。

Switch Transformer：

并没有重新设计 Transformer。

只是：

```
T5

↓

FFN

↓

Switch FFN
```

其它：

- Attention
- LayerNorm
- Embedding

全部保持一致。

因此：

论文能够证明：

> **性能提升来自 Switch Layer，而不是其它改动。**

---

# 十四、核心总结

一句话理解 Switch Transformer：

> **Dense Transformer 扩展模型，需要增加全部计算。**

> **Switch Transformer 扩展模型，只增加 Expert 数量，每个 Token 仍然只计算一个 Expert，因此实现了“参数量增长远快于计算量增长”的高效 Scaling。**

它证明了：

> **模型容量（Parameter Count）可以独立于计算量（FLOPs）进行扩展，这是现代 MoE 大模型发展的重要基础。**