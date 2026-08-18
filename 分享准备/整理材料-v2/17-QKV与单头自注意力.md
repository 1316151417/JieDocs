# QKV 与单头自注意力

## 1. 解决的问题

让序列中的每个位置根据当前需求，动态选择并汇总其他相关位置的信息。

---

## 2. 定义

**自注意力是由同一序列产生 Query、Key 和 Value，并根据 Query 与 Key 的匹配程度对 Value 加权汇总的机制。**

---

## 3. Q、K、V 的含义

对于每个位置的输入表示 $x_i$：

- Query：当前位置正在寻找什么信息。
- Key：当前位置可以用什么特征被其他位置匹配。
- Value：当前位置实际可以提供什么内容。

Q、K、V 不是人工定义的语义字段，而是通过训练学习出的不同线性投影。

---

## 4. 核心机制

令输入：

$$
X\in\mathbb R^{T\times d_{\text{model}}}
$$

### 4.1 线性投影

$$
Q=XW_Q
$$

$$
K=XW_K
$$

$$
V=XW_V
$$

其中：

$$
Q,K\in\mathbb R^{T\times d_k}
$$

$$
V\in\mathbb R^{T\times d_v}
$$

### 4.2 相关性分数

$$
S=QK^\top
$$

因此：

$$
S\in\mathbb R^{T\times T}
$$

$S_{ij}$ 表示位置 $i$ 的 Query 与位置 $j$ 的 Key 的匹配程度。

### 4.3 缩放

$$
\tilde S
=
\frac{QK^\top}{\sqrt{d_k}}
$$

当 $d_k$ 较大时，点积的尺度会变大，使 Softmax 过度饱和。

除以 $\sqrt{d_k}$ 可以控制分数尺度。

### 4.4 Softmax 权重

对每一行执行 Softmax：

$$
A
=
\operatorname{Softmax}
\left(
\frac{QK^\top}{\sqrt{d_k}}
\right)
$$

其中：

$$
\sum_j A_{ij}=1
$$

$A_{ij}$ 表示位置 $i$ 从位置 $j$ 读取信息的权重。

### 4.5 汇总 Value

$$
O=AV
$$

因此：

$$
O_i
=
\sum_jA_{ij}V_j
$$

每个输出位置都是全部可见 Value 的加权组合。

---

## 5. 完整公式

$$
\operatorname{Attention}(Q,K,V)
=
\operatorname{Softmax}
\left(
\frac{QK^\top}{\sqrt{d_k}}
\right)V
$$

对于 Self-Attention，Q、K、V 都来自同一个输入序列。

---

## 6. 为什么需要三个投影

如果直接使用同一个表示进行全部计算，匹配依据和被读取内容会被绑定在一起。

分别学习 Q、K、V，可以让模型：

- 用一种表示描述需求。
- 用另一种表示描述可匹配特征。
- 用第三种表示传递具体内容。

---

## 7. 核心本质

**自注意力用 Query 与 Key 决定“读哪里”，再按这些权重汇总 Value 决定“读什么”。**

