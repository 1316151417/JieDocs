这段代码实现的是一个**简化版 LLaMA Decoder-only Transformer**，核心执行链路是：

```text
输入 token id
→ token embedding
→ 多层 TransformerBlock
   → RMSNorm
   → Attention：QKV / RoPE / GQA / Causal Attention
   → 残差连接
   → RMSNorm
   → SwiGLU FFN
   → 残差连接
→ 最终 RMSNorm
→ Linear 输出 vocab logits
→ 训练时算 loss / 推理时只算最后一个 token
```

---

## **1. ModelArgs：模型配置**

```python
@dataclass
class ModelArgs:
```

这是模型超参数配置。

主要字段：

```text
dim = 4096              每个 token 的隐藏向量维度
n_layers = 32           Transformer 层数
n_heads = 32            Query 头数
n_kv_heads = None       Key/Value 头数，None 表示普通 MHA
vocab_size = 32000      词表大小
hidden_dim = None       FFN 中间层维度
max_seq_len = 2048      最大上下文长度
dropout = 0.0           dropout 概率
```

如果 `n_kv_heads < n_heads`，就是 GQA / MQA 结构。

---

## **2. RMSNorm：归一化层**

```python
class RMSNorm(torch.nn.Module):
```

LLaMA 不用 LayerNorm，而用 RMSNorm。

输入：

```text
x: [batch, seq_len, dim]
```

核心计算：

```python
x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + eps)
```

意思是：只用均方根做归一化，不减均值。

然后乘一个可学习参数：

```python
return output * self.weight
```

所以 RMSNorm 的作用是：

```text
稳定每层输入的数值尺度
减少训练不稳定
比 LayerNorm 更简单、更快
```

---

## **3. precompute_freqs_cis：提前算 RoPE 频率**

```python
def precompute_freqs_cis(dim, end, theta=10000.0):
```

这里提前生成 RoPE 需要的：

```text
freqs_cos
freqs_sin
```

形状大致是：

```text
[max_seq_len, head_dim / 2]
```

为什么是 `head_dim / 2`？

因为 RoPE 把向量两两一组看成二维平面，然后做旋转：

```text
(x0, x1), (x2, x3), ...
```

每一对维度使用一个旋转频率。

---

## **4. apply_rotary_emb：给 Q 和 K 加 RoPE**

```python
def apply_rotary_emb(xq, xk, freqs_cos, freqs_sin):
```

输入：

```text
xq: [batch, seq_len, n_heads, head_dim]
xk: [batch, seq_len, n_kv_heads, head_dim]
```

先把最后一维拆成二元组：

```python
reshape(..., (-1, 2))
```

例如：

```text
head_dim = 128
→ 变成 64 组二维向量
```

然后执行二维旋转：

```text
real' = real * cos - imag * sin
imag' = real * sin + imag * cos
```

这就是 RoPE 的核心。

RoPE 只加在：

```text
Q 和 K
```

不加在 V 上。

原因是 attention 分数来自：

```text
Q · K
```

位置关系需要影响注意力权重，而 V 是被加权聚合的内容，不负责算位置相关性。

---

## **5. repeat_kv：GQA / MQA 的 KV 头复制**

```python
def repeat_kv(x, n_rep):
```

如果：

```text
n_heads = 32
n_kv_heads = 8
```

那么：

```text
每 1 个 KV head 共享给 4 个 Q head
```

`repeat_kv` 做的就是把 KV head 复制成和 Q head 数量一致。

输入：

```text
[batch, seq_len, n_kv_heads, head_dim]
```

输出：

```text
[batch, seq_len, n_heads, head_dim]
```

本质是：

```text
计算 Q 的头很多
但 K/V 的头较少
节省 K/V 投影参数和推理 KV Cache
```

---

## **6. Attention：自注意力模块**

```python
class Attention(nn.Module):
```

这是 LLaMA 的注意力层。

初始化里创建四个线性层：

```python
self.wq
self.wk
self.wv
self.wo
```

含义：

