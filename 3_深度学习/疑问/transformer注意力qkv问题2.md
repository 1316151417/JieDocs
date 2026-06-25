是的，在你这份代码里，**Q/K/V 的向量维度都是 32**。

也就是最后这一维：

```
Q: B × ? × 32
K: B × ? × 32
V: B × ? × 32
```

这个 `32` 来自：

```
num_hiddens = 32
```

然后你构造 encoder / decoder 时传的是：

```
key_size=num_hiddens
query_size=num_hiddens
value_size=num_hiddens
num_hiddens=num_hiddens
```

所以：

```
query_size = 32
key_size   = 32
value_size = 32
输出维度    = 32
```

但中间那个 `?`，也就是长度，不一定一样。

比如：

```
encoder self-attention:
Q: B × S × 32
K: B × S × 32
V: B × S × 32

decoder self-attention 训练时:
Q: B × T × 32
K: B × T × 32
V: B × T × 32

decoder self-attention 预测第 3 步:
Q: B × 1 × 32
K: B × 3 × 32
V: B × 3 × 32

decoder cross-attention 预测时:
Q: B × 1 × 32
K: B × S × 32
V: B × S × 32
```

所以你可以记成一句：

```
在你的代码里，Q/K/V 的“宽度”都是 32；
但 Q/K/V 的“长度”会根据 encoder、decoder、训练、预测场景变化。
```

另外还有多头注意力这一步：

```
num_heads = 4
```

所以内部会把 32 拆成 4 个头：

```
每个 head 的维度 = 32 / 4 = 8
```

内部临时变成：

```
(B × 4) × length × 8
```

最后再拼回：

```
B × length × 32
```