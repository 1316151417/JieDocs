# LLM 强化学习基础

## 1. 解决的问题

直接根据完整回答获得的奖励优化语言模型，而不要求为每个 Token 提供唯一正确标签。

---

## 2. 定义

**强化学习是让策略与环境交互产生行为，并通过最大化期望累计奖励来学习策略的方法。**

---

## 3. 核心机制：LLM 中的强化学习元素

### 3.1 状态

状态可以表示为 Prompt 和已经生成的 Token 前缀：

$$
s_t=(x,y_{<t})
$$

### 3.2 动作

动作是选择下一个 Token：

$$
a_t=y_t
$$

### 3.3 策略

语言模型本身就是随机策略：

$$
\pi_\theta(a_t\mid s_t)
=
p_\theta(y_t\mid x,y_{<t})
$$

### 3.4 轨迹

完整回答是一条动作轨迹：

$$
\tau=(y_1,y_2,\ldots,y_T)
$$

轨迹概率为：

$$
\pi_\theta(\tau\mid x)
=
\prod_t
\pi_\theta(y_t\mid x,y_{<t})
$$

### 3.5 奖励

回答完成后得到标量奖励：

$$
r(x,y)
$$

奖励可能来自奖励模型、规则、测试结果或其他可验证器。

---

## 4. 优化目标

目标是最大化期望奖励：

$$
J(\theta)
=
\mathbb E_{x,y\sim\pi_\theta}
[r(x,y)]
$$

因为生成 Token 是离散采样，不能直接对采样结果求普通路径导数。

---

## 5. Policy Gradient

策略梯度的基本形式为：

$$
\nabla_\theta J
=
\mathbb E
\left[
r(x,y)
\nabla_\theta
\log\pi_\theta(y\mid x)
\right]
$$

其中：

$$
\log\pi_\theta(y\mid x)
=
\sum_t
\log\pi_\theta(y_t\mid x,y_{<t})
$$

直觉是：

- 高奖励回答：提高其 Token 轨迹的概率。
- 低奖励回答：降低其概率。

---

## 6. Baseline 与 Advantage

直接使用奖励会有很大方差。

可以减去基线：

$$
A=r-b
$$

$A$ 称为 Advantage，表示当前回答比基准预期好多少。

策略梯度变为：

$$
\nabla_\theta J
\approx
\mathbb E
\left[
A
\nabla_\theta
\log\pi_\theta(y\mid x)
\right]
$$

减去与当前动作无关的基线不会改变期望梯度方向，但可降低方差。

---

## 7. 探索与采样

强化学习需要从当前策略采样多个可能回答，才能发现不同质量的行为。

如果策略输出过于确定，探索不足；如果过度随机，采样质量和训练信号会下降。

---

## 8. KL 约束

如果只追求奖励，策略可能偏离原模型过远。

常用目标加入参考策略约束：

$$
J
=
\mathbb E[r]
-
\beta
D_{\mathrm{KL}}
(\pi_\theta\|\pi_{\text{ref}})
$$

它在提高奖励和保持原有语言能力之间建立平衡。

---

## 9. On-policy 与 Off-policy

- On-policy：使用当前策略新生成的数据更新当前策略。
- Off-policy：使用其他策略或历史策略产生的数据训练。

PPO 式 RLHF 主要依赖当前或接近当前策略的 Rollout。

DPO 则直接使用预先收集的偏好数据，不执行在线策略 Rollout。

---

## 10. 核心本质

**LLM 强化学习把语言模型视为逐 Token 策略，通过提高高奖励回答的生成概率来改变模型行为。**
