
> 论文：**Root Mean Square Layer Normalization**
>
> 作者：Biao Zhang、Rico Sennrich（NeurIPS 2019）
>
> 定位：LayerNorm 的简化版，也是 LLaMA、Qwen、DeepSeek、Mistral 等现代 LLM 使用的标准归一化方法。 [oai_citation:0‡1910.07467v1.pdf](sediment://file_000000007b587206b175ef0982f594f5)

---

# 一、论文一句话总结

RMSNorm 的核心思想：

> **LayerNorm 真正重要的是"控制数值尺度（re-scaling）"，而不是"减均值（re-centering）"。**

因此：

去掉减均值，仅保留 RMS（Root Mean Square）缩放，就能获得几乎相同的训练效果，同时显著减少计算开销。 [oai_citation:1‡1910.07467v1.pdf](sediment://file_000000007b587206b175ef0982f594f5)

---

# 二、论文背景

2016 年 LayerNorm 被提出后，已经成为：

- Transformer
- RNN
- BERT
- GPT

等模型的标准组件。

LayerNorm 能：

- 稳定训练
- 加快收敛
- 防止激活值越来越大

但是作者发现：

LayerNorm 做了两件事情：

```
① 减均值（Re-centering）

② 除标准差（Re-scaling）
```

作者提出疑问：

> **真的两件事都重要吗？**

论文最终答案：

> **真正重要的是第二件。**

---

# 三、LayerNorm 与 RMSNorm

## LayerNorm

公式：

```
x'

=

(x-mean)

/ std
```

步骤：

1. 计算均值
2. 减均值
3. 计算标准差
4. 除标准差
5. 乘 gamma

特点：

> 去中心化 + 控制尺度

---

## RMSNorm

公式：

```
RMS(x)

=

sqrt(mean(x²))
```

归一化：

```
x'

=

x / RMS(x)
```

最后：

```
y

=

gamma * x'
```

特点：

> **只控制尺度，不减均值。**

---

# 四、论文核心创新点

---

## 创新一：提出 RMSNorm

这是论文最大的创新。

作者提出：

> LayerNorm 不需要减均值。

直接：

```
LayerNorm

↓

RMSNorm
```

整个结构变成：

```
只计算：

RMS

↓

缩放
```

而不是：

```
mean

↓

variance

↓

normalize
```

因此：

计算更简单。

---

## 创新二：提出新的假设

论文最重要的一句话：

> **LayerNorm 成功的原因主要来自 Re-scaling Invariance，而不是 Re-centering Invariance。**  [oai_citation:2‡1910.07467v1.pdf](sediment://file_000000007b587206b175ef0982f594f5)

也就是说：

真正让模型稳定的是：

```
控制数值大小
```

而不是：

```
把均值变成0
```

这是 RMSNorm 的理论基础。

---

## 创新三：证明只控制尺度已经足够

作者进行了大量实验：

包括：

- RNN
- Transformer
- CNN
- Reading Comprehension
- Image Retrieval

实验结论：

> RMSNorm 与 LayerNorm 的最终性能几乎一致。 [oai_citation:3‡1910.07467v1.pdf](sediment://file_000000007b587206b175ef0982f594f5)

说明：

控制 RMS

已经足够。

---

## 创新四：提出 pRMSNorm

论文还提出：

Partial RMSNorm

思想：

```
不是所有维度都计算 RMS

↓

随机抽一部分

↓

估计 RMS
```

例如：

```
hidden

4096维

↓

只计算前256维

↓

估计 RMS
```

理论上：

计算还能继续减少。

实验：

效果依旧不错。

不过：

现代 LLM 基本不用。

LLaMA 也没有采用。

---

# 五、论文解决什么问题？

## 问题一：

LayerNorm 太慢。

LayerNorm：

需要：

```
mean

variance

减法

平方

开方
```

RMSNorm：

只需要：

```
平方

平均

开方
```

因此：

减少大量计算。

---

## 问题二：

LayerNorm 是否做了没必要的事情？

作者认为：

```
减均值

↓

可能没有贡献。
```

因此：

删除。

如果：

```
效果

≈

LayerNorm
```

那么：

为什么还要计算？

---

## 问题三：

大模型越来越大。

Transformer：

几十层。

以后：

上百层。

每层都有：

LayerNorm。

所以：

哪怕：

每层节省一点。

整个模型：

都会节省很多。

---

# 六、为什么不减均值？

这是整篇论文最核心的问题。

作者认为：

神经网络真正需要的是：

```
控制：

激活值大小
```

而不是：

```
控制：

均值
```

举个例子：

```
[100

101

102]
```

LayerNorm：

```
↓

[-1

0

1]
```

RMSNorm：

```
↓

[0.99

1.00

1.01]
```

虽然不同。

但是：

下一层：

Linear

完全可以学习：

```
bias

↓

抵消均值
```

所以：

均值不是那么重要。

真正危险的是：

```
100

↓

1000

↓

100000
```

尺度失控。

因此：

只控制 RMS 即可。

---

# 七、论文实验结论

论文做了：

- Transformer
- RNN
- CNN
- QA
- Image Retrieval

几乎全部结论一致：

## 性能

```
LayerNorm

≈

RMSNorm
```

几乎一样。

---

## 速度

RMSNorm：

比 LayerNorm：

快：

```
7%

~

64%
```

不同模型不同。 [oai_citation:4‡1910.07467v1.pdf](sediment://file_000000007b587206b175ef0982f594f5)

---

## 收敛

收敛速度：

几乎一样。

甚至：

有时候：

RMSNorm 更稳定。

---

## Robustness

论文还有一个比较有意思的实验。

故意：

把初始化改坏。

结果：

LayerNorm

反而：

更容易崩。

RMSNorm：

表现更稳定。 [oai_citation:5‡1910.07467v1.pdf](sediment://file_000000007b587206b175ef0982f594f5)

这是论文一个比较意外的发现。

---

# 八、为什么现代 LLM 都采用 RMSNorm？

因为：

对于 LLM：

大家最关心：

```
推理成本
```

而：

实验发现：

```
效果

≈

LayerNorm
```

于是：

大家自然都会选择：

```
RMSNorm
```

因此：

LLaMA

↓

Qwen

↓

DeepSeek

↓

Mistral

↓

Gemma

几乎全部采用 RMSNorm。

---

# 九、我的几个问题（整理）

## Q1：RMSNorm 比 LayerNorm 效果好吗？

不是。

更准确地说：

```
LayerNorm

≈

RMSNorm
```

性能：

基本一致。

偶尔：

RMSNorm

略好。

偶尔：

LayerNorm

略好。

差距：

通常：

不到：

1%。

很多时候：

随机种子造成的波动都比这个更大。

---

## Q2：为什么去掉减均值还能工作？

因为：

Transformer 真正需要的是：

```
控制：

激活值尺度
```

而不是：

```
均值=0
```

均值偏一点：

Linear 可以自己学习。

尺度爆炸：

模型很难自己解决。

因此：

控制 RMS 已经足够。

---

## Q3：为什么现在几乎没人用 LayerNorm？

不是：

LayerNorm 不好。

而是：

```
效果：

一样

↓

计算：

更贵
```

所以：

RMSNorm 性价比更高。

---

## Q4：RMSNorm 是不是更先进？

不是。

它不是：

```
更强。
```

而是：

```
更简单。
```

属于：

工程优化。

---

# 十、优缺点

## 优点

### ① 计算更简单

少：

- mean
- subtraction

---

### ② 推理更快

现代 LLM：

每层都有 Norm。

因此：

收益很明显。

---

### ③ 训练稳定

能够控制：

激活值尺度。

---

### ④ 性能几乎没有损失

Benchmark：

几乎一致。

---

### ⑤ 成为现代 LLM 标配

目前：

- LLaMA
- Qwen
- DeepSeek
- Mistral
- Gemma

均采用 RMSNorm。

---

## 缺点

### ① 理论约束更少

没有：

```
mean=0
```

---

### ② 某些模型 LayerNorm 仍可能略好

例如：

部分 CNN。

---

### ③ 并不是提升模型能力

它：

不能提高：

模型上限。

只是：

降低计算。

---

# 十一、与 LayerNorm 对比

| 对比项 | LayerNorm | RMSNorm |
|---------|-----------|----------|
| 是否减均值 | ✅ | ❌ |
| 是否控制尺度 | ✅ | ✅ |
| 是否标准化方差 | ✅ | 间接控制 RMS |
| 理论约束 | 更完整 | 更简单 |
| 最终性能 | 几乎一致 | 几乎一致 |
| 训练稳定性 | 高 | 高 |
| 推理速度 | 较慢 | 更快 |
| 现代 LLM 使用 | GPT-3 等 | LLaMA、Qwen、DeepSeek 等 |

---

# 十二、核心结论（★★★★★）

RMSNorm 的最大贡献，并不是提出一种更强的归一化方法，而是证明了：

> **LayerNorm 中真正不可或缺的是"控制激活值尺度（re-scaling）"，而不是"减均值（re-centering）"。**

因此，它用一个更简单的公式，在几乎不损失模型性能的前提下，显著降低了训练与推理成本。

这使得 RMSNorm 成为现代开源大语言模型（LLaMA、Qwen、DeepSeek、Mistral 等）的事实标准归一化方案，也是 Transformer 工程优化中最成功的改进之一。