# Read Research Paper

一个面向科研新手的 Codex skill：读取学术论文 PDF，核验论文年份、正式发表信息和代码仓库，再用“问题 → 洞见 → 方法 → 证据 → 局限”的结构解释论文。

它不会只生成一段摘要，而会把论文原文证据、作者主张、外部核验结果和分析判断分开，并为关键结论保留 PDF 页码、章节、图表或公式位置。

OpenAI 将这类可重复工作流称为 skills，可参考 [Codex 官方用例](https://developers.openai.com/codex/use-cases)。

## 主要能力

- 核验标题、作者、机构、预印本年份、正式发表年份、Venue 和论文版本。
- 区分 arXiv 预印本、已投稿、在审、已录用、正式发表和 workshop 等状态。
- 查找 GitHub 或其他代码仓库，并区分官方实现、很可能官方、匿名未核验、第三方实现和归属不明。
- 用零基础读者能理解的方式解释术语、核心想法、Pipeline、公式和实验。
- 将主要 claim 绑定到具体实验数字、Figure、Table、Equation 和 PDF 页码。
- 区分作者明确承认的局限与阅读者根据证据推断的局限。
- 分开整理历史技术脉络与最近 12–24 个月的相关工作。
- 支持方法、理论、系统、数据集、Benchmark、Survey 等不同类型论文。
- 输出完整新手导读，或压缩为组内 600–1000 字 Reading Note。

## 项目结构

```text
read-research-paper/
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── examples/
│   └── prompts.md
└── skills/
    └── read-research-paper/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   ├── beginner-explanation-framework.md
        │   └── verification-protocol.md
        └── assets/
            ├── beginner-paper-guide-template.md
            └── reading-note-template.md
```

仓库根目录是给 GitHub 用户阅读的项目文档；只有 `skills/read-research-paper/` 是需要安装到 Codex 的 skill 文件夹。

## 安装

### 方式一：下载 ZIP

1. 在 GitHub 页面点击 **Code → Download ZIP**。
2. 解压仓库。
3. 将 `skills/read-research-paper` 整个文件夹复制到个人 Codex skills 目录。

默认目录：

- Windows：`%USERPROFILE%\.codex\skills\read-research-paper`
- macOS / Linux：`~/.codex/skills/read-research-paper`
- 如果设置了 `CODEX_HOME`：使用 `$CODEX_HOME/skills/read-research-paper`

### 方式二：克隆后复制

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/read-research-paper.git
cd read-research-paper
```

Windows PowerShell：

```powershell
$skillsDir = if ($env:CODEX_HOME) {
    Join-Path $env:CODEX_HOME "skills"
} else {
    Join-Path $HOME ".codex\skills"
}

New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
Copy-Item ".\skills\read-research-paper" -Destination $skillsDir -Recurse -Force
```

macOS / Linux：

```bash
SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$SKILLS_DIR"
cp -R skills/read-research-paper "$SKILLS_DIR/"
```

安装后新建一个 Codex 任务。如果 skill 没有立即出现，请重新打开 Codex 后再试。

## 快速使用

向 Codex 附加论文 PDF，然后显式调用 skill：

```text
使用 $read-research-paper 阅读这篇论文 PDF，核验它的发表年份、会议和官方代码仓库，并给我一份零基础也能读懂的中文导读。
```

也可以提供本地 PDF 路径、arXiv 链接、DOI 页面或正式论文页面：

```text
使用 $read-research-paper 阅读 C:\papers\example.pdf。
先告诉我这份 PDF 是哪个版本，再核验正式 Venue 和代码仓库，最后解释论文的方法与实验。
```

建议第一次使用时显式写出 `$read-research-paper`，便于确认 Codex 已加载正确的 skill。

## 常用输出模式

### 1. 完整新手导读

```text
使用 $read-research-paper 深入阅读这篇 PDF。
假设我完全不了解这个领域，用中文解释必要术语、问题、Key Idea、方法流程、核心公式、实验、创新点、局限和最新相关工作。所有关键结论请标出 PDF 页码或外部来源。
```

### 2. 只核验论文身份与代码

```text
使用 $read-research-paper 只做元信息核验：
区分首次预印本、当前 PDF 版本和正式发表年份，确认 Venue 状态，并查找 GitHub 仓库及其官方性。暂时不要展开方法细节。
```

### 3. 生成组内 Reading Note

```text
使用 $read-research-paper 阅读这篇论文，然后按照组内 Reading Note 模板压缩成 600–1000 字。
保留 Problem、Motivation、Key Idea、Pipeline、核心公式或机制、Main Results、Novelty、Limitation、Possible Extension 和 One Question for Authors。
```

### 4. 专门解释公式

```text
使用 $read-research-paper 解释论文第 4 页的 Eq. (7)。
请依次说明公式目的、所有符号、每一项的作用、优化时发生什么、依赖的假设，以及它位于整个 Pipeline 的哪一步。
```

更多可复制提示词见 [examples/prompts.md](examples/prompts.md)。

## 默认报告结构

完整报告通常包含：

1. 一分钟看懂
2. 论文身份卡
3. 阅读前置知识
4. 问题与动机
5. 一句话 Key Idea
6. 方法拆解与核心公式
7. 实验到底证明了什么
8. 真正的创新与前人差异
9. 局限与可信边界
10. 历史脉络、最近前沿与趋势
11. 可行的后续方向
12. 一个想问作者的问题
13. 新手阅读路线
14. 证据索引与待确认事项

不适用于当前论文类型的栏目会说明原因，而不是虚构内容。例如，系统论文不会被强行填写“训练损失”。

## 代码仓库如何判定

skill 不会因为仓库名称相同或 Star 数量较高，就直接把它写成官方代码。它会使用以下分类：

- **确认官方**：论文、作者项目页或正式页面直接链接该仓库。
- **很可能官方**：仓库与作者身份能交叉对应，但缺少直接来源链接。
- **匿名作者提供、身份未核验**：盲审论文提供了仓库，但无法核验作者身份。
- **社区实现**：第三方复现或重新实现。
- **归属不明**：信息不足或证据冲突。
- **截至核验日期未找到**：表示没有找到可核验仓库，不等于断言代码不存在。

## 使用边界

- 这份报告适合作为阅读前导读或阅读后核对，不能替代亲自阅读原文。
- Venue、GitHub 状态和“最新论文”会随时间变化，需要允许 Codex 访问网页才能完整核验。
- 扫描件、复杂双栏、公式和表格可能需要 OCR 或页面渲染；无法可靠读取时，skill 会明确报告缺失范围。
- “作者声称达到 SOTA”不等于该结论已经被独立证明；skill 会检查比较条件和证据边界。
- 提交组内 Reading Note 前，请自行对照 PDF 检查页码、公式、图表和分析判断。

## 首次上传到 GitHub

在本项目根目录执行：

```bash
git init
git add .
git commit -m "Initial commit: add read-research-paper skill"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/read-research-paper.git
git push -u origin main
```

执行前，请先在 GitHub 创建同名空仓库，并把 `YOUR_GITHUB_USERNAME` 换成自己的用户名。

## 参与贡献

欢迎通过 Issue 或 Pull Request 改进证据规范、论文类型适配、提示词和输出模板。修改前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

本项目目前没有附加开源许可证。在维护者选择并添加许可证之前，默认不授予复制、修改或再分发权利。公开发布前建议根据团队需求选择合适的许可证。
