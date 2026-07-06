
> 核心一句话：
>
> **SentencePiece 的本质就是一个自动学习 Subword（子词）词表和切分规则的 Tokenizer，将任意文本稳定地映射为模型可输入的 Token 序列。**

---

# 一、SentencePiece 是什么？

SentencePiece 是 Google 开源的一套 **Tokenizer 框架**。

它解决的是：

> **如何把自然语言文本，转换成 Transformer 可以处理的 Token ID。**

整个流程：

```text
文本

↓

SentencePiece Tokenizer

↓

Token

↓

Token ID

↓

Embedding

↓

Transformer
```

它不是模型的一部分，而是模型前面的"文本编码器"。

---

# 二、为什么需要 SentencePiece？

模型不能直接理解：

```text
我喜欢人工智能
```

必须转换成数字。

最简单有三种方案：

## 1、字符级（Character）

```text
我
喜
欢
人
工
智
能
```

优点：

- 不会出现未知词（OOV）

缺点：

- Token 太多
- 一个词的语义被拆散

例如：

```text
人工智能

↓

人
工
智
能
```

模型需要自己重新学习这是一个概念。

---

## 2、词级（Word）

```text
我
喜欢
人工智能
```

优点：

Token 少。

缺点：

需要人工分词。

例如：

```text
机器学习工程师
```

到底应该：

```text
机器
学习
工程师
```

还是：

```text
机器学习
工程师
```

没有统一标准。

另外：

新词不断出现：

```text
ChatGPT
DeepSeek
Qwen3
```

都会变成 OOV。

---

## 3、子词级（Subword）

SentencePiece 采用：

```text
人工智能

↓

人工
智能
```

或者：

```text
人工
智
能
```

它自动寻找最优拆法。

优点：

- Token 数量适中
- 没有 OOV
- 保留更多语义

这也是现代 LLM 普遍采用的方法。

---

# 三、SentencePiece 的本质

一句话：

> **SentencePiece = 自动学习 Subword 词表和切分规则的 Tokenizer。**

或者：

> **SentencePiece 的本质就是自动学习一种"最适合模型训练"的文本切分方式。**

注意：

它关心的不是语言学意义上的"词"。

而是：

> **怎样切分最利于模型学习。**

---

# 四、SentencePiece 做了什么？

主要两件事情。

## 第一件：训练 Vocabulary

输入：

```text
几百 GB 文本
```

学习：

```text
人工
人工智能
学习
机器
机器学习
...
```

最终生成：

```text
tokenizer.model
```

里面保存：

- Token
- Token ID
- Token Score（Unigram）
- Merge Rule（BPE）
- 特殊 Token

---

## 第二件：Encode

例如：

```text
我喜欢人工智能
```

编码：

```text
我
喜欢
人工智能
```

变成：

```text
[315,842,12094]
```

模型真正看到的是：

```text
315
842
12094
```

---

# 五、为什么 decode 很简单？

因为：

Vocabulary 本身就是双向映射。

例如：

```text
12094

↓

人工智能
```

decode 本质就是：

```text
Token ID

↓

字符串

↓

拼接
```

只是查表。

---

# 六、为什么 API 看起来只有一句？

例如：

```python
sp.encode(text)
```

真正复杂的是：

```text
SentencePieceTrainer
```

训练：

```text
几十分钟

↓

tokenizer.model
```

推理阶段只是：

```text
加载 model

↓

查找

↓

切分
```

因此 API 非常简单。

---

# 七、tokenizer.model 保存了什么？

主要保存：

- Token
- Token ID
- Token Score（Unigram）
- Merge Rule（BPE）
- 特殊 Token

例如：

```text
人工智能

↓

ID = 12094
Score = -1.2
```

---

# 八、为什么需要 Score？

这是很多人第一次容易忽略的问题。

SentencePiece 不是简单查字典。

例如：

```text
人工智能
```

可能有三种切法：

方案一：

```text
人工智能
```

方案二：

```text
人工
智能
```

方案三：

```text
人
工
智
能
```

到底选哪个？

如果：

## Unigram

每个 Token 都有一个概率：

```text
人工智能 score=-1.2
人工 score=-3.5
智能 score=-3.8
```

SentencePiece 会计算：

```text
整个句子的概率
```

选择概率最大的切法。

所以：

**Score 用于寻找最优切分。**

---

如果：

## BPE

没有 Score。

而是：

保存：

```text
Merge Rule
```

例如：

```text
a+b

↓

ab
```

不断 Merge。

因此：

- BPE 保存 Merge
- Unigram 保存 Score

---

# 九、为什么使用 ▁？

SentencePiece 使用：

```text
▁
```

表示：

> **Whitespace Marker（空白字符标记）**

例如：

原始文本：

```text
I love NLP
```

内部：

```text
▁I ▁love ▁NLP
```

---

它不是下划线。

也不是普通字符。

只是：

**把空格变成一个可学习字符。**

---

为什么？

因为：

模型需要知道：

```text
love
```

和：

```text
▁love
```

并不是同一个 Token。

例如：

```text
lovely
```

里面：

```text
love
```

只是单词一部分。

而：

```text
▁love
```

表示：

一个新单词开始。

---

## 为什么不用真正空格？

因为：

Tokenizer 希望：

空格也参与训练。

如果直接删除：

```text
IloveNLP
```

就无法恢复。

因此：

SentencePiece：

```text
空格

↓

▁
```

decode：

```text
▁

↓

空格
```

完全可逆。

---