```text
wq: hidden → Q
wk: hidden → K
wv: hidden → V
wo: 多头结果 → hidden
```

### **6.1 forward：输入进入注意力**

输入：

```text
x: [batch, seq_len, dim]
```

先算 QKV：

```python
xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)
```

然后 reshape 成多头形式：

```text
xq: [batch, seq_len, n_heads, head_dim]
xk: [batch, seq_len, n_kv_heads, head_dim]
xv: [batch, seq_len, n_kv_heads, head_dim]
```

---

### **6.2 给 Q/K 加 RoPE**

```python
xq, xk = apply_rotary_emb(xq, xk, freqs_cos, freqs_sin)
```

RoPE 加完后，Q/K 已经包含位置信息。

---

### **6.3 如果是 GQA，复制 KV**

```python
xk = repeat_kv(xk, self.n_rep)
xv = repeat_kv(xv, self.n_rep)
```

把 KV head 数量扩展到和 Q head 一样。

---

### **6.4 调整维度，准备算 attention**

```python
xq = xq.transpose(1, 2)
```

从：

```text
[batch, seq_len, heads, head_dim]
```

变成：

```text
[batch, heads, seq_len, head_dim]
```

这样方便做矩阵乘法。

---

### **6.5 Flash Attention 分支**

如果 PyTorch 支持：

```python
scaled_dot_product_attention(...)
```

就直接调用官方实现：

```python
is_causal=True
```

这表示每个 token 只能看自己和前面的 token，不能看未来 token。

这是 Decoder-only 模型的核心约束。

---

### **6.6 手写 Attention 分支**

如果没有 Flash Attention，就手写：

```python
scores = torch.matmul(xq, xk.transpose(2, 3)) / math.sqrt(self.head_dim)
```

得到注意力分数：

```text
[batch, heads, seq_len, seq_len]
```

然后加 causal mask：

```python
scores = scores + mask
```

未来位置被加上 `-inf`，softmax 后概率变成 0。

然后：

```python
scores = softmax(scores)
output = scores @ xv
```

得到每个 token 聚合后的上下文向量。

---

### **6.7 多头合并**

```python
output = output.transpose(1, 2).contiguous().view(bsz, seqlen, -1)
```

从：

```text
[batch, heads, seq_len, head_dim]
```

恢复为：

```text
[batch, seq_len, dim]
```

最后经过输出投影：

```python
output = self.wo(output)
```

---

## **7. FeedForward：SwiGLU 前馈网络**

```python
class FeedForward(nn.Module):
```

LLaMA 的 FFN 不是普通的：

```text
Linear → GELU → Linear
```

而是 SwiGLU：

```python
self.w2(F.silu(self.w1(x)) * self.w3(x))
```

结构是：

```text
x
→ w1(x) → SiLU
→ 与 w3(x) 相乘
→ w2 投影回 dim
```

也就是：

```text
FFN(x) = W2( SiLU(W1x) * W3x )
```

其中：

```text
w1 是激活分支
w3 是门控分支
w2 是输出投影
```

`hidden_dim` 的默认计算：

```python
hidden_dim = 4 * dim
hidden_dim = int(2 * hidden_dim / 3)
hidden_dim = multiple_of * ceil(hidden_dim / multiple_of)
```

这是为了让 SwiGLU 的参数量大致接近普通 FFN，同时满足硬件友好的对齐倍数。

---

## **8. TransformerBlock：一个完整 Decoder Block**

```python
class TransformerBlock(nn.Module):
```

一个 block 包含：

```text
RMSNorm
Attention
残差连接
RMSNorm
FeedForward
残差连接
```

执行顺序：

```python
h = x + self.attention(self.attention_norm(x), freqs_cos, freqs_sin)
out = h + self.feed_forward(self.ffn_norm(h))
```

也就是 Pre-Norm 结构：

```text
x
→ RMSNorm
→ Attention
→ + x

→ RMSNorm
→ FFN
→ + h
```

这里不是 Post-Norm。

Pre-Norm 对深层 Transformer 更稳定。

---

## **9. Transformer：完整模型**

