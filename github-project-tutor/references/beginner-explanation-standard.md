# 零基础技术解释标准

## 目录

1. 核心原则
2. 轴与形状的讲解顺序
3. 必须详细解释的操作
4. 疑问驱动模板
5. Tokenizer 与多编码器专项
6. Attention 专项
7. 数字与证据
8. 从“操作说明”升级为“设计解释”

## 1. 核心原则

不要假设读者看到 `[B,L,D]` 就已经理解它。每次出现新布局时，把张量想成“多层表格/容器”，逐轴说明：有多少份数据、每份有多少位置、每个位置用多少数字描述。

先用白话，再给符号和公式，最后绑定到代码。避免用“投影、对齐、融合、映射”替代真正的操作说明。

一个完整解释必须闭合三层：

1. **发生了什么**：代码、数据与 shape；
2. **为什么成立**：元素数量、轴兼容、数学公式或 API 语义；
3. **为什么这样设计**：目标、收益、代价、替代方案和边界条件。

## 2. 轴与形状的讲解顺序

对每个新张量按顺序回答：

1. 它在现实中表示什么？
2. rank 是多少，即有几个轴？
3. 每个轴从左到右分别表示什么？
4. 每个轴的长度由哪里决定？
5. 一个位置上的标量或向量表示什么？
6. dtype、值域、device 是什么？
7. 下一步哪个模块消费它？

先确认对象确实是张量。若 tokenizer、dataset 或 parser 返回的是 Python list、dict、tuple、字符串或 PIL Image，先写真实容器和元素类型；直到实际执行 `torch.tensor/as_tensor/from_numpy` 后才能赋予 tensor dtype、device 和严格 shape。

示例：

```text
[B,L,D] 不是“一个 D×L 的大特征”。
B：有多少条文本。
L：每条文本有多少个 token 位置。
D：每个 token 位置用多少个数字描述。
```

## 3. 必须详细解释的操作

### Embedding lookup

说明 token id 是整数索引，不是语义向量。Embedding 表的形状通常为 `[V,D]`；查询 $L$ 个 id 得到 `[L,D]`。子词变多只增加 $L$，不改变由模型结构固定的 $D$。

### Padding

说明补的是位置或特征维、补什么值、mask 是否忽略这些位置。补零只能统一 shape，不会自动创造语义。

### Concatenate

必须写 `dim`。先核对除拼接轴外所有轴相等，再对拼接轴做加法：

```text
沿 feature 轴： [B,L,D1] + [B,L,D2] → [B,L,D1+D2]
沿 token 轴：   [B,L1,D] + [B,L2,D] → [B,L1+L2,D]
```

解释这两种拼接在语义上的区别：前者丰富同一位置的描述，后者增加位置数量。

### Stack

说明 stack 会创建新轴，而 cat 延长已有轴：两个 `[L,D]` stack 后可以是 `[2,L,D]`；cat 后只能是 `[2L,D]` 或 `[L,2D]`。

### Reshape/View/Flatten

说明元素总数必须保持不变，数据通常不重新计算，只改变索引方式。写出乘积守恒。若涉及 contiguous，解释内存布局要求。

### Permute/Transpose

说明轴长度集合通常不变，只改变轴的顺序。给“旧轴编号 → 新轴编号”映射，不能只写结果 shape。

### Unsqueeze/Squeeze

说明新增/删除的是长度为 1 的轴，元素数量不变；解释为何需要 batch、head 或 broadcast 轴。

### Broadcast

指出哪个长度为 1 或缺失的轴被逻辑扩展；说明通常不是真的复制内存。相加/相乘前列出对齐后的两个 shape。

### Convolution/Pooling/Upsample

分别解释 channel 和空间轴的变化。卷积输出空间尺寸使用公式，并代入本项目参数计算一个例子。

### Residual add

证明两个分支 shape 相容，说明加法不会拼接通道或 token；解释残差保存了什么信息。

### QKV 与多头注意力

说明 `3D` 常代表把 Q/K/V 三组宽度为 $D$ 的向量暂时放在同一轴，不是 token 数变成三倍。解释：

```text
[B,L,D] → Linear → [B,L,3D]
→ split → Q,K,V 各 [B,L,D]
→ heads → 各 [B,A,L,Dh]，其中 D=A×Dh
```

说明拆头不会增加信息总宽度，只是把 $D$ 分组。

### Loss flatten

解释为何 `[B,L,K]` 常变为 `[B×L,K]`，target `[B,L]` 变为 `[B×L]`；batch 和位置被合并成样本轴，类别轴保持。

## 4. 疑问驱动模板

在高认知负担步骤后写：

