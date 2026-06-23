不是完全一样。你的 **encoder** 和 **decoder** 里有三种 attention，要分开看。

**1. Encoder self-attention**

在 encoder 里：

```
self.attention(X, X, X, valid_lens)
```

所以：

```
Q = X
K = X
V = X
```

如果源句长度是 `S`：

```
Q: B × S × H
K: B × S × H
V: B × S × H
```

这里 `q_len = k_len = v_len = S`。

**2. Decoder masked self-attention**

在 decoder 第一段 attention 里：

```
X2 = self.attention1(X, key_values, key_values, dec_valid_lens)
```

训练时，decoder 一次拿到整条目标输入：

```
X = <bos> + Y[:-1]
```

如果目标长度是 `T`：

```
Q: B × T × H
K: B × T × H
V: B × T × H
```

也就是：

```
q_len = k_len = v_len = T
```

但它会用 `dec_valid_lens` 做 causal mask，所以第 1 个位置只能看第 1 个，第 2 个位置只能看前 2 个，依此类推。

预测时就不一样了。你的代码是一个 token 一个 token 预测：

```
dec_X = torch.tensor([[tgt_vocab["<bos>"]]])
Y, state = net.decoder(dec_X, state)
dec_X = Y[:, -1:].argmax(dim=2)
```

每一步送进 decoder 的 `dec_X` 只有当前这一个 token，所以：

```
Q: B × 1 × H
```

但是 `DecoderBlock` 里有 cache：

```
key_values = X if cache[self.i] is None else torch.cat((cache[self.i], X), dim=1)
cache[self.i] = key_values
```

所以 K/V 会越来越长：

```
第 1 步:
Q: B × 1 × H
K/V: B × 1 × H

第 2 步:
Q: B × 1 × H
K/V: B × 2 × H

第 3 步:
Q: B × 1 × H
K/V: B × 3 × H
```

所以回答你这个问题：

```
随着解码 token 一个一个预测出来，Q 的长度不会变，始终是 1；
K/V 的长度会变，因为 cache 会累积历史 token。
```

**3. Decoder cross-attention**

decoder 第二段 attention 是：

```
Y2 = self.attention2(Y, enc_outputs, enc_outputs, enc_valid_lens)
```

这里：

```
Q 来自 decoder 当前状态
K/V 来自 encoder outputs
```

训练时：

```
Q: B × T × H
K/V: B × S × H
```

预测时：

```
Q: B × 1 × H
K/V: B × S × H
```

所以 decoder 不是“Q/K/V 都和 encoder 一样”。更准确是：

```
encoder self-attention:
Q/K/V 都来自源句

decoder self-attention:
Q 来自当前目标输入，K/V 来自当前目标输入 + 历史 cache

decoder cross-attention:
Q 来自 decoder，K/V 来自 encoder memory
```

你这段代码里 `query_size/key_size/value_size` 都传了 `num_hiddens=32`，这只是说它们的**向量维度都是 32**，不是说它们的**长度**一样。