```python
class Transformer(nn.Module):
```

初始化时创建：

```python
self.tok_embeddings
self.layers
self.norm
self.output
```

对应：

```text
token embedding
多层 TransformerBlock
最终 RMSNorm
输出 vocab logits 的线性层
```

---

## **10. 权重绑定：Embedding 和输出层共享参数**

```python
self.tok_embeddings.weight = self.output.weight
```

这叫 weight tying。

含义是：

```text
输入 token embedding 矩阵
和输出 token classifier 矩阵
共享同一份参数
```

好处：

```text
减少参数量
提升输入/输出词向量空间一致性
```

注意：代码里这行写法有点反直觉，更常见的是：

```python
self.output.weight = self.tok_embeddings.weight
```

但本质都是让两者指向同一个参数对象。

---

## **11. RoPE 预计算并注册为 buffer**

```python
freqs_cos, freqs_sin = precompute_freqs_cis(...)
self.register_buffer("freqs_cos", freqs_cos, persistent=False)
self.register_buffer("freqs_sin", freqs_sin, persistent=False)
```

这表示：

```text
freqs_cos / freqs_sin 不是模型参数
不参与训练
但会跟随模型移动到 GPU
```

`persistent=False` 表示保存 checkpoint 时不保存它们，因为可以重新计算。

---

## **12. 权重初始化**

```python
self.apply(self._init_weights)
```

对 Linear 和 Embedding 做正态初始化：

```text
mean = 0
std = 0.02
```

然后对部分残差投影做缩放初始化：

```python
if pn.endswith('w3.weight') or pn.endswith('wo.weight'):
    std = 0.02 / sqrt(2 * n_layers)
```

这里意图是让深层残差网络更稳定。

不过有个细节：LLaMA / GPT-2 风格通常重点缩放的是残差分支的输出投影，例如：

```text
attention.wo
ffn.w2
```

这段代码缩放了：

```text
w3 和 wo
```

更合理的写法通常应该是缩放：

```text
w2.weight
wo.weight
```

因为 `w2` 才是 FFN 的输出投影。

---

## **13. forward：训练和推理主流程**

```python
def forward(self, tokens, targets=None):
```

输入：

```text
tokens: [batch, seq_len]
```

### **13.1 token id → embedding**

```python
h = self.tok_embeddings(tokens)
```

变成：

```text
[batch, seq_len, dim]
```

---

### **13.2 取当前长度需要的 RoPE**

```python
freqs_cos = self.freqs_cos[:seqlen]
freqs_sin = self.freqs_sin[:seqlen]
```

只取当前序列长度对应的位置编码。

---

### **13.3 逐层经过 TransformerBlock**

```python
for layer in self.layers:
    h = layer(h, freqs_cos, freqs_sin)
```

每一层都做：

```text
Attention + FFN
```

---

### **13.4 最终归一化**

```python
h = self.norm(h)
```

得到最终 hidden states：

```text
[batch, seq_len, dim]
```

---

### **13.5 训练模式：输出所有位置 logits 并计算 loss**

如果传入了 `targets`：

```python
logits = self.output(h)
```

输出：

```text
[batch, seq_len, vocab_size]
```

然后计算交叉熵：

```python
F.cross_entropy(
    logits.view(-1, vocab_size),
    targets.view(-1),
    ignore_index=-1
)
```

这是标准 next-token prediction。

通常：

```text
tokens  = [x0, x1, x2, x3]
targets = [x1, x2, x3, x4]
```

模型在每个位置预测下一个 token。

---

### **13.6 推理模式：只输出最后一个位置**

如果没有传 `targets`：

```python
logits = self.output(h[:, [-1], :])
```

只对最后一个 token 的 hidden state 做输出层。

原因是生成时只关心：

```text
下一个 token 是什么
```

不需要重新输出所有位置的 logits。

输出形状仍然保留时间维：

```text
[batch, 1, vocab_size]
```

---

## **14. configure_optimizers：构建 AdamW 优化器**

```python
def configure_optimizers(...)
```

