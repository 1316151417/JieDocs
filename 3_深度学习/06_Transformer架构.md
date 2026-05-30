# 第6章 Transformer架构

> **核心问题**：Transformer为什么能取代RNN？纯注意力架构的性能优势从何而来？

---

## 6.1 从RNN到Transformer

### 6.1.1 RNN的局限性

1. **顺序计算**：无法并行，训练慢
2. **长程依赖**：虽然LSTM缓解了梯度消失，但仍有局限
3. **信息瓶颈**：Seq2Seq将所有信息压缩到一个向量

### 6.1.2 Transformer的突破

一个完全基于注意力机制的新网络架构，完全摒弃了循环和卷积结构，在机器翻译质量上超越了基于RNN/CNN的编码器-解码器模型。

> "We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train."
> — Vaswani et al., *Attention Is All You Need* (arXiv:1706.03762)

**关键突破性成果**：

- 在WMT 2014英语-德语翻译任务上达到28.4 BLEU，超越此前最优结果（包括集成模型）超过2个BLEU点
- 在WMT 2014英语-法语翻译任务上达到41.8 BLEU，创造新的单模型最优记录
- 训练速度大幅提升，仅需8块GPU训练3.5天

> "Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation dataset, improving over the existing best results, including ensembles by over 2 BLEU."
> — Vaswani et al., *Attention Is All You Need* (arXiv:1706.03762)

**关键优势**：
- 完全并行化
- 直接建模任意距离的依赖
- 更好的长程依赖建模
- 训练成本大幅降低

---

## 6.2 自注意力机制

### 6.2.1 基本概念

**自注意力**：序列中的每个位置关注所有其他位置

**Query, Key, Value**：
- Query（查询）：当前位置想要什么信息
- Key（键）：每个位置提供什么信息
- Value（值）：每个位置的实际内容

### 6.2.2 缩放点积注意力

**公式**：
```
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V
```

**步骤**：
1. 计算相似度：`QK^T`
2. 缩放：除以 `sqrt(d_k)`（防止点积过大）
3. 归一化：softmax得到注意力权重
4. 加权求和：得到输出

### 6.2.3 为什么要缩放

**问题**：当d_k很大时，点积的方差很大

**数学推导**：
- 假设Q和K的元素独立，均值为0，方差为1
- Q dot K的方差为d_k
- 除以sqrt(d_k)后，方差变为1

---

## 6.3 多头注意力

### 6.3.1 核心思想

**问题**：单个注意力只能捕捉一种依赖关系

**解决方案**：使用多个注意力头，每个头学习不同的模式

### 6.3.2 数学公式

```
MultiHead(Q, K, V) = Concat(head_1, ..., head_h) W^O
where head_i = Attention(QW_i^Q, KW_i^K, VW_i^V)
```

### 6.3.3 实现细节

```python
class MultiHeadAttention(nn.Module):
    def __init__(self, d_model, num_heads):
        super().__init__()
        self.num_heads = num_heads
        self.d_k = d_model // num_heads

        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)

    def forward(self, Q, K, V, mask=None):
        batch_size = Q.size(0)

        # 线性变换并分头
        Q = self.W_q(Q).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        K = self.W_k(K).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)
        V = self.W_v(V).view(batch_size, -1, self.num_heads, self.d_k).transpose(1, 2)

        # 计算注意力
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = torch.softmax(scores, dim=-1)
        output = torch.matmul(attn, V)

        # 合并多头
        output = output.transpose(1, 2).contiguous().view(batch_size, -1, self.num_heads * self.d_k)
        return self.W_o(output)
```

---

## 6.4 位置编码

### 6.4.1 为什么需要位置编码

**问题**：自注意力是置换不变的，无法区分位置

**例子**：
- "猫吃鱼"和"鱼吃猫"在没有位置信息时相同

### 6.4.2 正弦位置编码

