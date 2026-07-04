
> 论文：GLU Variants Improve Transformer（Noam Shazeer，2020）
>
> 一句话总结：
>
> **这篇论文并不是提出了一种新的激活函数，而是提出了一种新的 FFN（Feed Forward Network）结构：双路投影 + 乘性交互（Multiplicative Interaction）。**

---

# 一、论文背景

Transformer 的 FFN（GPT-1/2/3 使用）：

```text
x
 ↓
Linear
 ↓
GELU
 ↓
Linear
```

数学形式：

```
FFN(x) = W₂ · GELU(W₁x)
```

整个 FFN 只有一条计算路径：

> Linear → 激活函数 → Linear

---

# 二、论文真正的创新

论文不是改进 GELU。

而是把 FFN 改成了：

```text
           Gate 分支
        x ──Linear(W)──Swish
             │
             ▼
             ×
             ▲
        x ──Linear(V)
          Feature 分支

               │
           Linear(W₂)
```

数学形式：

```
Feature = xV

Gate = Swish(xW)

Output = (Feature × Gate) W₂
```

其中：

- Feature：负责学习特征表达
- Gate：负责学习如何调制（Modulate）这些特征

最终逐元素相乘（Element-wise Multiply）。

---

# 三、GLU、GEGLU、SwiGLU 到底是什么？

很多文章容易误导。

实际上：

它们都不是新的激活函数。

而是新的 FFN 结构。

| 名称 | 是激活函数？ | 本质 |
|-------|------------|------|
| ReLU | ✅ | 激活函数 |
| GELU | ✅ | 激活函数 |
| Swish | ✅ | 激活函数 |
| GLU | ❌ | 门控 FFN |
| GEGLU | ❌ | 使用 GELU 作为 Gate 的 FFN |
| SwiGLU | ❌ | 使用 Swish 作为 Gate 的 FFN |

所以：

SwiGLU ≠ 新激活函数

而是：

> **带 Swish 门控的 FFN。**

---

# 四、为什么要增加一条 Gate 分支？

传统 FFN：

```text
Feature
 ↓
GELU
```

只有：

一套 Linear 参数。

需要同时完成：

- 学习特征
- 判断特征重要性

所有能力都压在：

```
W₁
```

这一套参数上。

---

SwiGLU：

拆成两条路：

```text
Feature

↓

学习"内容"
```

```text
Gate

↓

学习"如何调制内容"
```

职责分离。

因此：

表达能力更强。

---

# 五、真正的创新不是 Gate，而是 Dual Projection

学习过程中最大的误区：

> Gate 能看到更多全局信息。

后来分析发现：

**这个理解是不准确的。**

原因：

普通 GELU：

```
z = xW₁
```

本身：

就是全连接。

每一个神经元：

已经能够看到：

整个输入向量。

因此：

GELU 本来就是利用全局信息计算出来的。

所以：

> GLU 并不是因为看到了更多信息。

---

真正的创新：

是：

以前：

```text
x

↓

一个 Projection

↓

Feature
```

现在：

```text
x

├──Projection₁

└──Projection₂
```

两套独立参数：

分别学习：

不同表示。

论文真正增加的是：

> **第二套 Projection。**

---

# 六、真正提升表达能力的原因

传统 FFN：

```
f(x)=W₂·GELU(W₁x)
```

整个模型：

只有：

一个 Projection。

---

SwiGLU：

```
f(x)=W₂[(xV)⊙Swish(xW)]
```

第一次出现：

```
Projection₁

×

Projection₂
```

即：

两个不同特征之间：

发生乘性交互（Multiplicative Interaction）。

这是表达能力提升的核心。

---

# 七、为什么乘性交互更强？

以前：

只有：

```text
Feature

↓

非线性
```

现在：

变成：

```text
Feature

×

Gate
```

意味着：

输出：

不再只依赖：

一个特征。

而是：

依赖：

两个独立学习出的特征之间的关系。

例如：

```
Feature：

"苹果公司"

=

10
```

```
Gate：

"科技上下文"

=

0.1
```

输出：

```
1
```

如果：

```
Gate：

0.9
```

输出：

```
9
```

因此：

模型能够学习：

更多条件关系（Conditional Relationship）。

---

# 八、和 Attention 的思想非常类似

Attention：

不是：

```
Q

↓

Linear
```

而是：

```
Q × K
```

两个 Projection：

发生交互。

---

SwiGLU：

同样：

不是：

```
Feature

↓

激活函数
```

而是：

```
Feature × Gate
```

本质思想：

一致。

都是：

> Multiplicative Interaction（乘性交互）。

---

# 九、为什么现代 LLM 都使用 SwiGLU？

代表模型：

- PaLM
- LLaMA
- Qwen
- DeepSeek
- Gemma

原因：

相比传统 FFN：

优点：

✅ 更强表达能力

✅ 参数几乎不增加（隐藏层缩放到约 2/3）

✅ FLOPs 基本一致

✅ 实现简单

几乎属于：

> 免费提升。

---

# 十、个人学习过程中最大的收获

## 误区一：

> SwiGLU 是新的激活函数。

错误。

实际上：

它是一种新的 FFN。

---

## 误区二：

> Gate 能看到更多全局信息。

也不准确。

因为：

普通 GELU 前面的 Linear：

本来就是全连接。

每个神经元：

已经利用了整个输入。

---

## 真正理解后的本质

论文真正创新：

不是：

> 更换激活函数。

不是：

> Gate。

而是：

> **把 FFN 从"单路非线性映射"升级成"双路 Projection + 乘性交互"。**

其中：

- 两个 Projection（Feature / Gate）分别学习不同表示。
- 两者逐元素相乘，实现更丰富的条件建模。
- Gate 使用什么激活函数（Sigmoid、GELU、Swish）只是具体实现细节。

---

# 一句话总结

> **GLU Variants Improve Transformer 的本质，不是发明了新的激活函数，而是让 FFN 从"Linear → 激活 → Linear"演化为"Dual Projection + Multiplicative Interaction"，利用两套独立学习到的特征进行乘性交互，从而显著增强模型表达能力，而几乎不增加计算成本。**