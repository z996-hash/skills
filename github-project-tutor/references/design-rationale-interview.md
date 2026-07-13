# 设计原因与模拟面试追问规范

## 目录

1. 目标
2. 七步设计解释闭环
3. 五层递进追问
4. 问题重要性与数量
5. 关键操作问题库
6. PatchEmbed 标准示范
7. 答案质量与证据边界

## 1. 目标

把源码中的每个关键操作从“代码翻译”提升为“工程决策解释”。读者不仅要能复述 shape，还应能回答：

- 上游出现了什么问题或约束？
- 当前实现怎样解决？
- 数学上为何有效？
- 为什么不用另一种常见写法？
- 得到了什么，牺牲了什么？
- 参数改变后会怎样？
- 什么输入会暴露错误，怎样验证？

问题必须服务于当前数据流。不要在 PatchEmbed 后突然询问与项目无关的优化器题目，也不要用通用面试题替代源码分析。

## 2. 七步设计解释闭环

对 `P0` 关键模块依次回答：

1. **约束**：上游张量是什么，下游接口需要什么？
2. **选择**：代码实际选择了哪个算子、布局或参数？
3. **机制**：用公式或最小例子说明它怎样工作。
4. **收益**：信息表达、计算、显存、并行、优化或工程实现上的好处。
5. **代价**：信息压缩、归纳偏置、精度、灵活性、数值稳定性或维护成本。
6. **替代**：至少一种合理替代方案，并写明何时等价、何时不等价。
7. **验证**：一个能发现 shape/语义错误的最小测试、断言、hook 或反例。

写成因果链，而不是形容词堆积：

```text
图像网格 token 太多
→ 用 P×P、stride=P 的卷积按非重叠 patch 聚合
→ token 数 N=HW/P²
→ 全注意力关系数量约 N²，随 P 增大快速下降
→ 代价是更粗的空间粒度和更强的信息压缩
```

## 3. 五层递进追问

每条追问后立即给参考答案。优先使用以下顺序：

### L1 基础事实

- 输入/输出 shape 是什么？
- 哪个轴改变？元素总数是否变化？
- 参数来自配置、checkpoint 还是运行时输入？
- 可学习参数量怎样由这些尺寸决定？

### L2 数学机制

- 为什么这个操作在 shape 上合法？
- 对一个输出位置，究竟读取哪些输入值？
- `reshape`、索引、卷积或 attention 的公式是什么？

### L3 设计动机

- 下游为什么需要这种布局或宽度？
- 删除该操作后，最先在哪个模块失败或退化？
- 这一步加入了新的可学习参数、位置信息，还是仅改变视图？

### L4 权衡与替代

- 为什么不用 `unfold + Linear`、pooling、projection、stack 或另一种 attention？
- 两种写法等价需要哪些 kernel、stride、padding、轴顺序和权重对应条件？
- 参数扩大一倍时，token 数、计算量、显存和信息粒度如何变化？

### L5 边界与调试

- 输入尺寸不能整除 stride 时会 padding、floor、报错还是丢边界？
- 非 contiguous 张量上使用 `view` 会怎样？
- 怎样用递增数字张量验证 transpose/reshape 没有串轴？
- 哪个 `assert`、单元测试或 hook 最容易捕捉错误？
- 构造函数声明的 flag 是否真的在 `forward` 中被读取？

## 4. 问题重要性与数量

先标级别，再生成问题，避免报告膨胀：

| 级别 | 判断标准 | 问题数量 | 至少覆盖 |
|---|---|---:|---|
| `P0` | 改变 token、空间、通道、语义、复杂度；跨模态/跨模块接口 | 4–8 | L1、L2、L3、L4、L5 |
| `P1` | 主干上的归一化、残差、激活、门控，shape 常不变 | 2–4 | L1、L3，以及 L4/L5 之一 |
| `P2` | 明显样板代码、getter、薄包装 | 0–1 | 作用与证据 |

同构重复 block 不重复相同题目；首次完整回答，后续只问参数或分支差异。

## 5. 关键操作问题库

这些是选题方向，不是必须逐字照抄的题库。只选择源码能够支持的问题。

### Tokenizer / Embedding

- 为什么 token 数 $L$ 可变而 hidden width $D$ 固定？
- tokenizer 与 embedding 各自做什么，谁有可训练参数？
- 为什么 padding token 仍会得到向量，mask 怎样阻止它污染结果？
- 子词更多会怎样影响 attention 计算量和截断风险？

### Patchify / Downsample / Convolution

- 为什么 kernel 与 stride 取相同的 $P$？patch 是否重叠？
- Conv2d 与 `unfold + Linear` 在什么条件下等价？
- $P$ 改变后 $N$ 和 $N^2$ 怎样变化？
- 参数量是否为 $DCP^2+D$，bias 关闭后怎样变化？
- 压缩 token 的代价是什么？边界不能整除时发生什么？
- `flatten/strict_img_size/dynamic_img_pad` 等开关是否在真实调用链生效？

### Flatten / Reshape / Transpose

