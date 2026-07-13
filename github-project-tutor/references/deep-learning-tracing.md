# 深度学习端到端追踪规范

## 目录

1. 先确定执行模式
2. 数据输入与样本语义
3. Batch 构造
4. 模型构造
5. Forward 与张量形状账本
6. Loss 与参数更新
7. 评估与推理
8. 动态验证
9. 常见陷阱
10. 小白解释粒度
11. 设计因果与面试追问

## 1. 先确定执行模式

为训练、验证、测试、单样本推理、批量推理和服务接口分别找入口。它们可能共享模型但使用不同 transform、batch、forward 参数和后处理。先选用户最关心的一条作为主链，再列差异。

从实际命令反推有效配置：配置文件默认值 < 继承/组合配置 < CLI 覆盖 < 代码运行时修改。记录随机种子、精度、设备、分布式 world size 和 per-device/global batch size。

## 2. 数据输入与样本语义

回答并引用证据：

- 原始数据来自哪里，单个文件或记录包含什么？
- 标注如何对应样本？训练/验证如何划分？
- `__getitem__(i)` 返回 tuple、dict、dataclass 还是嵌套结构？
- 每个字段的现实含义、shape、dtype、值域和单位是什么？
- 随机增强在哪发生？同一 index 是否每次相同？
- resize/crop/normalize/tokenize 的顺序是什么？均值方差、词表、特殊 token 从哪里来？
- 无效样本、变长序列、缺失模态如何处理？

为一个样本建立表：

| 字段 | 现实含义 | 进入 Dataset 前 | `__getitem__` 输出 | dtype/值域 | 证据 |
|---|---|---|---|---|---|

如果 transform 由第三方库实现，结合项目参数和官方算子语义推导，但标明哪些维度由运行时输入决定。

## 3. Batch 构造

追踪 sampler → worker → `__getitem__` → collate → device transfer。重点确认：

- 默认 collate 是增加 batch 维，还是项目自定义拼接？
- 变长数据 pad 到何处，mask 中 0/1 各表示什么？
- 图数据是否合并节点/边并维护 batch index？
- 多视角/多 crop 是否形成 `[B,V,...]`，之后在哪合并为 `[B*V,...]`？
- distributed sampler 是否改变每个进程看到的数据量？
- `drop_last` 是否影响 batch 数与 BatchNorm？

明确区分：dataset length、steps per epoch、per-device batch、global batch、gradient accumulation 后的 effective batch。

## 4. 模型构造

从配置追到真正的类构造函数，不只读配置名。列出：

- backbone/encoder、neck、decoder/head、loss、postprocessor；
- 各模块注册位置、构造位置和 forward 调用位置；
- checkpoint 加载到哪些 key，strict、冻结层和参数组；
- 影响 shape 的配置：channels、hidden size、patch size、stride、heads、classes、vocab、max length；
- train/eval 模式对 dropout、BatchNorm、随机深度等的影响。

给参数量时注明来源：项目日志、工具统计或静态估计。不要凭架构名称猜数字。

## 5. Forward 与张量形状账本

### 维度符号

优先使用：

- `B` batch，`C` channel，`H/W/D` 空间尺寸；
- `T/L` 时间或序列长度，`N` token/patch/node 数；
- `E` embedding/hidden size，`A` attention heads，`Dh=E/A`；
- `V` view 数，`K` 类别/候选数，`Q` query 数。

先定义项目中的含义，再使用符号；存在具体配置时同时给符号和示例数值。

### 账本格式

| # | 位置/变量 | 数据含义 | 输入 shape | 操作/参数 | 输出 shape | dtype/device | 下游消费者 | 设计目的 | 证据等级 |
|---|---|---|---|---|---|---|---|---|---|

先建立 forward 覆盖表，列出实际执行路径上的全部自定义模块，并标记“已逐步解释 / 与第 n 个重复块同构 / 未执行分支 / 尚未确认”。只有完全同构且 shape 规律已写清的重复 block 才能合并讲解；首个 block、最后一个 block，以及任何改变分辨率、通道、token 数、路由或返回结构的 block 必须单独展开。

对每个模块同时回答四件事：接收什么、内部做什么、输出给谁、为什么需要它。涉及 attention、卷积、归一化、位置编码、门控、匹配或 loss 时，给出简化公式并把公式符号对应到代码变量；不要只翻译类名或复制 `print(model)`。

每遇到以下操作必须新增一行：

- `unsqueeze/squeeze`；
- `view/reshape/flatten/unflatten`；
- `permute/transpose/movedim`；
- `cat/stack/split/chunk`；
- conv/pool/interpolate/pad/crop；
- embedding、patchify、token 添加/删除；
- attention 的 Q/K/V 拆头与合头；
- RNN/Transformer 的 batch-first 切换；
- 检测/分割 head 的多尺度输出与 decode；
- 跨模态对齐、broadcast 和 einsum。

解释维度变化原因。例如：

