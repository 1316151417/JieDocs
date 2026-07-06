# tokenizer.py 学习笔记（SentencePiece Tokenizer）

## 文件作用

`tokenizer.py` 是对 **SentencePiece Tokenizer** 的一个简单封装。

它主要提供两类能力：

1. **推理时使用**
   - 加载 `tokenizer.model`
   - 文本编码（Encode）
   - Token 解码（Decode）

2. **导出 Tokenizer**
   - 将 `tokenizer.model`
   - 转换为 `tokenizer.bin`
   - 供 `llama2.c`（C 语言推理版本）使用

整个文件可以理解为：

```text
SentencePiece
        │
        ▼
  Tokenizer 封装
        │
        ├──────────────┐
        │              │
        ▼              ▼
 Encode/Decode      Export
(Python 推理)      (C 推理)
```

---

# 整体执行流程

## 推理时

```text
加载 tokenizer.model
        ↓
读取词表信息
        ↓
Encode（文本 → Token）
        ↓
Decode（Token → 文本）
```

## 导出时

```text
加载 tokenizer.model
        ↓
遍历整个词表
        ↓
读取 Token 和 Score
        ↓
简单后处理
        ↓
写入 tokenizer.bin
```

---

# 第一部分：导入依赖

```python
import os
import struct
import argparse

from sentencepiece import SentencePieceProcessor
```

主要依赖：

| 模块 | 作用 |
|------|------|
| os | 检查 tokenizer 文件是否存在 |
| struct | 写入二进制文件 |
| argparse | 命令行参数 |
| SentencePieceProcessor | SentencePiece Tokenizer |

---

# 第二部分：默认 Tokenizer

```python
TOKENIZER_MODEL = "tokenizer.model"
```

默认读取：

```
tokenizer.model
```

这是 SentencePiece 训练完成后的模型文件。

里面保存了：

- Token 词表
- Token ↔ ID 映射
- Token Score
- BOS / EOS / PAD
- SentencePiece 分词规则

---

# 第三部分：Tokenizer 类

整个类主要提供四个能力：

```text
初始化
    ↓
Encode
    ↓
Decode
    ↓
Export
```

---

# 第四部分：初始化 Tokenizer

```python
self.sp_model = SentencePieceProcessor(...)
```

作用：

加载：

```
tokenizer.model
```

加载完成后：

```text
SentencePiece
已经知道：

文本
↓

Token

Token

↓

文本
```

---

## 读取词表信息

随后读取：

```python
self.n_words
self.bos_id
self.eos_id
self.pad_id
```

表示：

| 属性 | 含义 |
|------|------|
| n_words | 词表大小 |
| bos_id | BOS Token |
| eos_id | EOS Token |
| pad_id | PAD Token |

例如：

```
<s>
</s>
```

这些特殊 Token 的编号都保存在这里。

---

# 第五部分：Encode

```python
encode(...)
```

作用：

```
文本
↓

Token ID
```

例如：

```
Hello world
```

可能变成：

```
[15043, 29871]
```

如果：

```python
bos=True
```

则：

```
Hello world
```

变成：

```
[1, 15043, 29871]
```

如果：

```python
eos=True
```

则：

```
[15043, 29871, 2]
```

因此：

```python
bos
```

决定：

是否加：

```
<s>
```

而：

```python
eos
```

决定：

是否加：

```
</s>
```

---

# 第六部分：Decode

```python
decode(...)
```

作用：

```
Token ID

↓

文本
```

例如：

```
[1,15043,29871]
```

恢复为：

```
Hello world
```

本质只是调用：

```python
SentencePiece.decode()
```

---

# 第七部分：Export

这是整个文件最特殊的部分。

作用：

将：

```
tokenizer.model
```

转换成：

```
tokenizer.bin
```

原因：

Python 可以直接使用：

```
SentencePiece
```

但是：

```
llama2.c
```

不依赖 SentencePiece。

因此：

提前把所有 Token 导出成：

```
tokenizer.bin
```

方便 C 程序直接读取。

---

# 第八部分：遍历整个词表

```python
for i in range(self.n_words):
```

依次读取：

每一个 Token。

例如：

```
0
1
2
3
...
31999
```

对于每一个 Token：

读取：

```python
id_to_piece()
```

得到：

```
Token 字符串
```

例如：

```
▁hello
```

同时读取：

```python
get_score()
```

得到：

```
Token Score
```

Score 是：

SentencePiece 训练得到的子词分数。

