# Encoder、Decoder 与三类 Transformer

## 1. 解决的问题

区分 Transformer 的三种主要结构和训练目标，理解为什么现代通用生成式 LLM 主要采用 Decoder-only。

---

## 2. Encoder-only

### 2.1 定义

**Encoder-only Transformer 使用双向 Self-Attention，让每个位置同时读取左右两侧上下文。**

### 2.2 注意力范围

通常没有 Causal Mask：

$$
x_i\leftrightarrow x_j
$$

每个位置都能看到整段输入。

### 2.3 典型训练目标

Masked Language Modeling：

1. 遮住部分输入 Token。
2. 使用左右上下文恢复被遮住的 Token。

### 2.4 适合任务

适合理解型任务，例如分类、序列标注和表示提取。

它不能直接按标准训练方式从左到右持续生成任意长度文本。

### 2.5 核心本质

**Encoder-only 通过双向上下文学习输入表示，重点是理解而不是自回归生成。**

---

## 3. Decoder-only

### 3.1 定义

**Decoder-only Transformer 使用 Causal Self-Attention，根据左侧上下文预测下一个 Token。**

### 3.2 典型训练目标

$$
p(x_{1:T})
=
\prod_t p(x_t\mid x_{<t})
$$

### 3.3 适合任务

- 开放式文本生成。
- 对话。
- 代码生成。
- 条件生成。
- 通过上下文完成多种任务。

提示、指令、示例和待处理内容都可以串成一个 Token 序列，统一为续写问题。

### 3.4 核心本质

**Decoder-only 把各种条件任务统一成“给定前文继续生成”，因此成为通用生成式 LLM 的主流结构。**

---

## 4. Encoder-Decoder

### 4.1 定义

**Encoder-Decoder Transformer 先用 Encoder 双向编码输入，再由 Decoder 通过 Cross-Attention 读取 Encoder 表示并自回归生成输出。**

### 4.2 核心机制

Encoder：

$$
H_{\text{enc}}
=
\operatorname{Encoder}(X)
$$

Decoder 使用：

- 对已生成输出的 Causal Self-Attention。
- 对 $H_{\text{enc}}$ 的 Cross-Attention。

### 4.3 适合任务

输入和输出边界明确的序列转换任务，例如翻译、摘要和结构化转换。

### 4.4 核心本质

**Encoder-Decoder 将输入理解和输出生成分开，并通过 Cross-Attention 连接两者。**

---

## 5. 对比

|结构|上下文可见性|主要目标|核心用途|
|---|---|---|---|
|Encoder-only|双向|恢复或理解输入|表示与理解|
|Decoder-only|仅过去|预测下一个 Token|开放生成与通用 LLM|
|Encoder-Decoder|输入双向、输出因果|条件序列生成|输入到输出转换|

---

## 6. 核心本质

**三类 Transformer 的根本区别是信息可见范围和训练目标，而 Decoder-only 用统一的续写形式覆盖了最广泛的生成任务。**