```text
x: [B, 3, 224, 224]
patch_embed(stride=16): [B, 768, 14, 14]
flatten(2): [B, 768, 196]       # 合并 H、W，196=14×14
transpose(1,2): [B, 196, 768]   # 改为 Transformer 的 token-first feature 布局
prepend cls: [B, 197, 768]      # 加一个全局分类 token
```

对于每次 shape 变化，再增加一张轴变化表：

| 轴 | 操作前含义/大小 | 操作后含义/大小 | 是否变化 | 原因 |
|---|---|---|---|---|

不能用“维度变了”笼统描述。严格区分：

- 张量有几个轴（rank）；
- 某个轴的长度；
- 每个元素/Token 的特征宽度；
- 轴的顺序；
- 元素总数是否变化。

不要把“代码没改变 shape”和“尚未查到 shape”写成同一件事。残差相加前验证形状可兼容；concat 要说明沿哪个轴及新尺寸；broadcast 要说明隐式扩展哪些轴。

### 分支与循环

对 U-Net skip、FPN、多模态、MoE、多尺度和 recurrent 结构，分别追踪每条支路，再在汇合处核对 shape。重复 block 可完整解释第一层，并表格列出后续层的配置和尺寸变化，但不可跳过发生 downsample、通道变化或路由变化的层。

## 6. Loss 与参数更新

追踪 prediction、target、mask、sample weight 进入 loss 前的 shape 和 dtype。解释 reduction、各 loss 权重以及总 loss 的公式。检查 label reshape、one-hot、ignore index、正负样本匹配和跨设备 gather。

给出精确训练顺序，包括：

```text
取 batch → 搬到 device → autocast → forward → loss → 缩放/除以累计步数
→ backward → unscale/clip → optimizer.step → scaler.update → scheduler.step → zero_grad
```

按实际代码修正顺序。指出哪些参数被冻结、哪些模块收到梯度、是否有 detach/no_grad/EMA、多优化器或交替训练。

## 7. 评估与推理

追踪 logits/feature 到最终用户可理解结果的过程：softmax/sigmoid、argmax、beam search、NMS、坐标缩放、mask resize、token decode、指标聚合和文件写出。

解释 train 与 eval 的 transform、batch、model mode、gradient、TTA 和后处理差异。指标要说明输入、聚合范围和越大/越小是否更好。

## 8. 动态验证

静态信息不足且安全可运行时，按低成本顺序验证：

1. 运行已有 shape/test 用例；
2. 使用项目自带示例的一条样本；
3. 构造最小合成输入；
4. 注册 forward hooks，打印模块名、输入/输出嵌套 shape；
5. 使用框架 summary/trace 工具，但检查动态控制流是否被省略。

先检查代码、依赖和命令，不运行下载脚本或任意安装钩子。hook 输出需处理 tuple/dict/list，且不要把 hook 本身造成的行为变化误判为项目行为。保存实际命令、配置和输出摘要，使“运行验证”可复核。

## 9. 常见陷阱

- README 对应旧版本，入口或参数已变化。
- config 中的模型名经 registry/factory 动态解析。
- 张量变量名沿用旧布局，名字与实际 shape 不一致。
- DataLoader 前是 HWC，框架前变成 CHW。
- `.view()` 依赖 contiguous；此前 permute 可能要求 `.contiguous()`。
- attention mask 的布尔语义在不同 API 相反。
- 分类任务 sigmoid 与 softmax 代表不同标签假设。
- batch 被多视角、beam、query 或 distributed gather 暂时展开。
- loss 仅在训练返回，推理返回不同结构。
- 预训练 checkpoint 的类别数或位置编码被重映射。
- gradient accumulation 使 optimizer step 少于 forward 次数。
- 验证指标在进程内与跨进程聚合不同。

## 10. 小白解释粒度

完整遵循 [beginner-explanation-standard.md](beginner-explanation-standard.md)。尤其检查：

- 子词拆分只增加序列长度，不会自动扩大 embedding width；
- 多个编码器沿 feature 轴拼接与沿 token 轴拼接是两类不同操作；
- padding 只改变容器形状，不凭空产生语义；
- `reshape` 不等于 `transpose`，`stack` 不等于 `cat`；
- attention 中 head 数、每头宽度和总 hidden size 的关系已解释；
- 公式中的每个符号都在首次使用处定义，并给出项目内的实际或示意数值。

## 11. 设计因果与面试追问

完整遵循 [design-rationale-interview.md](design-rationale-interview.md)。对 PatchEmbed、downsample、upsample、token 合并、cross/joint attention、QKV、归一化、残差、门控、采样更新和 loss 等关键机制，除 shape 外继续追踪：

```text
上游约束 → 当前设计选择 → 数学或实现机制 → 下游收益
                              └→ 代价/风险 → 替代实现 → 等价条件
```

复杂度必须绑定变量。不要只写“减少计算”，而要写例如 $N=HW/P^2$，全注意力关系矩阵规模从 $N^2$ 推出对 $P$ 的四次方反比。若代码没有全注意力、使用稀疏/窗口/线性 attention，则按真实实现修正，不能套用通用结论。
