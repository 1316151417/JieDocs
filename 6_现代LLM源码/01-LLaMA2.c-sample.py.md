# sample.py 学习笔记（LLaMA 推理流程）

## 文件作用

`sample.py` 是一个完整的 **LLM 推理（Inference）示例**。

它负责完成整个推理流程：

```text
加载训练好的模型
        ↓
加载 Tokenizer
        ↓
Prompt 编码（Encode）
        ↓
Transformer 自回归生成
        ↓
Token 解码（Decode）
        ↓
输出文本
```

整个流程对应 LLM 推理的完整闭环。

---

# 整体执行流程

```text
导入依赖
    ↓
配置推理参数
    ↓
设置随机种子、设备
    ↓
加载 checkpoint
    ↓
恢复模型结构
    ↓
加载模型权重
    ↓
切换推理模式
    ↓
加载 Tokenizer
    ↓
Prompt 编码
    ↓
generate()
    ↓
Decode 输出
```

---

# 第一部分：导入依赖

```python
import torch
from model import ModelArgs, Transformer
from tokenizer import Tokenizer
```

主要依赖：

| 模块 | 作用 |
|------|------|
| torch | PyTorch 推理 |
| ModelArgs | 模型配置 |
| Transformer | LLaMA 模型 |
| Tokenizer | SentencePiece Tokenizer |

---

# 第二部分：配置推理参数

```python
checkpoint = 'out/ckpt.pt'
start = ""
num_samples = 1
max_new_tokens = 100
temperature = 1.0
top_k = 300
device = ...
dtype = ...
compile = False
```

这一部分定义：

**模型如何进行生成。**

常用参数：

| 参数 | 含义 |
|------|------|
| checkpoint | 模型权重文件 |
| start | Prompt |
| num_samples | 生成几条 |
| max_new_tokens | 最大生成 Token 数 |
| temperature | 随机程度 |
| top_k | Top-K Sampling |
| device | CPU / GPU |
| dtype | 推理精度 |
| compile | 是否使用 PyTorch Compile |

其中：

```python
exec(open("configurator.py").read())
```

允许：

```bash
python sample.py --temperature=0.7
```

直接覆盖这些参数。

---

# 第三部分：初始化运行环境

包括：

```python
torch.manual_seed(...)
torch.cuda.manual_seed(...)
```

作用：

- 固定随机种子
- 保证生成结果尽可能可复现

然后：

```python
ctx = autocast(...)
```

作用：

根据设备决定是否启用：

> Automatic Mixed Precision（AMP）

GPU 推理可降低显存并提高速度。

---

# 第四部分：加载 Checkpoint

```python
checkpoint_dict = torch.load(...)
```

读取：

```
out/ckpt.pt
```

Checkpoint 一般包含：

```text
{
    model_args
    model
    optimizer
    config
}
```

本文件主要使用：

- model_args
- model
- config

---

# 第五部分：恢复模型结构

```python
gptconf = ModelArgs(**checkpoint_dict['model_args'])
model = Transformer(gptconf)
```

注意：

Checkpoint 不保存模型对象。

Checkpoint 只保存：

```text
模型配置
+
模型权重
```

因此必须：

先恢复模型结构：

```text
Transformer(...)
```

再加载权重。

---

# 第六部分：加载模型权重

```python
state_dict = checkpoint_dict["model"]
```

得到：

```text
{
layers.0.attention.wq.weight
layers.0.feed_forward.w1.weight
...
}
```

即：

整个模型所有参数。

随后：

```python
model.load_state_dict(...)
```

将权重加载进模型。

---

## 为什么要删除 `_orig_mod.`？

```python
_orig_mod.layers.0...
```

这是：

PyTorch Compile 保存模型时产生的前缀。

当前模型名称没有：

```
_orig_mod.
```

因此需要：

```python
删除前缀
```

否则：

模型名字无法匹配。

---

# 第七部分：进入推理模式

```python
model.eval()
```

作用：

关闭训练行为：

例如：

- Dropout
- BatchNorm 更新

然后：

```python
model.to(device)
```

将模型放到：

- CPU
- GPU

---

# 第八部分：加载 Tokenizer

```python
enc = Tokenizer(...)
```

Tokenizer 负责：

```text
文本
↓

Token ID

↓

文本
```

如果没有指定：

```python
tokenizer=""
```

则：

自动根据：

- vocab_source
- vocab_size

寻找对应：

```
tokenizer.model
```

---

# 第九部分：Prompt 编码

如果：

```python
start="FILE:prompt.txt"
```

先读取文件。

否则：

直接编码：

```python
start_ids = enc.encode(...)
```

例如：

```
Hello
```

可能变成：

```
[1, 15043]
```

其中：

```
1 = BOS
```

随后：

```python
torch.tensor(...)
```

转换为：

```
shape:

[batch, seq_len]
```

例如：

```
[1, 12]
```

---

# 第十部分：开始生成

```python
with torch.no_grad():
```

表示：

> 推理阶段，不计算梯度。

随后：

```python
model.generate(...)
```

真正进入：

LLM 自回归生成。

---

## generate() 的工作流程

假设：

Prompt：

```
The cat
```

流程：

```text
The cat

↓

预测：

sat

↓

The cat sat

↓

预测：

on

↓

The cat sat on

↓

预测：

the

↓

...
```

即：

```text
输入
↓

预测下一个 Token

↓

拼接到输入

↓

继续预测

↓

直到：

EOS

或

达到 max_new_tokens
```

这就是：

**Autoregressive Generation（自回归生成）。**

---

# 第十一部分：Decode

generate 返回：

```python
y
```

例如：

```
[1, 100, 300, 25, 9]
```

随后：

```python
enc.decode(...)
```

恢复成：

```
The cat sat.
```

最后：

```python
print(...)
```

输出到终端。

---

# 推理流程总结

```text
Prompt
    │
    ▼
Tokenizer.encode()
    │
    ▼
Token IDs
    │
    ▼
Transformer.forward()
    │
    ▼
Next Token
    │
    ▼
Sampling
(temperature / top_k)
    │
    ▼
Append Token
    │
    ├──────────────┐
    │              │
    └────继续生成───┘
    │
    ▼
Tokenizer.decode()
    │
    ▼
最终文本
```

---

# sample.py 核心模块总结

| 模块 | 作用 |
|------|------|
| 参数配置 | 定义推理行为（temperature、top_k 等） |
| 初始化环境 | 设置随机种子、设备、AMP |
| 加载 Checkpoint | 读取模型配置和权重 |
| 构建模型 | 根据 `model_args` 恢复 Transformer |
| 加载权重 | `load_state_dict()` |
| 推理模式 | `eval()` + `to(device)` |
| 加载 Tokenizer | 加载 SentencePiece |
| Prompt 编码 | 文本 → Token IDs |
| Generate | 自回归生成 Token |
| Decode | Token IDs → 文本 |

---

# 核心思想

整个 `sample.py` 可以浓缩为下面几步：

```text
加载模型
    ↓
加载 Tokenizer
    ↓
Encode Prompt
    ↓
Transformer Generate
    ↓
Decode
    ↓
输出文本
```

它体现了现代大语言模型推理的标准流程，也是 GPT、LLaMA、Qwen、DeepSeek 等模型推理代码的基本框架。