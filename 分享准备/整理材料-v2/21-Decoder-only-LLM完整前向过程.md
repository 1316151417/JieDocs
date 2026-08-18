# Decoder-only LLM 完整前向过程

## 1. 解决的问题

把 Token ID 序列转换为每个位置的下一个 Token 概率分布，并将前面学过的分词、Embedding、Attention、Transformer Block 和交叉熵连接成一个完整模型。

---

## 2. 定义

**Decoder-only LLM 是由因果 Transformer Block 堆叠而成、按照从左到右方式预测下一个 Token 的语言模型。**

---

## 3. 核心机制：输入与前向过程

Token ID 张量：

$$
I\in\mathbb N^{B\times T}
$$

其中：

- $B$：Batch Size。
- $T$：序列长度。

---

## 4. Token Embedding

通过词表 Embedding 矩阵查表：

$$
X_0=E[I]
$$

得到：

$$
X_0\in\mathbb R^{B\times T\times d}
$$

位置信息通过位置 Embedding、RoPE 或其他方式注入。

---

## 5. Transformer Block 堆叠

对于第 $l$ 层：

$$
X_l
=
\operatorname{Block}_l(X_{l-1})
$$

每层包含：

1. 归一化。
2. 带 Causal Mask 的多头自注意力。
3. 残差连接。
4. 归一化。
5. FFN。
6. 残差连接。

经过 $L$ 层后：

$$
X_L\in\mathbb R^{B\times T\times d}
$$

每个位置的隐藏状态已经融合了该位置可见的上下文。

---

## 6. 最终归一化与词表输出层

先进行最终归一化：

$$
H=\operatorname{Norm}(X_L)
$$

再投影到词表：

$$
Z=HW_{\text{vocab}}^\top+b
$$

其中：

$$
Z\in\mathbb R^{B\times T\times V}
$$

$Z_{b,t,:}$ 是第 $b$ 个样本在位置 $t$ 对词表全部 Token 的 Logits。

---

## 7. 概率与预测

$$
P_{b,t,:}
=
\operatorname{Softmax}(Z_{b,t,:})
$$

这个分布预测位置 $t$ 之后的下一个 Token。

模型内部和训练损失通常直接使用 Logits，不需要提前显式计算完整 Softmax。

---

## 8. 训练损失

输入：

$$
[x_1,x_2,\ldots,x_{T-1}]
$$

目标：

$$
[x_2,x_3,\ldots,x_T]
$$

损失为：

$$
L
=
-\frac{1}{N_{\text{valid}}}
\sum_{b,t}
m_{b,t}
\log
p_\theta(x_{b,t+1}\mid x_{b,\le t})
$$

其中 $m_{b,t}$ 表示该位置是否参与损失。

---

## 9. 参数共享

- 同一个 Token Embedding 矩阵用于所有位置。
- 同一个 Transformer Block 内的参数用于所有序列位置。
- 不同 Block 通常有各自参数。
- 输入 Embedding 与输出词表权重可以共享。

---

## 10. 参数量从哪里来

### 10.1 Embedding

Token Embedding 参数量约为：

$$
Vd
$$

如果输出层不共享权重，还需要另一组近似 $Vd$ 的参数。

### 10.2 Attention

标准多头注意力中的 $W_Q$、$W_K$、$W_V$ 和 $W_O$ 合计约为：

$$
4d^2
$$

### 10.3 FFN

经典两层 FFN 参数量约为：

$$
2dd_{\text{ff}}
$$

门控 FFN 通常包含三次主要投影。

### 10.4 层数

Block 参数量随层数 $L$ 近似线性增长。

上下文长度 $T$ 不直接增加模型参数量，但会增加激活、Attention 计算和 KV Cache。

---

## 11. 训练与推理的区别

### 11.1 训练

已知整段真实序列，可并行计算全部位置的下一个 Token 损失。

### 11.2 推理

未来 Token 未知，只能：

1. 根据当前上下文预测下一个 Token。
2. 选择或采样一个 Token。
3. 将其追加到序列。
4. 重复执行。

---

## 12. 完整数据流

**文本 → Token IDs → Embedding → 多层因果 Transformer Block → 最终归一化 → 词表 Logits → Softmax/交叉熵或采样**

---

## 13. 核心本质

**Decoder-only LLM 用多层因果 Transformer 把已有 Token 上下文化，再为每个位置预测下一个 Token 的词表分布。**