**公式**：
```
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

**特点**：
- 每个位置有唯一编码
- 可以表示相对位置（通过线性变换）
- 可以推广到更长序列

### 6.4.3 可学习位置编码

```
PE = Embedding(max_len, d_model)
```

**特点**：
- 直接学习每个位置的编码
- 通常效果与正弦编码相当
- 无法推广到训练时未见过的长度

---

## 6.5 Transformer编码器

### 6.5.1 编码器层结构

```
输入 -> 多头自注意力 -> 残差连接 + LayerNorm -> 前馈网络 -> 残差连接 + LayerNorm -> 输出
```

### 6.5.2 前馈网络

```
FFN(x) = max(0, xW_1 + b_1)W_2 + b_2
```

**特点**：
- 两层全连接网络
- 中间维度通常是d_model的4倍
- 使用ReLU或GELU激活

### 6.5.3 残差连接和LayerNorm

**残差连接**：
```
output = LayerNorm(x + Sublayer(x))
```

**LayerNorm**：
```
LN(x) = gamma * (x - mu) / sigma + beta
```

**为什么用LayerNorm而不是BatchNorm**：
- 序列长度可变
- BatchNorm在序列维度上不稳定

---

## 6.6 Transformer解码器

### 6.6.1 解码器层结构

```
输入 -> 掩码多头自注意力 -> 残差连接 + LayerNorm ->
交叉注意力（关注编码器输出）-> 残差连接 + LayerNorm ->
前馈网络 -> 残差连接 + LayerNorm -> 输出
```

### 6.6.2 掩码自注意力

**目的**：防止看到未来的信息

**实现**：
```
mask = torch.triu(torch.ones(seq_len, seq_len), diagonal=1).bool()
scores = scores.masked_fill(mask, -1e9)
```

### 6.6.3 交叉注意力

**Query**：来自解码器
**Key, Value**：来自编码器

```
Q = decoder_output
K = encoder_output
V = encoder_output
```

---

## 6.7 完整的Transformer架构

### 6.7.1 原始架构

```
输入序列 -> [编码器xN] -> 编码器输出
目标序列 -> [解码器xN] -> 输出概率
```

### 6.7.2 超参数

| 参数 | 原始论文 | 说明 |
|------|----------|------|
| d_model | 512 | 模型维度 |
| num_heads | 8 | 注意力头数 |
| d_ff | 2048 | 前馈网络中间维度 |
| num_layers | 6 | 编码器/解码器层数 |
| dropout | 0.1 | Dropout率 |

---

## 6.8 Transformer的变体

### 6.8.1 只有编码器：BERT

**特点**：
- 双向注意力
- 预训练任务：掩码语言模型
- 适合理解任务

### 6.8.2 只有解码器：GPT

**特点**：
- 单向注意力（掩码）
- 预训练任务：预测下一个词
- 适合生成任务

### 6.8.3 编码器-解码器：T5

**特点**：
- 保留原始架构
- 统一文本到文本框架
- 适合各种任务

### 6.8.4 线性注意力变体

**问题**：标准注意力复杂度O(n^2)

**解决方案**：
- Linear Transformer：O(n)复杂度
- Performer：使用随机特征近似
- Flash Attention：优化内存访问模式

---

## 6.9 Transformer的计算复杂度

### 6.9.1 自注意力复杂度

**时间和空间**：O(n^2 * d)

其中n是序列长度，d是模型维度。

**问题**：长序列计算成本高

### 6.9.2 优化方法

1. **稀疏注意力**：只关注部分位置
2. **线性注意力**：使用核函数近似
3. **分块处理**：将序列分成块
4. **Flash Attention**：优化GPU内存访问

---

## 6.10 实践示例：用PyTorch实现Transformer

```python
import torch
import torch.nn as nn
import math

class TransformerEncoder(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, num_layers, dropout=0.1):
        super().__init__()
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(d_model, num_heads, d_ff, dropout)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x, mask=None):
        for layer in self.layers:
            x = layer(x, mask)
        return self.norm(x)

class TransformerEncoderLayer(nn.Module):
    def __init__(self, d_model, num_heads, d_ff, dropout):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, num_heads, dropout=dropout)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x, mask=None):
        # 自注意力
        attn_output, _ = self.self_attn(x, x, x, attn_mask=mask)
        x = self.norm1(x + self.dropout(attn_output))

        # 前馈网络
        ffn_output = self.ffn(x)
        x = self.norm2(x + self.dropout(ffn_output))
        return x
```

---

## 6.11 本章小结

| 要点 | 内容 |
|------|------|
| 核心创新 | 完全基于注意力机制，摒弃循环和卷积 |
| 翻译性能 | WMT 2014 EN-DE: 28.4 BLEU (超越集成模型2+ BLEU), EN-FR: 41.8 BLEU |
| 自注意力 | 序列内任意位置的直接连接 |
| 多头注意力 | 捕捉不同类型的依赖关系 |
| 位置编码 | 注入位置信息 |
| 复杂度 | O(n^2)，需要优化 |

---

## 延伸阅读

1. **Vaswani, A., et al.** (2017). Attention is all you need. *NeurIPS*.
   - Transformer的原始论文，深度学习历史上最具影响力的论文之一
   - [https://arxiv.org/abs/1706.03762](https://arxiv.org/abs/1706.03762)

2. **Devlin, J., et al.** (2019). BERT: Pre-training of deep bidirectional transformers for language understanding.
   - BERT的原始论文
   - [https://arxiv.org/abs/1810.04805](https://arxiv.org/abs/1810.04805)

3. **Radford, A., et al.** (2018). Improving language understanding by generative pre-training.
   - GPT的原始论文

4. **Dao, T., et al.** (2022). FlashAttention: Fast and memory-efficient exact attention with IO-awareness.
   - Flash Attention的论文
   - [https://arxiv.org/abs/2205.14135](https://arxiv.org/abs/2205.14135)
