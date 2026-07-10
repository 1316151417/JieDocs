# FlashAttention 系列论文学习笔记（V1 / V2 / V3）

> 论文：
>
> - FlashAttention (2022)
> - FlashAttention-2 (2023)
> - FlashAttention-3 (2024)

---

# 一、FlashAttention 系列的发展路线

整个 FlashAttention 系列，并没有改变 Transformer 或 Attention 的数学公式，而是在**GPU 执行方式**上不断优化。

发展路线：

```text
Standard Attention
        │
        ▼
FlashAttention V1
Memory-aware
（减少HBM读写）

        │
        ▼
FlashAttention V2
Parallelism-aware
（提高GPU利用率）

        │
        ▼
FlashAttention V3
Hardware-aware
（充分利用Hopper新硬件）
```

一句话总结：

- V1：减少 IO
- V2：提高并行
- V3：利用新硬件

---

# 二、FlashAttention V1

## 论文解决的问题

传统 Attention：

```text
S = QKᵀ
P = softmax(S)
O = PV
```

需要保存：

```text
S (N×N)
P (N×N)
```

问题：

- Attention Matrix 非常大
- 大量写入 HBM
- GPU 大部分时间在等待显存

真正瓶颈：

> **不是算力，而是 IO。**

---

## 核心创新

### 1. IO-aware Algorithm

提出新的设计思想：

> GPU 优化不能只看 FLOPs，还要看 Memory IO。

目标：

尽可能避免：

```text
HBM

↓

SRAM

↓

HBM

↓

SRAM
```

而是：

```text
HBM

↓

SRAM

全部算完

↓

HBM
```

---

### 2. Tiling（分块计算）

Attention 不再一次计算整个矩阵。

改成：

```text
Q Block

↓

K/V Block

↓

局部计算

↓

累加输出
```

始终在 SRAM 中完成。

---

### 3. Online Softmax

难点：

Softmax：

```text
exp(x)

────────────

sum(exp(x))
```

需要知道整行数据。

解决办法：

维护：

```text
m = 当前最大值

l = 当前exp和
```

随着 Block 更新：

```text
m

↓

l

↓

Output
```

最终结果：

与普通 Softmax 完全一致。

因此：

FlashAttention：

**Exact Attention**

不是 Approximate Attention。

---

### 4. Backward Recompute

前向：

不保存：

```text
S
P
```

只保存：

```text
Output

m

l
```

反向：

重新计算 Attention。

现代 GPU：

> 多算一点，比读写大矩阵更快。

---

## 核心贡献

> 用 IO 换 FLOPs。

数学完全不变。

只是 GPU Kernel 完全重写。

---

# 三、FlashAttention V2

## V1 的问题

虽然 IO 少了。

但是：

GPU 利用率仍然不高。

例如：

```text
Tensor Core

80~90%

FlashAttention

25~40%
```

说明：

GPU 没吃满。

---

## 核心创新

### 1. Parallelize over Sequence Length

V1：

一个 Head：

对应：

```text
一个 Thread Block
```

GPU：

大量 SM 空闲。

---

V2：

一个 Head：

继续拆：

```text
Head

↓

多个 Row Block

↓

多个 Thread Block
```

于是：

GPU：

几乎全部利用。

---

### 2. Warp 划分优化

V1：

Warp 之间：

需要：

```text
同步

Shared Memory

通信
```

V2：

每个 Warp：

负责自己的 Query。

尽量：

```text
独立完成

不用同步
```

Shared Memory 通信明显减少。

---

### 3. 减少 Non-Matmul

GPU：

最擅长：

```text
MatMul
```

最慢：

```text
exp

max

softmax
```

V2：

尽量：

合并：

```text
softmax

normalize
```

减少：

非矩阵乘计算。

---

## 核心贡献

如果说：

V1：

优化：

```text
Memory
```

V2：

优化：

```text
Compute Parallelism
```

---

# 四、FlashAttention V3

## V2 的问题

H100：

Tensor Core：

理论：

```text
80~90%
```

V2：

只有：

```text
35%
```

GPU：

仍然很多时间：

在等待。

---