---

# 第九部分：Token 后处理

主要进行了两件事情。

---

## ① BOS / EOS 特殊处理

如果：

```
BOS
```

替换成：

```
<s>
```

如果：

```
EOS
```

替换成：

```
</s>
```

方便后续 C 程序识别。

---

## ② 替换空格符号

SentencePiece 使用：

```
▁
```

表示：

```
空格
```

例如：

```
▁Hello
```

真正含义：

```
 Hello
```

因此：

```python
replace("▁"," ")
```

恢复为空格。

---

随后：

```python
.encode("utf8")
```

转换成：

```
Bytes
```

因为：

二进制文件只能保存：

```
Byte
```

而不能直接保存：

```
Python String
```

---

# 第十部分：计算最长 Token

```python
max_token_length
```

计算：

整个词表里：

最长 Token 有多少字节。

例如：

```
最长：

internationalization
```

可能：

```
24 Bytes
```

这个值会写到：

```
tokenizer.bin
```

文件头。

作用：

方便 C 程序一次性申请 Buffer。

---

# 第十一部分：写入 tokenizer.bin

输出文件：

```
tokenizer.bin
```

首先写：

```
最长 Token 长度
```

随后：

每一个 Token：

依次写入：

```
Score
↓

Token 长度

↓

Token Bytes
```

最终：

整个文件格式：

```text
max_token_length

↓

token1
score
length
bytes

↓

token2
score
length
bytes

↓

...
```

即：

```text
+----------------------+
|max_token_length      |
+----------------------+

+----------------------+
|score                 |
|length                |
|bytes                 |
+----------------------+

+----------------------+
|score                 |
|length                |
|bytes                 |
+----------------------+

......
```

因此：

C 程序无需依赖：

SentencePiece。

只需要：

读取：

```
tokenizer.bin
```

即可获得：

整个词表。

---

# 第十二部分：命令行入口

```python
if __name__ == "__main__":
```

说明：

只有直接运行：

```bash
python tokenizer.py
```

时：

才执行下面代码。

流程：

```text
读取命令行参数
        ↓
创建 Tokenizer
        ↓
调用 export()
        ↓
生成 tokenizer.bin
```

例如：

默认：

```bash
python tokenizer.py
```

生成：

```
tokenizer.bin
```

也可以：

```bash
python tokenizer.py \
    -t my_tokenizer.model
```

生成：

```
my_tokenizer.bin
```

---

# 整体流程总结

## 推理阶段

```text
文本
    │
    ▼
SentencePiece
    │
    ▼
Token IDs
    │
    ▼
Transformer
    │
    ▼
Token IDs
    │
    ▼
SentencePiece
    │
    ▼
文本
```

---

## 导出阶段

```text
tokenizer.model
        │
        ▼
SentencePiece
        │
        ▼
遍历整个词表
        │
        ▼
Token
Score
Special Token
Whitespace
        │
        ▼
tokenizer.bin
```

---

# tokenizer.py 核心模块总结

| 模块 | 作用 |
|------|------|
| 初始化 | 加载 `tokenizer.model` |
| 读取元信息 | 获取词表大小、BOS、EOS、PAD |
| Encode | 文本 → Token IDs |
| Decode | Token IDs → 文本 |
| Export | 导出 `tokenizer.bin` |
| Token 遍历 | 获取所有 Token 与 Score |
| Token 后处理 | BOS/EOS、空格符号替换、UTF-8 编码 |
| 写入二进制 | 保存为 `tokenizer.bin` |

---

# 与 sample.py 的关系

`sample.py` 只使用了 `Tokenizer` 的 **编码** 和 **解码** 能力：

```python
enc = Tokenizer(...)

start_ids = enc.encode(...)

...

text = enc.decode(...)
```

`export()` 在推理过程中不会被调用，它的作用是提前将 `tokenizer.model` 转换为 `tokenizer.bin`，供 `llama2.c` 等 C 语言版本直接读取，而无需依赖 SentencePiece 库。

---

# 核心思想

整个 `tokenizer.py` 可以概括为：

```text
加载 SentencePiece
        │
        ├──────────────┐
        │              │
        ▼              ▼
 Encode/Decode      Export
(Python 推理)      (C 推理)
```

其中：

- **Encode / Decode** 是 Python 推理阶段的核心功能。
- **Export** 是为了兼容 `llama2.c`，将 SentencePiece 模型转换为更简单、易于 C 程序读取的二进制格式。