```markdown
#### 你可能会问：为什么……？

先给一句直接答案。

再按“原 shape → 操作轴 → 新 shape”解释。

给 2–4 个元素的玩具例子。

最后写“容易误解为……，实际是……”。

继续追加：项目为什么需要这一步；若删除或换成另一写法会怎样；主要收益和代价是什么；怎样用一个最小实验验证。
```

优先回答真实疑问：

- 一个单词拆成多个 token，特征宽度会不会跟着翻倍？
- 两个编码器输出宽度不同，为什么能拼？
- 补零后是不是增加了新的语义？
- `dim=-1` 和 `dim=-2` 到底分别是哪一轴？
- batch 为什么突然翻倍？
- hidden size 拆成多个 head 后数字是否变多？
- patchify 后图像是不是丢失了？
- sampler 循环为什么 shape 一直不变，内容却持续变化？
- 为什么选这个算子而不是看似等价的另一个算子？
- 参数增大后，token 数、计算量、显存和细节保留会怎样变化？
- 这个实现在哪些输入尺寸或 dtype 下会失败？

## 5. Tokenizer 与多编码器专项

区分字符、单词、子词、token id、embedding 和 contextual hidden state。不要把 tokenizer 输出称为“4096 维 token”；tokenizer 只产生 id，4096 维来自 embedding 和 Transformer hidden size。

若一个词被拆成多个子词：

$$
[B,L]\xrightarrow{\text{Embedding}}[B,L,D]
$$

$L$ 由 token 数决定，$D$ 由模型配置决定。每个子词各有一个 $D$ 维向量，self-attention 使它们交换上下文，但不会自动合并成单个 token。

多个编码器合并前检查：

- 是否使用相同 tokenizer；
- token 序列长度是否相同；
- 相同位置是否真的语义对齐；
- 拼接沿 token 轴还是 feature 轴；
- 不同 feature width 如何投影或 padding；
- pooled 与 per-token 输出是否走不同下游。

不得用未经验证的具体分词结果作为事实。能运行实际 tokenizer 时记录版本和输出；不能运行时使用“示意”，并说明真实结果可能随 tokenizer 和版本不同。

## 6. Attention 专项

先解释目的，再解释公式。至少覆盖：

1. Q 表示当前 token 想找什么；
2. K 表示每个 token 可以被怎样匹配；
3. V 表示匹配后实际汇总的内容；
4. $QK^T$ 为什么得到位置对位置的分数；
5. softmax 沿哪个轴；
6. mask 屏蔽什么；
7. 输出为何仍是每个 query 位置一个向量。

给完整 shape 链：

$$
Q:[B,A,L_q,D_h],\quad K:[B,A,L_k,D_h]
$$

$$
QK^T:[B,A,L_q,L_k]
$$

$$
\operatorname{softmax}(QK^T)V:[B,A,L_q,D_h]
$$

如果是 cross/joint attention，明确 $L_q$、$L_k$ 分别包含哪些模态的 token，并解释 concat 后注意力矩阵的四个区域。

## 7. 数字与证据

所有数字标记来源：

- `运行验证`：实际 tokenizer、hook、测试或日志；
- `代码确认`：配置、权重 shape 或算子静态推出；
- `示意`：为了教学选取的小数字；
- `暂未确认`：缺失权重、数据或动态值。

具体例子优先选择项目默认配置。若默认值会被 checkpoint/CLI 覆盖，同时给“符号公式”和“当前已确认数值”，不要把类构造函数默认值当成实际模型配置。

不要仅凭推理公式给模型输出命名为 noise、velocity、score、flow 或 logits。只有训练 target、loss、论文与代码映射或官方说明能确认语义时才使用这些名称；否则沿用源码变量名，如 `model_output`。

复现章节必须交叉核对 README 下载文件名与代码硬编码路径，并说明首次运行时会发生的 tokenizer/config 网络访问、许可证门控、缓存、重命名和 device 要求。不能把只有主命令的一行称为“从零可运行”。

## 8. 从“操作说明”升级为“设计解释”

完整遵循 [design-rationale-interview.md](design-rationale-interview.md)。尤其避免以下低质量写法：

- “使用 Flatten 是为了展平”——只是重复算子名；
- “Transpose 是为了维度匹配”——没有说明匹配谁以及为何需要这种布局；
- “卷积可以提取特征”——没有解释 receptive field、stride、共享参数和压缩比例；
- “这样效率更高”——没有写复杂度关于哪个变量怎样缩放；
- “另一种写法也可以”——没有写等价成立的 kernel、stride、padding、权重排列等条件。

解释设计原因时，把结论绑定到当前项目的消费者。例如不要泛泛说 Transformer 需要序列，而要指出下游 `Linear/LayerNorm/Attention` 把最后一轴当 hidden size，并引用调用位置。
