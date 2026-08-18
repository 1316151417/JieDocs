# Transformer Block

## 1. 解决的问题

把“跨位置交换信息”和“每个位置内部进行非线性变换”组合成可以稳定堆叠的深层网络基本单元。

---

## 2. 定义

**Transformer Block 是由注意力子层、前馈网络、残差连接和归一化组成的可重复堆叠模块。**

Decoder-only LLM 使用带 Causal Mask 的 Transformer Block。

---

## 3. 核心机制：Pre-Norm Block

令输入为：

$$
X\in\mathbb R^{B\times T\times d}
$$

### 3.1 注意力子层

$$
X'
=
X+
\operatorname{MHA}
\left(
\operatorname{Norm}(X)
\right)
$$

### 3.2 前馈子层

$$
Y
=
X'
+
\operatorname{FFN}
\left(
\operatorname{Norm}(X')
\right)
$$

$Y$ 是当前 Block 的输出，并作为下一层输入。

整个 Block 前后 Shape 不变：

$$
B\times T\times d
\rightarrow
B\times T\times d
$$

---

## 4. 注意力子层

### 4.1 作用

注意力在不同 Token 位置之间交换信息。

当前位置的表示可以根据内容和位置，从其他可见位置读取相关信息。

### 4.2 Decoder 的限制

Decoder-only LLM 使用 Causal Mask，保证每个位置只能读取自身及之前的位置。

---

## 5. 前馈网络

### 5.1 定义

**FFN 是对每个 Token 位置独立应用、参数共享的 MLP。**

经典形式为：

$$
\operatorname{FFN}(x)
=
W_2\phi(W_1x+b_1)+b_2
$$

通常先把隐藏维度扩展到更大的中间维度，再投影回 $d$。

### 5.2 作用

- Attention：在位置之间混合信息。
- FFN：在每个位置的特征维度内部进行非线性计算。

同一层中所有位置使用相同 FFN 参数。

---

## 6. 残差连接

残差连接计算：

$$
y=x+F(x)
$$

它允许：

- 原始表示直接向更深层传递。
- 子层只学习对当前表示的增量修改。
- 梯度沿加法路径更稳定地传播。

---

## 7. 归一化

LayerNorm 或 RMSNorm 控制每个 Token 隐藏向量的尺度。

Pre-Norm 在子层前归一化，现代大规模 Decoder 常使用这一结构，因为深层训练通常更稳定。

---

## 8. Dropout

训练时可以在注意力权重、子层输出或残差分支中使用 Dropout。

推理时关闭 Dropout。

具体是否使用以及使用强度取决于模型和训练规模。

---

## 9. 层数与表示

多个 Block 堆叠后：

- 浅层处理较局部和基础的模式。
- 后续层在已有表示上继续组合和变换信息。

每层都同时具有上下文信息交换和逐位置非线性计算能力。

---

## 10. 核心本质

**Transformer Block 用 Attention 在 Token 之间传递信息，用 FFN 处理每个 Token 的特征，并靠残差与归一化实现深层堆叠。**
