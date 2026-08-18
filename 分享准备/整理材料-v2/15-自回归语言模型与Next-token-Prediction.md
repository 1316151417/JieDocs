# 自回归语言模型与 Next-token Prediction

## 1. 解决的问题

学习完整 Token 序列的概率分布，并在给定已有上下文时预测下一个 Token。

---

## 2. 定义

**自回归语言模型按照从左到右的顺序，将序列联合概率分解为每个 Token 在先前 Token 条件下的概率。**

---

## 3. 核心机制

### 3.1 概率链式分解

对于序列：

$$
x_{1:T}=(x_1,x_2,\ldots,x_T)
$$

联合概率分解为：

$$
p_\theta(x_{1:T})
=
\prod_{t=1}^{T}
p_\theta(x_t\mid x_{<t})
$$

其中：

$$
x_{<t}=(x_1,\ldots,x_{t-1})
$$

复杂的序列生成问题因此被转化为重复预测下一个 Token。

### 3.2 输入与标签右移

对于 Token 序列：

$$
[x_1,x_2,x_3,x_4]
$$

训练输入可以是：

$$
[x_1,x_2,x_3]
$$

对应目标为：

$$
[x_2,x_3,x_4]
$$

模型在一次前向传播中并行预测每个位置的下一个 Token。

### 3.3 Logits 与概率

位置 $t$ 的隐藏状态经过词表输出层得到：

$$
z_t\in\mathbb R^V
$$

再经过 Softmax：

$$
p_\theta(x_{t+1}=i\mid x_{\le t})
=
\operatorname{Softmax}(z_t)_i
$$

### 3.4 训练目标

序列负对数似然为：

$$
L
=
-\sum_{t=1}^{T}
\log p_\theta(x_t\mid x_{<t})
$$

通常对有效 Token 取平均。

最小化该损失等价于最大化训练文本的似然。

### 3.5 Teacher Forcing

训练时，每个位置看到的历史上下文来自真实训练序列，而不是模型刚刚生成的 Token。

这使所有位置可以并行训练。

推理时没有未来的真实 Token，模型必须把自己生成的 Token 追加到上下文中继续预测。

---

## 4. 因果性

预测位置 $t$ 时，模型只能使用 $x_{\le t}$，不能看到目标位置之后的 Token。

Decoder-only Transformer 使用 Causal Mask 强制满足这一限制。

---

## 5. Perplexity

如果平均负对数似然为：

$$
\bar L
=
-\frac{1}{N}
\sum_{i=1}^{N}\log p_\theta(x_i\mid x_{<i})
$$

则困惑度为：

$$
\operatorname{PPL}=e^{\bar L}
$$

在相同 Tokenizer 和数据定义下，PPL 越低，表示模型平均为真实 Token 分配的概率越高。

不同 Tokenizer 下的 PPL 通常不能直接比较。

---

## 6. 训练与生成

### 6.1 训练

一次输入多个 Token，并行计算所有位置的预测和损失。

### 6.2 生成

每一步只产生一个新 Token：

1. 输入已有上下文。
2. 计算下一个 Token 分布。
3. 选择或采样一个 Token。
4. 追加到上下文。
5. 重复直到停止。

---

## 7. 核心本质

**自回归语言模型通过反复学习“给定前文预测下一个 Token”，间接学习并生成完整序列。**

