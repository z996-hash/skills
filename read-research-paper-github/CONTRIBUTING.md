# Contributing

感谢你帮助改进 `read-research-paper`。

## 可以贡献什么

- 修正论文元信息、Venue 或代码仓库核验规则。
- 改进对方法、理论、系统、数据集、Benchmark 和 Survey 论文的适配。
- 增加更清晰的新手解释方法，但不要牺牲技术准确性。
- 改进完整导读或 Reading Note 模板。
- 增加真实、可复现的使用示例和失败案例。

## 修改原则

1. 以论文原文和一手来源为准，不使用博客或搜索摘要替代证据。
2. 保持 `SKILL.md` 精炼，把详细规则放在 `references/`。
3. 不要在 `skills/read-research-paper/` 内添加 README、安装指南或 Changelog；用户文档放在仓库根目录。
4. 不要把缺失搜索结果写成“代码不存在”或“没有正式发表”。
5. 不要把第三方实现标记为官方仓库。
6. 新增术语时，确保零基础读者能理解其作用。
7. 修改输出结构时，兼顾不同论文类型，允许不适用栏目明确说明原因。

## 提交前检查

- `skills/read-research-paper/SKILL.md` 的 frontmatter 只包含 `name` 和 `description`。
- skill 文件夹名称与 frontmatter 中的 `name` 一致。
- `agents/openai.yaml` 与当前 skill 的名称和用途一致。
- 所有 Markdown 相对链接都能找到对应文件。
- 所有文本文件使用 UTF-8 编码。
- 没有遗留未完成占位符、损坏字符或本地绝对路径。
- 至少用一篇真实 PDF 检查修改后的行为。
- 涉及元信息或代码仓库规则时，至少测试一个“有官方代码”和一个“未找到官方代码”的案例。
- 涉及论文类型路由时，不要只测试机器学习论文。

如果本地环境包含 `skill-creator`，请在提交前运行其 `quick_validate.py` 验证 `skills/read-research-paper/`。

## Pull Request 建议格式

请在 PR 中说明：

- 改了什么；
- 为什么需要修改；
- 使用了哪些论文或原始资料进行验证；
- 修改前后的关键输出差异；
- 仍然存在的限制或未确认事项。