它把参数分成两组：

### **需要 weight decay 的参数**

```python
p.dim() >= 2
```

主要是：

```text
Linear weight
Embedding weight
```

### **不需要 weight decay 的参数**

```python
p.dim() < 2
```

主要是：

```text
RMSNorm weight
bias
```

然后创建 AdamW：

```python
torch.optim.AdamW(...)
```

如果是 CUDA，并且 PyTorch 支持 fused AdamW，就启用：

```python
fused=True
```

---

## **15. estimate_mfu：估算训练吞吐效率**

```python
def estimate_mfu(self, fwdbwd_per_iter, dt):
```

MFU 是：

```text
Model FLOPs Utilization
```

意思是模型实际用掉了硬件峰值算力的多少比例。

这里用 PaLM 论文里的粗略公式估计：

```text
每 token FLOPs ≈ 6N + 12LHQT
```

然后和 A100 BF16 峰值：

```text
312 TFLOPS
```

做比较。

这只是训练性能估算工具，不影响模型结果。

---

## **16. generate：自回归生成**

```python
@torch.inference_mode()
def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
```

输入：

```text
idx: [batch, 当前 token 数]
```

循环生成 `max_new_tokens` 次。

每一步：

### **16.1 截断上下文**

```python
idx_cond = idx if idx.size(1) <= max_seq_len else idx[:, -max_seq_len:]
```

超过最大上下文就只保留最后 `max_seq_len` 个 token。

---

### **16.2 前向计算最后 token 的 logits**

```python
logits = self(idx_cond)
logits = logits[:, -1, :]
```

得到：

```text
[batch, vocab_size]
```

---

### **16.3 选择下一个 token**

如果：

```python
temperature == 0.0
```

用贪心搜索：

```text
选择概率最高的 token
```

否则：

```python
logits = logits / temperature
```

temperature 控制随机性：

```text
temperature 越低：越保守
temperature 越高：越随机
```

如果设置了 `top_k`：

```python
只保留概率最高的 k 个 token
```

然后 softmax，采样：

```python
idx_next = torch.multinomial(probs, num_samples=1)
```

---

### **16.4 拼接到序列后面**

```python
idx = torch.cat((idx, idx_next), dim=1)
```

然后进入下一轮。

最终返回完整序列：

```text
原始 prompt + 新生成 token
```

---

## **17. 总执行顺序汇总**

训练时：

```text
tokens
→ Embedding
→ Dropout
→ 取 RoPE cos/sin
→ Block 1
   → RMSNorm
   → QKV
   → RoPE(Q, K)
   → repeat KV
   → causal attention
   → output projection
   → residual
   → RMSNorm
   → SwiGLU FFN
   → residual
→ Block 2
→ ...
→ Block N
→ final RMSNorm
→ output linear
→ logits
→ cross entropy loss
```

推理生成时：

```text
prompt tokens
→ forward
→ 得到最后位置 logits
→ temperature / top-k
→ 采样 next token
→ 拼回输入
→ 重复
```

---

## **18. 这份代码和真实 LLaMA 的主要差异**

核心结构接近 LLaMA，但不是完整生产版。

主要差异：

```text
1. generate 没有 KV Cache，所以生成很慢
2. 没有加载官方权重逻辑
3. 没有 tokenizer 部分
4. 没有模型并行
5. RoPE 没有支持超长上下文扩展
6. 初始化细节和真实 LLaMA 不完全一致
7. dropout 默认 0，但代码保留了 dropout
8. attention 使用 PyTorch SDPA，而不是手写完整 FlashAttention 内核
```

这段代码最适合用来学习：

```text
LLaMA 的模型结构
RoPE
RMSNorm
GQA/MQA
SwiGLU
Decoder-only 自回归生成
```

核心可以记成一句话：

```text
这是一个 Pre-Norm Decoder-only Transformer：每层先 RMSNorm，再做因果自注意力和 SwiGLU 前馈网络，位置编码用 RoPE，KV 可以用 GQA 共享，最后用 tied embedding 输出下一个 token 概率。
```