# 十、中文之间会不会有 ▁？

答案：

**不会。**

只有：

- 原始空格
- 句首隐式空格

才对应：

```text
▁
```

例如：

```text
我喜欢人工智能
```

不会：

```text
▁我▁喜欢▁人工智能
```

而是类似：

```text
▁我
喜欢
人工智能
```

句首默认存在一个隐式空格。

---

# 十一、SentencePiece 会不会分词？

会。

但是：

它分的是：

> **Subword（子词）**

不是：

中文分词。

例如：

```text
中华人民共和国
```

可能：

```text
中华
人民
共和国
```

也可能：

```text
中华人民共和国
```

取决于训练结果。

它不关心：

语言学上的词。

只关心：

> **怎样切分最适合模型学习。**

---

# 十二、SentencePiece 与 BPE 的关系

很多人误认为：

```text
SentencePiece = BPE
```

实际上：

不是。

SentencePiece 是：

```text
Tokenizer Framework

├── BPE
└── Unigram
```

训练时：

```bash
--model_type=bpe
```

就是：

BPE。

如果：

```bash
--model_type=unigram
```

就是：

Unigram。

因此：

SentencePiece 不是算法。

而是：

Tokenizer 框架。

---

# 十三、Llama2 使用什么 Tokenizer？

Llama2：

采用：

```text
SentencePiece

+

BPE
```

即：

> **SentencePiece BPE**

不是：

Unigram。

---

Python：

```python
SentencePieceProcessor(model_file=...)
```

根本看不出来。

真正决定算法的是：

```text
tokenizer.model
```

里面保存：

```text
model_type=bpe
```

或者：

```text
model_type=unigram
```

---

# 十四、是不是 Byte-Level BPE？

不是。

Llama：

采用：

```text
Unicode Character

↓

BPE
```

即：

字符级 BPE。

---

GPT-2：

采用：

```text
UTF-8 Bytes

↓

Byte-Level BPE
```

例如：

```text
你
```

UTF-8：

```text
E4 BD A0
```

GPT：

从：

```text
E4
BD
A0
```

开始 Merge。

---

Llama：

直接：

```text
你
```

作为初始 Symbol。

因此：

Llama 使用：

> **Unicode 字符级 BPE。**

不是：

Byte-Level BPE。

---

# 十五、为什么 Llama 不采用 Byte-Level BPE？

主要三个原因。

## 1、中文 Token 更少

例如：

```text
人工智能
```

Byte：

```text
12 个 Byte
```

Unicode：

```text
4 个字符
```

训练效率更高。

---

## 2、SentencePiece 当时已经成熟

Google：

- T5
- ALBERT
- XLNet

全部采用 SentencePiece。

Meta 直接沿用。

---

## 3、工程实现成熟

SentencePiece：

训练、

编码、

解码、

导出

全部完善。

无需自己维护 Tokenizer。

---

# 十六、为什么 GPT 坚持 Byte-Level？

OpenAI 更关注：

> **任何文本都能编码。**

Byte：

```text
0~255
```

任何 Unicode：

任何 Emoji：

任何生僻字：

都能表示。

天然不存在字符级 OOV。

---

# 十七、现代 LLM 都使用什么？

目前形成两条路线。

| 模型 | Tokenizer |
|------|-----------|
| GPT-2 | Byte-Level BPE |
| GPT-3 | Byte-Level BPE |
| GPT-4 | 未公开，普遍认为属于 Byte-Level BPE 家族 |
| Llama1 | SentencePiece BPE |
| Llama2 | SentencePiece BPE |
| Llama3 | tiktoken（Byte-Level BPE 家族） |
| Mistral | SentencePiece BPE |
| Gemma | SentencePiece |
| Qwen2 | tiktoken（Byte-Level BPE） |
| DeepSeek V3 | Byte-Level BPE（tiktoken 风格） |

可以发现：

近年来越来越多模型开始采用：

> **Byte-Level BPE（tiktoken 路线）**

主要原因：

- 更统一
- 更快
- 工程生态更成熟

---

# 十八、整体架构总结

```text
SentencePiece
        │
        ▼
Tokenizer Framework
        │
        ├── BPE
        └── Unigram
                │
                ▼
训练 tokenizer.model
                │
                ▼
encode()
decode()
```

真正决定 Tokenizer 行为的：

不是 Python。

而是：

```text
tokenizer.model
```

里面保存：

- Vocabulary
- Merge Rule 或 Score
- Special Tokens
- Model Type

所有 encode / decode 都依据它完成。

---

# 总结（一页记住）

## SentencePiece

- Google 开源 Tokenizer 框架
- 自动学习 Subword
- 支持 BPE 与 Unigram
- Llama1/2 使用 SentencePiece BPE

---

## BPE

保存：

- Merge Rule

不断 Merge 得到 Token。

---

## Unigram

保存：

- Token Score

寻找概率最大的切分。

---

## ▁

不是下划线。

表示：

> Whitespace Marker（空格标记）

作用：

让空格也参与学习。

---

## Llama2

采用：

```text
SentencePiece
+
Unicode 字符级 BPE
```

不是：

Byte-Level BPE。

---

## GPT 系列

采用：

```text
Byte-Level BPE
```

初始单位：

UTF-8 Byte。

---

## 一句话总结

> **SentencePiece 是一个自动学习子词词表和切分规则的 Tokenizer 框架；Llama2 使用的是其中的 Unicode 字符级 BPE，而 GPT 系列采用的是 Byte-Level BPE。**