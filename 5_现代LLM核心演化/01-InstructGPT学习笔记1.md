

> 论文：**Training Language Models to Follow Instructions with Human Feedback**
>
> 这是 GPT-3 之后最重要的一篇论文，它没有改变模型架构，而是开创了现代 LLM **Post-training（后训练）** 的范式。

---

# 一、论文解决了什么问题？

## GPT-3 的真正问题

GPT-3 已经拥有非常强的语言能力，但它训练目标始终只有一个：

> **预测下一个 Token（Next Token Prediction）**

而用户真正希望模型完成的是：

> **理解用户意图，并给出符合期望的回答。**

也就是说：

```
Language Modeling Objective
≠
User Intent Objective
```

GPT-3 的问题不是：

> 不会回答。

而是：

> **不会按照用户真正想要的方式回答。**

---

# 二、论文最大的贡献

很多人认为：

> InstructGPT = 教模型听懂指令。

其实这是一个误解。

真正的贡献是：

> **第一次将 Human Preference（人类偏好）作为模型优化目标。**

整个训练目标发生了变化：

以前：

```
Loss = CrossEntropy
```

现在：

```
Reward = Human Preference
```

即：

```
预测 Token

↓

符合人类偏好
```

这就是后来整个 Alignment（模型对齐）研究的起点。

---

# 三、RLHF 三阶段训练流程

```
GPT-3 Pretrain

↓

SFT
(Supervised Fine-Tuning)

↓

Reward Model

↓

PPO(RLHF)

↓

InstructGPT
```

三个阶段分别解决不同问题。

---

## 第一阶段：SFT（监督微调）

输入：

```
Prompt

↓

Labeler Answer
```

训练方式：

```
CrossEntropy
```

作用：

> 让模型具备基础的 Instruction Following 能力。

例如：

```
帮我写一封辞职信

↓

生成一封辞职信
```

此时模型已经：

> **知道用户让它做什么。**

---

## 第二阶段：Reward Model（RM）

人类不会告诉模型：

> 什么才是最好的回答。

但是：

很容易判断：

```
A

B

哪个好？
```

于是：

```
Prompt

↓

Answer A

Answer B

↓

Human Ranking
```

训练：

```
Reward Model

↓

Score(answer)
```

作用：

> 学习人类偏好。

---

## 第三阶段：PPO（RLHF）

训练流程：

```
GPT

↓

Answer

↓

Reward Model

↓

Reward

↓

更新 GPT
```

目标：

```
最大化 Reward
```

模型开始逐渐学习：

> 什么样的回答更符合人的偏好。

---

# 四、为什么需要三步？

不能直接 PPO。

原因：

模型首先要：

> 会回答。

然后：

> 才知道什么回答更好。

最后：

> 再不断优化。

所以：

```
SFT

↓

RM

↓

RL
```

缺一不可。

---

# 五、KL Penalty 的作用

RL 最大的问题：

模型可能为了骗 Reward 而胡乱优化。

例如：

Reward 偏好：

```
礼貌
```

模型可能变成：

```
谢谢谢谢谢谢谢谢...
```

因此论文加入：

```
KL(original GPT)
```

限制：

> 不允许模型偏离原来的 GPT 太远。

作用：

保持：

```
能力

+

Alignment
```

之间的平衡。

---

# 六、PPO-ptx

论文发现：

RLHF 会导致：

部分 NLP Benchmark 能力下降。

即：

```
Alignment Tax
```

解决办法：

继续混合：

```
Pretraining Loss
```

一起训练。

即：

```
PPO

+

Pretraining
```

称为：

```
PPO-ptx
```

作用：

既保持 Alignment，

又减少能力下降。

---

# 七、论文实验最重要结论

论文最经典结果：

> **1.3B InstructGPT 的人类偏好超过 175B GPT-3。**

说明：

模型大小：

```
<<<<<<
```

Alignment。

用户真正喜欢的是：

```
Helpful

Honest

Harmless
```

而不是：

```
Perplexity 更低。
```

---

# 八、论文提出 Alignment 三原则（HHH）

论文提出：

模型应该做到：

## Helpful

帮助用户完成任务。

---

## Honest

不胡编事实。

尽量真实。

---

## Harmless

避免造成伤害。

---

后来：

HHH 成为 ChatGPT 很长时间的重要设计原则。

---

# 九、论文局限

论文作者也指出：

目前仍存在很多问题。

例如：

- 幻觉
- 编造事实
- 过度保守
- 容易迎合错误前提
- 偏好来自有限标注员，并不能代表所有人

因此：

RLHF

只是 Alignment 的第一步。

---

# 十、这篇论文真正改变了什么？

GPT-3 时代：

```
Pretrain

↓

Deployment
```

InstructGPT 后：

```
Pretrain

↓

SFT

↓

Reward Model

↓

RLHF

↓

Deployment
```

现代几乎所有大模型：

- ChatGPT
- Claude
- Gemini
- DeepSeek
- Qwen
- Kimi

本质都采用这一套 Post-training 思路。

区别仅在：

最后 RLHF 的实现方式不同。

例如：

- PPO
- DPO
- ORPO
- GRPO
- RLAIF

---

# 学习过程中几个容易混淆的问题

## 问题一：Instruction Tuning 是 InstructGPT 首次提出的吗？

不是。

SFT 并不是 InstructGPT 的创新。

真正的发展过程：

```
GPT-3
↓

Prompt Engineering

↓

T0
↓

FLAN
↓

Instruction Tuning

↓

InstructGPT
↓

RLHF
```

其中：

T0 与 FLAN 才真正推动了现代 **Instruction Tuning**。

InstructGPT 只是采用了这一思想。

真正创新的是：

> 使用真实用户 Prompt + Human Preference + RLHF。

---

## 问题二：InstructGPT 名字是不是容易误导？

是。

很多人第一次都会认为：

```
InstructGPT
```

就是：

```
教模型理解 Instruction
```

实际上：

SFT 已经基本完成了：

```
Instruction Following
```

RLHF 做的是：

```
Preference Alignment
```

即：

不是：

```
Can
```

变成：

```
Can Better
```

而是：

```
Will Better
```

模型已经知道怎么回答。

只是：

回答更符合人的偏好。

---

## 为什么 OpenAI 还叫 InstructGPT？

这是一个产品命名。

用户看到的是：

```
终于会听话了。
```

所以：

```
InstructGPT
```

比：

```
PreferenceGPT
```

更容易理解。

但从研究角度：

真正的新东西其实是：

```
Human Feedback
```

而不是：

```
Instruction
```

论文标题已经说明这一点：

> **Training Language Models to Follow Instructions with Human Feedback**

真正的方法创新：

> **with Human Feedback**

而：

> **Follow Instructions**

更多描述的是最终效果。

---

# 与 GPT 系列论文的关系

| 论文 | 最大贡献 |
|------|---------|
| Transformer | Attention 架构 |
| GPT-1 | Decoder Only + 预训练 |
| GPT-2 | Zero-shot Emergence |
| GPT-3 | Scaling Law + In-context Learning |
| **InstructGPT** | RLHF、Alignment、Post-training |

---

# 一句话总结

> **GPT-1 解决"如何训练语言模型"，GPT-3 解决"模型为什么会涌现能力"，而 InstructGPT 解决"如何让模型按照人类希望的方式使用这些能力"。**