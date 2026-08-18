# Base、Instruct、Chat 与上下文学习

## 1. 解决的问题

区分预训练模型与助手模型，并解释为什么同一个下一个 Token 预测模型能够根据 Prompt、示例和对话角色表现出不同任务行为。

---

## 2. Base Model

### 2.1 定义

**Base Model 是主要通过大规模下一个 Token 预测完成预训练、尚未专门优化为指令助手的语言模型。**

### 2.2 行为

Base Model 学习的是训练语料的条件分布：

$$
p_\theta(x_{\text{next}}\mid x_{\text{context}})
$$

它擅长续写给定上下文，但不保证：

- 遵循用户指令。
- 采用问答格式。
- 拒绝危险请求。
- 判断用户真正意图。

### 2.3 核心本质

**Base Model 学会的是根据上下文继续文本，而不是天然学会扮演可靠助手。**

---

## 3. Instruct Model

### 3.1 定义

**Instruct Model 是经过指令数据后训练，使输出更符合用户任务要求的语言模型。**

训练样本通常包含：

$$
\text{指令或上下文}
\rightarrow
\text{理想回答}
$$

后训练改变的是给定指令条件下的输出行为，而不是替换语言模型的自回归结构。

### 3.2 核心本质

**Instruct Model 在 Base Model 的语言能力上，进一步学习“收到任务后应当怎样回答”。**

---

## 4. Chat Model

### 4.1 定义

**Chat Model 是使用带角色和消息边界的多轮对话格式进行后训练与推理的 Instruct Model。**

对话在进入模型前仍会被序列化为一个 Token 序列，例如：

$$
\text{System}
\rightarrow
\text{User}
\rightarrow
\text{Assistant}
\rightarrow
\text{User}
\rightarrow
\text{Assistant}
$$

模型并不接收抽象的“消息对象”，而是接收按 Chat Template 编码后的 Token IDs。

### 4.2 Chat Template

Chat Template 规定：

- 每个角色使用什么特殊 Token。
- 消息如何开始和结束。
- Assistant 生成从哪个边界开始。
- 工具或结构化内容如何表示。

使用错误模板会使输入分布偏离训练格式，导致行为下降。

### 4.3 核心本质

**Chat Model 仍是自回归语言模型，只是通过特殊 Token 和训练数据学习了多轮角色结构。**

---

## 5. 核心机制：上下文学习

### 5.1 定义

**上下文学习是在不更新模型参数的情况下，仅通过 Prompt 中的任务描述、示例或信息改变当前输出行为。**

### 5.2 Zero-shot

只提供任务描述，不提供示例。

### 5.3 Few-shot

在上下文中提供少量输入输出示例，让模型根据示例延续任务模式。

### 5.4 与训练的区别

上下文学习：

- 不执行反向传播。
- 不改变参数。
- 信息只在当前上下文中有效。

参数学习：

- 使用损失和梯度更新参数。
- 学到的变化可跨请求保留。

---

## 6. Prompt 的作用

Prompt 通过改变条件：

$$
p_\theta(y\mid \text{context})
$$

来改变输出分布。

Prompt 不会凭空向模型参数中写入知识，也不能保证模型一定遵守所有文字要求。

---

## 7. 核心本质

**Base、Instruct 和 Chat 使用相同的自回归骨架，差别主要来自后训练数据、目标和输入序列化格式。**
