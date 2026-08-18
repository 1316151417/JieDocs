# LLM 推理系统与 KV Cache

## 1. 解决的问题

在模型参数固定后，以尽可能低的延迟、显存和计算成本为一个或多个请求生成 Token。

---

## 2. 定义

**LLM 推理系统是负责模型加载、Prompt 计算、自回归解码、缓存管理、请求调度和资源利用的运行系统。**

---

## 3. 核心机制：Prefill 与 Decode

### 3.1 Prefill

**Prefill 是一次处理 Prompt 全部 Token，并为各层建立初始 KV Cache 的阶段。**

特点：

- 输入 Token 数多。
- Attention 需要处理 Prompt 内部的上下文关系。
- 矩阵计算并行度较高。
- 首 Token 延迟受 Prompt 长度影响。

### 3.2 Decode

**Decode 是在已有缓存基础上，每一步输入一个新 Token 并生成下一个 Token 的阶段。**

特点：

- 必须逐步执行。
- 每步读取大量模型参数和历史 KV。
- 单步计算规模较小但内存访问压力高。

---

## 4. KV Cache

### 4.1 解决的问题

如果每生成一个 Token 都重新计算全部历史 Token 在每层的 Key 和 Value，会产生大量重复计算。

### 4.2 定义

**KV Cache 是保存每一层历史 Token 的 Key 和 Value，使后续解码只需计算新 Token 的 Q、K、V 的缓存。**

历史缓存可抽象为：

$$
K_{\text{cache}}
\in
\mathbb R^{B\times H_{kv}\times T\times d_h}
$$

$$
V_{\text{cache}}
\in
\mathbb R^{B\times H_{kv}\times T\times d_h}
$$

新 Token 的 Query 与全部历史 Key 计算注意力，再汇总历史 Value。

### 4.3 显存规模

KV Cache 大小近似正比于：

$$
2
\times
L
\times
T
\times
H_{kv}
\times
d_h
\times
\text{每元素字节数}
$$

还要乘以并发序列数。

其中 $2$ 表示 Key 和 Value。

上下文越长、并发越高，KV Cache 显存越大。

### 4.4 GQA/MQA

减少 KV 头数量 $H_{kv}$ 可以显著降低 KV Cache。

因此 GQA 和 MQA 主要改善长上下文和高并发推理效率。

---

## 5. 延迟与吞吐

### 5.1 延迟

用户关心：

- Time to First Token：从请求到首 Token。
- Time per Output Token：后续每个 Token 的时间。
- 总响应时间。

### 5.2 吞吐

系统关心单位时间能够处理的：

- 输入 Token。
- 输出 Token。
- 请求数量。

提高 Batch Size 通常能提高吞吐，但可能增加单请求等待和延迟。

---

## 6. Continuous Batching

### 6.1 定义

**Continuous Batching 是在每个解码步动态加入新请求、移除已完成请求，使设备持续处理有效序列的调度方式。**

它避免必须等待同一静态 Batch 中最长请求完成。

---

## 7. KV Cache 内存管理

不同请求长度不断变化，如果为每个请求预留最大连续空间，会浪费显存并产生碎片。

推理系统可以把 KV Cache 分页或分块管理：

- 按需分配。
- 非连续物理块映射为逻辑连续序列。
- 请求完成后快速回收。

核心目标是提高可用显存比例和并发能力。

---

## 8. 量化

### 8.1 定义

**量化是使用更低位宽表示权重、激活或 KV Cache，以减少存储、带宽和计算成本。**

常见对象包括：

- Weight-only 量化。
- 权重和激活量化。
- KV Cache 量化。

### 8.2 权衡

位宽越低：

- 显存和带宽通常越低。
- 支持的并发或模型规模越高。
- 数值误差和能力下降风险越大。

量化效果取决于模型、层、校准数据、硬件和 Kernel 支持，不能只看标称位宽。

---

## 9. 推理的主要瓶颈

- Prefill：长 Prompt 的 Attention 和大矩阵计算。
- Decode：逐 Token 顺序依赖、参数读取和 KV Cache 访问。
- 高并发：KV Cache 显存与调度。
- 大模型：参数显存和跨设备通信。

训练优化和推理优化关注的瓶颈并不完全相同。

---

## 10. 核心本质

**LLM 推理通过 Prefill 建立上下文缓存，再利用 KV Cache 逐 Token Decode，并在延迟、吞吐、显存和精度之间进行系统级权衡。**
