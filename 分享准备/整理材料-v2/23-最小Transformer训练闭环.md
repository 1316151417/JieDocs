# 最小 Transformer 训练闭环

## 1. 解决的问题

把数据、模型、损失、反向传播、优化和生成连接起来，形成一个可以实际运行的最小 Decoder-only Transformer。

---

## 2. 定义

**最小 Transformer 训练闭环是从原始文本构造训练 Batch，经模型计算下一个 Token 损失并更新参数，再使用训练后的模型自回归生成文本的完整过程。**

---

## 3. 核心机制：数据准备

### 3.1 分词

$$
\text{文本}
\rightarrow
[x_1,x_2,\ldots,x_N]
$$

### 3.2 切分训练样本

从 Token 流中取长度为 $T+1$ 的片段：

$$
[x_s,\ldots,x_{s+T}]
$$

输入：

$$
X=[x_s,\ldots,x_{s+T-1}]
$$

标签：

$$
Y=[x_{s+1},\ldots,x_{s+T}]
$$

---

## 4. 模型组成

最小模型至少需要：

1. Token Embedding。
2. 位置信息。
3. 一个或多个 Causal Transformer Block。
4. 最终归一化。
5. 词表输出层。

---

## 5. 一次训练步骤

### 5.1 前向传播

$$
Z=\operatorname{Model}(X)
$$

其中：

$$
Z\in\mathbb R^{B\times T\times V}
$$

### 5.2 计算损失

把每个有效位置的 Logits 与下一个真实 Token 对齐：

$$
L
=
\operatorname{CrossEntropy}
(Z,Y)
$$

### 5.3 清空旧梯度

优化器更新前必须清除或重置上一轮累积的梯度。

### 5.4 反向传播

$$
\nabla_\theta L
=
\operatorname{Backward}(L)
$$

### 5.5 参数更新

$$
\theta\leftarrow\operatorname{OptimizerStep}
(\theta,\nabla_\theta L)
$$

---

## 6. 训练伪代码

~~~text
for each batch:
    input_ids, labels = make_shifted_batch(tokens)
    logits = model(input_ids)
    loss = cross_entropy(logits, labels)

    optimizer.zero_grad()
    loss.backward()
    clip_grad_if_needed()
    optimizer.step()
    scheduler.step()
~~~

---

## 7. 验证

定期固定模型参数，在验证集上计算平均损失和 Perplexity。

验证时：

- 不计算梯度。
- 不更新参数。
- 关闭 Dropout。

训练损失和验证损失都应被记录。

---

## 8. 生成闭环

给定 Prompt：

1. 编码为 Token IDs。
2. 前向计算最后一个位置的 Logits。
3. 选择或采样下一个 Token。
4. 把 Token 追加到输入。
5. 重复直到 EOS 或达到长度上限。
6. 将 Token IDs 解码为文本。

---

## 9. 必须检查的正确性

### 9.1 Shape

- 输入：$B\times T$。
- 隐藏状态：$B\times T\times d$。
- Logits：$B\times T\times V$。

### 9.2 标签对齐

位置 $t$ 的输出必须预测位置 $t+1$ 的 Token。

### 9.3 因果掩码

改变未来 Token 不应影响更早位置的输出。

### 9.4 过拟合小数据

模型应能在极小数据集上把训练损失显著降低。

如果做不到，通常说明实现、梯度或标签存在问题。

### 9.5 训练与验证模式

验证和生成时应切换到推理模式并关闭梯度记录。

---

## 10. 核心本质

**最小训练闭环就是让 Transformer 对右移一位的 Token 标签计算交叉熵，再通过反向传播和优化不断提高真实序列的概率。**
