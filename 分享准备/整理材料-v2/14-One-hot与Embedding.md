# One-hot 与 Embedding

## 1. 解决的问题

把没有数值意义的 Token ID 转换为可学习的连续向量，使神经网络能够对 Token 表示进行计算。

---

## 2. One-hot

### 2.1 定义

**One-hot 是长度等于词表大小、只有目标位置为 1、其余位置为 0 的稀疏向量。**

如果词表大小为 $V$：

$$
o_t\in\mathbb R^V
$$

Token ID 只决定哪一维为 $1$。

### 2.2 能力边界

不同 Token 的 One-hot 向量彼此正交：

$$
o_i^\top o_j=0,\qquad i\ne j
$$

它只表示身份，不直接表示 Token 之间的语义相似性。

词表很大时，One-hot 也非常稀疏。

---

## 3. 核心机制：Embedding

### 3.1 定义

**Embedding 是从离散 Token ID 到可学习稠密向量的映射。**

Embedding 矩阵为：

$$
E\in\mathbb R^{V\times d}
$$

其中：

- $V$：词表大小。
- $d$：隐藏维度。

Token $t$ 的向量就是矩阵第 $t$ 行：

$$
x_t=E[t]
$$

### 3.2 与 One-hot 的关系

Embedding 查表等价于：

$$
x_t=o_t^\top E
$$

实际实现不需要显式创建巨大的 One-hot，而是直接读取对应行。

### 3.3 可学习性

Embedding 矩阵是模型参数。

训练时，反向传播会更新本批次使用到的 Token 向量，使它们逐渐形成有利于语言建模的表示。

### 3.4 序列表示

长度为 $T$ 的 Token 序列经过 Embedding 后变为：

$$
X\in\mathbb R^{T\times d}
$$

加入 Batch 维度后：

$$
X\in\mathbb R^{B\times T\times d}
$$

---

## 4. 静态 Token 表示与上下文化表示

输入 Embedding 中，同一个 Token ID 初始查到同一个向量。

经过 Transformer 后，同一个 Token 在不同上下文中会得到不同隐藏状态。

因此：

- Embedding 表示 Token 的初始可学习向量。
- Transformer 隐藏状态表示 Token 在当前上下文中的动态含义。

---

## 5. 输出层

最终隐藏状态 $h_t\in\mathbb R^d$ 需要映射到词表大小的 Logits：

$$
z_t=W_{\text{vocab}}h_t+b
$$

其中：

$$
W_{\text{vocab}}\in\mathbb R^{V\times d}
$$

Softmax 再把 $z_t$ 转换为下一个 Token 的模型概率分布。

有些模型让输出权重与输入 Embedding 共享：

$$
W_{\text{vocab}}=E
$$

这称为 Weight Tying。

---

## 6. 核心本质

**Embedding 用可学习矩阵把离散 Token 身份变成连续向量，Transformer 再把这些初始向量变成与上下文相关的表示。**