## 核心创新

### 1. Producer-Consumer Asynchrony

以前：

```text
Load

↓

Compute

↓

Load

↓

Compute
```

串行。

---

现在：

```text
Producer

负责：

Load

Consumer

负责：

Compute
```

两者：

异步执行。

Load 与 Compute：

重叠。

---

### 2. GEMM 与 Softmax 重叠

以前：

```text
QK

↓

softmax

↓

PV
```

必须等待。

---

V3：

重新安排执行顺序。

变成：

```text
Warp1

softmax

Warp2

QK
```

两者：

同时执行。

论文称：

> Hide Softmax under GEMM

---

### 3. Ping-Pong Scheduling

两个 WarpGroup：

交替：

```text
Warp1

GEMM

↓

Softmax

Warp2

      GEMM

           Softmax
```

Tensor Core：

几乎不停。

---

### 4. FP8 支持

H100：

新增：

FP8 Tensor Core。

理论吞吐：

约：

FP16：

2 倍。

---

但：

FP8：

误差更大。

论文：

提出：

#### Block Quantization

以前：

```text
整个 Tensor

一个 Scale
```

现在：

```text
每个 Block

一个 Scale
```

量化误差明显下降。

---

#### Incoherent Processing

LLM：

存在：

Outlier。

例如：

```text
100

0.1

0.2

0.3
```

先乘：

随机正交矩阵：

```text
M

MMᵀ = I
```

把异常值：

均匀打散。

Attention：

数学完全不变。

量化误差：

明显降低。

---

## 核心贡献

V3：

已经不仅仅是：

Attention 优化。

而是：

> GPU Kernel 与 Hopper 硬件协同设计。

---

# 五、GPU 存储层次

论文中大量提到：

## SRAM

GPU 芯片内部。

包括：

- Register
- Shared Memory
- L1 Cache

特点：

- 极快
- 极小

FlashAttention：

主要就在这里计算。

---

## HBM

GPU 显存。

例如：

```text
80GB

96GB
```

特点：

- 很大
- 比 SRAM 慢

模型参数：

激活：

KV Cache：

都主要放这里。

---

## DRAM

CPU 内存。

特点：

- 最大
- 最慢

GPU：

需要：

PCIe/NVLink：

才能访问。

---

一句话：

```text
SRAM

>>

HBM

>>

DRAM
```

FlashAttention：

核心思想：

> 尽量少访问 HBM，多利用 SRAM。

---

# 六、三篇论文贡献总结

| 版本 | 核心问题 | 核心创新 | 第一性原理 |
|------|----------|----------|------------|
| V1 | IO 太多 | Tiling + Online Softmax | Memory-aware |
| V2 | GPU 没跑满 | Parallelize over Sequence + Warp 优化 | Parallelism-aware |
| V3 | Hopper 没利用好 | Asynchrony + FP8 + Pipeline | Hardware-aware |

---

# 七、个人思考（学习过程）

## Q1：SRAM 是 CPU Cache 吗？

不是。

GPU：

也有自己的 SRAM。

主要包括：

- Register
- Shared Memory
- L1 Cache

FlashAttention 中：

SRAM：

主要就是：

GPU Shared Memory。

---

## Q2：FlashAttention 到底优化了什么？

不是：

```text
Attention 数学公式
```

而是：

```text
Attention GPU 实现方式
```

最终：

```text
softmax(QKᵀ)V
```

完全没有变化。

---

## Q3：三篇论文本质区别

可以理解成三个阶段：

第一阶段：

> 数据不要来回搬。

第二阶段：

> GPU 不要闲着。

第三阶段：

> 新硬件全部吃满。

---

# 八、一句话总结

**FlashAttention 系列不是提出了新的 Attention，而是重新发明了 Attention 在 GPU 上的执行方式。**

- **V1：重新设计内存访问（Memory）。**
- **V2：重新设计并行调度（Parallelism）。**
- **V3：重新设计软硬件协同（Hardware Co-design）。**

整个系列都遵循同一个原则：

> **数学不变，只优化执行；让 GPU 花更少时间等待数据，把更多时间用于计算。**