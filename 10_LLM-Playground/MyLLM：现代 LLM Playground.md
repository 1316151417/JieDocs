
一个用于学习、实验、验证现代大语言模型技术的统一实验平台。

---

# **一、项目定位**

## **为什么做这个项目？**

在学习 LLM 的过程中，会不断阅读新的论文，例如：

- Transformer
- GPT 系列
- LLaMA
- FlashAttention
- MQA / GQA
- MoE
- RoPE
- RMSNorm
- SwiGLU
- Speculative Decoding
- MTP
- KV Cache

传统的学习方式通常是：

```
阅读论文
    ↓
找一个 Demo
    ↓
修改代码
    ↓
跑通实验
    ↓
项目结束
```

随着学习内容越来越多，会出现几个问题：

- 每篇论文都是独立 Demo
- 每次都需要重新搭建环境
- 技术之间没有统一框架
- 没有持续沉淀
- 一年后很难复用之前的成果

MyLLM 希望解决这个问题。

---

# **二、项目目标**

MyLLM 并不是一个产品，而是一个长期演进的技术平台。

目标包括：

- 深入理解现代 LLM 架构
- 学习模型训练与推理工程
- 建立统一实验环境
- 快速验证新论文
- 沉淀长期技术资产
- 形成高质量个人作品集

---

# **三、解决什么问题**

## **1. 知识无法沉淀**

传统方式：

```
FlashAttention Demo
RoPE Demo
MoE Demo
Tokenizer Demo
```

全部散落在不同仓库。

MyLLM：

```
MyLLM
├── attention
├── rope
├── moe
├── tokenizer
```

所有知识集中维护。

---

## **2. 新技术验证成本高**

例如：

今天阅读一篇新的 KV Cache 论文。

传统方式：

```
重新下载项目
重新修改代码
重新训练
重新部署
```

有了 Playground：

```
新增模块
运行 Benchmark
完成实验
```

验证成本极低。

---

## **3. 工程能力无法持续积累**

普通项目：

```
完成
↓

结束
```

MyLLM：

```
持续增加模块

↓

持续优化

↓

持续沉淀
```

最终形成自己的 LLM Framework。

---

## **4. 成为自己的 AI 实验室**

以后任何论文都可以放进去：

- 新 Tokenizer
- 新 Position Encoding
- 新 Attention
- 新推理算法
- 新训练算法

形成统一实验平台。

---

# **四、项目整体架构**

```
MyLLM

├── tokenizer
│
├── datasets
│
├── models
│   ├── llama
│   ├── qwen
│   ├── deepseek
│
├── inference
│   ├── kv cache
│   ├── flash attention
│   ├── speculative decoding
│   ├── continuous batching
│
├── finetune
│   ├── lora
│   ├── qlora
│
├── evaluation
│
├── benchmark
│
├── serving
│
├── plugins
│   ├── vscode
│   ├── idea
│
├── examples
│
└── docs
```

整个仓库围绕一个目标：

每学习一种现代 LLM 技术，都能沉淀到这里。

---

# **五、长期规划**

## **第一阶段：基础能力**

目标：

理解模型最核心流程。

模块：

- Tokenizer
- Transformer
- LLaMA 推理
- KV Cache
- Sampling
- OpenAI Compatible API

完成后能够：

```
模型

↓

推理

↓

HTTP API
```

---

## **第二阶段：现代推理优化**

目标：

理解现代推理技术。

模块：

- FlashAttention
- MQA
- GQA
- Continuous Batching
- Prefix Cache
- Speculative Decoding

重点回答：

这些技术为什么更快？

实际能快多少？

适用于哪些场景？

---

## **第三阶段：训练与微调**

目标：

理解训练体系。

模块：

- SFT
- LoRA
- QLoRA
- DPO
- 数据预处理
- Tokenizer 训练

完成：

```
数据

↓

训练

↓

模型
```

完整闭环。

---

## **第四阶段：模型评测**

目标：

建立统一评测体系。

模块：

- HumanEval
- MBPP
- MMLU
- Benchmark
- 回归测试

以后所有实验统一评测。

---

## **第五阶段：工程化**

目标：

真正做到可部署。

模块：

- Serving
- OpenAI API
- 模型管理
- 配置管理
- 日志
- Monitoring

---

## **第六阶段：IDE 插件**

目标：

真正解决自己的开发问题。

实现：

- VS Code 插件
- IDEA 插件
- Java Code Completion
- Fill-in-the-Middle
- 本地补全

最终形成：

```
IDE

↓

MyLLM

↓

代码补全
```

---

## **第七阶段：高级能力**

后续继续扩展：

- Agent
- MCP
- Code Search
- RAG
- Tool Calling
- 多模型路由
- 多 Agent

所有能力共享统一基础设施。

---

# **六、项目原则**

## **1. 平台优先**

不要做一个个独立 Demo。

而是在平台中增加模块。

---

## **2. 理解原理优先**

目标不是重复造轮子。

而是：

- 理解设计思想
- 理解实现原理
- 能自己实现核心流程

复杂工程能力尽量复用成熟开源方案。

---

## **3. 模块独立**

每项技术都是插件。

例如：

```
FlashAttention

↓

Attention 接口
```

未来可以自由替换。

---

## **4. Benchmark 驱动**

任何新技术必须回答：

- 是否更快？
- 是否更省显存？
- 是否更准确？
- 是否值得保留？

数据驱动，而不是感觉驱动。

---

## **5. 长期维护**

这是一个长期项目。

不是：

```
完成

↓

结束
```

而是：

```
持续学习

↓

持续增加模块

↓

持续优化

↓

持续积累
```

---

# **七、项目价值**

## **对学习**

能够系统理解：

- Tokenizer
- 模型结构
- 推理
- 微调
- Serving
- Agent

形成完整知识体系。

---

## **对工程能力**

覆盖：

- Python
- CUDA（可选）
- PyTorch
- 推理框架
- API
- 插件开发
- Benchmark
- 自动化测试

形成完整 AI 工程能力。

---

## **对面试**

相比：

做了一个 RAG

或

做了一个 Agent

更容易体现：

- 模型理解能力
- 推理优化能力
- 工程设计能力
- 技术深度

同时具有持续迭代能力。

---

## **对长期发展**

MyLLM 将成为自己的 AI 技术实验室。

未来学习任何新论文，都可以快速：

```
阅读论文

↓

新增模块

↓

Benchmark

↓

总结

↓

沉淀
```

几年后，它不仅是一个项目，更是一套持续成长的技术资产和个人作品集。