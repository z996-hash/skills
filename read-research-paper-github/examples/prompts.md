# Prompt Examples

以下示例假设 skill 已安装，并使用显式调用 `$read-research-paper`。

## 完整精读

```text
使用 $read-research-paper 阅读我附加的论文 PDF。
我是这个领域的新手，请先核验论文版本、首次公开年份、正式 Venue 和官方代码仓库，再解释 Problem、Motivation、Key Idea、Pipeline、核心公式、主要实验、Novelty、Limitation 和最新相关工作。
每个关键结论都要给出 PDF 页码、章节、Figure、Table 或 Equation 位置。
```

## 阅读前快速导读

```text
使用 $read-research-paper 给我一份 10 分钟阅读前导读。
只讲理解本文所需的最小背景、问题、核心想法、方法数据流和最值得检查的三项实验。不要假装我已经读过论文。
```

## 阅读后核对

```text
使用 $read-research-paper 检查我的理解是否准确：
【粘贴自己的理解】

请逐条对照 PDF，区分“原文支持”“部分支持”“原文没有说”“我的推断”，并给出证据位置。
```

## 元信息与 GitHub 核验

```text
使用 $read-research-paper 核验这篇论文的身份。
请分别列出首次公开时间、当前 PDF 版本、正式发表年份、完整 Venue/Track、DOI/arXiv/OpenReview，以及所有候选代码仓库。
代码仓库必须说明 owner、官方性分类、归属证据和核验日期。
```

## 核心公式教学

```text
使用 $read-research-paper 解释本文最重要的两个公式。
对每个公式依次说明：它解决什么问题、所有符号、如何用人话读、训练或推导时每一项起什么作用、关键假设、与 Pipeline 的关系，以及一个最小例子。
```

## 实验审计

```text
使用 $read-research-paper 审计这篇论文的实验。
把每个核心 claim 绑定到数据集、指标方向、最公平 baseline、论文结果、差值和证据位置，并检查消融、误差条、统计显著性、模型规模、数据和计算预算是否可比。
```

## 理论论文

```text
使用 $read-research-paper 阅读这篇理论论文。
不要强行套用机器学习训练模板；重点解释定义、假设、主要定理、证明思路、结论边界，以及哪些假设可能过强。
```

## 系统论文

```text
使用 $read-research-paper 阅读这篇系统论文。
重点重画架构和请求/数据路径，说明瓶颈、容错、吞吐、延迟、资源成本和 workload 是否真实；不适用的 loss 或训练栏目请明确写不适用。
```

## 数据集或 Benchmark 论文

```text
使用 $read-research-paper 阅读这篇数据集论文。
重点检查数据来源、采集和标注流程、质量控制、任务与指标、覆盖范围、数据泄漏、偏差、许可证和伦理风险。
```

## 生成组内 Reading Note

```text
使用 $read-research-paper 按 reading-note 模板生成 600–1000 字的中文初稿。
保留核心原文定位，并在结尾列出我提交前必须亲自核对的内容。不要替我声称已经完成原文阅读。
```

## 对比两篇论文

```text
使用 $read-research-paper 分别阅读这两篇 PDF，再比较它们的问题设定、核心机制、训练或系统流程、数据集、指标、证据强度、计算成本和适用边界。
不要只按摘要中的营销表述比较。
```