- 此操作改变数值、元素总数、轴长度还是轴顺序？
- 为什么不能用一次裸 `reshape` 代替 transpose？
- 下游哪个算子要求 feature 在最后一轴？
- 怎样用小张量验证没有把 channel 与 token 串错？

### Cat / Pad / Projection

- 为什么沿 feature 轴而不是 token 轴？
- 除拼接轴外哪些轴必须相同？
- 补零、线性投影和独立 adapter 的语义与参数代价有何区别？
- concat 后宽度增大怎样影响后续线性层参数量？

### QKV / Attention

- `3D` 是三个向量组还是三倍 token？
- 为什么除以 $\sqrt{D_h}$？softmax 沿哪一轴？
- head 数改变且 $D$ 固定时，每头宽度、参数量和 attention map 显存怎样变化？
- joint/cross/self-attention 的 Q、K、V 来自哪里？注意力矩阵各区域代表什么？

### Normalization / Residual / Gating

- LayerNorm 归一化哪个轴？为什么不是 batch 轴？
- 残差为何要求 shape 一致？它对梯度传播有什么帮助？
- 门控为 0 时模块退化成什么？初始化策略怎样影响稳定性？
- Pre-Norm 与 Post-Norm 的数据流差异是什么？

### Sampler / Decoder / Upsample

- 为什么循环中 shape 不变但样本持续改变？
- step size、sigma/timestep 如何 broadcast 到 `[B,C,H,W]`？
- 最近邻上采样加卷积与转置卷积的伪影、参数和 shape 有何差异？
- 解码器恢复空间尺寸是否等于恢复原始信息？

### Loss / Optimizer

- prediction、target、mask 进入 loss 前怎样对齐？
- reduction 改变的是 shape 还是梯度尺度？
- 为什么在某处 detach/no_grad，哪些参数因此收不到梯度？
- 梯度累积怎样改变 effective batch，而不改变单次 forward shape？

## 6. PatchEmbed 标准示范

以下结构是写法示范，数值必须替换成目标仓库事实或标注“示意”。

### 数据轨

```text
[B,C,H,W]
--Conv2d(kernel=P,stride=P,out=D)--> [B,D,H/P,W/P]
--flatten(2)----------------------> [B,D,N]
--transpose(1,2)------------------> [B,N,D]
其中 N=(H/P)(W/P)
```

逐轴解释：卷积同时把每个 $P\times P$ 局部块聚合成一个 $D$ 维描述；`flatten(2)` 合并两个空间轴；`transpose(1,2)` 把布局改成下游 Transformer 常用的 `[batch, token, feature]`。

### 设计轨

```text
约束：逐像素 token 导致 N 太大，下游 attention 代价高
选择：非重叠 patch 卷积 + 序列化
收益：局部聚合、通道投影、降 token 数一次完成
代价：空间粒度变粗，投影通常有损，边界处理受 stride/padding 约束
替代：unfold + Linear；在相同 patch/stride/padding 和权重重排条件下等价
验证：用递增数字输入检查每个 token 对应哪个 patch，并断言输出 N
```

### 递进追问示范

1. **`flatten` 是否丢值？** 不丢元素；它把 `(h,w)` 用固定索引映射到 $n$。但仅有内容 token 不足以让 permutation-equivariant attention 理解二维坐标，所以通常还需要位置编码。
2. **为什么不能直接 `reshape(B,N,D)`？** 原布局 `[B,D,H_p,W_p]` 的连续内存顺序以 channel 为外层；裸 reshape 会把值按错误语义分组。等价写法应先 `permute(0,2,3,1)` 再 reshape。
3. **为何用 Conv2d？** 权重 `[D,C,P,P]` 可重排为 Linear 权重 `[D,CP^2]`，所以在非重叠、相同 padding 等条件下等价于每个 patch 展平后共享同一个 Linear；卷积实现更直接，也能使用优化内核。
4. **$P$ 增大有什么好处和代价？** $N=HW/P^2$；若使用全注意力，关系矩阵规模 $N^2=(HW)^2/P^4$。$P$ 翻倍时 $N$ 约变为四分之一、关系数量约变为十六分之一，但每个 token 覆盖更大区域，细粒度信息压缩更强。
5. **尺寸不能整除 $P$ 时怎么办？** 必须读真实 padding/check 代码；无 padding 的 Conv2d 使用 floor 规则，可能舍弃不足一个 kernel 的边缘，而有些实现会动态 pad 或直接报错。

## 7. 答案质量与证据边界

每个参考答案至少包含“直接结论 + 项目证据”。涉及公式、复杂度或等价性时再补成立条件。区分：

- `代码确认`：当前实现、参数、调用者和边界行为；
- `数学推导`：由已确认 shape/算子推出；
- `工程解释`：常见实现收益，但必须说明如何与当前项目对应；
- `合理推断`：论文或训练代码缺失时的解释；
- `暂未确认`：checkpoint、运行时分支或第三方实现无法静态确定。

不要为了“像面试”制造唯一正确答案。设计题通常有条件：写出目标约束后再评价方案。不要声称某实现“更好”，应说明它在何种输入规模、硬件、精度或任务目标下更合适。
