---
title: "LLM Knowledge Bases"
source: "https://academy.dair.ai/blog/llm-knowledge-bases-karpathy"
author:
  - "[[Elvis Saravia]]"
published: 2026-04-03
created: 2026-06-25
description: "A visual breakdown of Andrej Karpathy's approach to building personal knowledge bases powered by LLMs. Learn the 4-phase pipeline: ingest, compile, query, and maintain - with an interactive architecture diagram."
tags:
  - "clippings"
---
Andrej Karpathy 最近分享了他构建由 LLM 驱动的个人知识库的方法。这是一个出乎意料地实用的系统——它不依赖复杂的 RAG 流水线或向量数据库，而是使用一个结构化的 Markdown 维基，由 LLM 增量地编译和维护。

我做了一张交互式图表，拆解了 Karpathy 方法的完整架构。将鼠标悬停在每个组件上即可查看详情。

<iframe src="https://academy.dair.ai/blog/llm-knowledge-bases/diagram.html" width="100%" frameborder="0"></iframe>

## 核心思想

Karpathy 的方法并非构建一个传统的 RAG 系统，而是把 LLM 当作一个**编译器**——它读取原始文档，并产出一个结构化、相互链接的维基。维基本身就是知识库——在个人知识库的规模下，无需嵌入（embeddings）或向量搜索。

该系统包含四个持续循环的阶段：

## 第一阶段：摄入（Ingest）

原始数据从多个来源流入：

- **Obsidian Web Clipper** 将网页文章转换为整洁的 `.md` 文件，并将图片下载到本地
- 来自 arXiv、GitHub 的**论文和代码库**，以及数据集，被收集到一个 `raw/` 暂存目录中
- 所有内容首先进入 `raw/`——LLM 从这里读取

## 第二阶段：编译（Compile）

LLM 增量地读取 `raw/` 并构建一个结构化维基：

- **索引文件**包含所有文档的简要摘要——它们作为查询的入口点
- **概念文章**（约 100 篇文章、约 40 万字）按主题组织，带有反向链接和交叉引用
- **派生产出**，如 Marp 幻灯片、matplotlib 图表，以及归档回维基的查询答案
- LLM 自动维护概念之间的**链接图**，为新文章候选寻找关联

## 第三阶段：查询与增强（Query and Enhance）

这是知识库发挥作用的地方：

- **Obsidian IDE** 用于浏览维基和可视化内容
- **问答 Agent** 用于跨文章的复杂研究问题——答案以 Markdown、幻灯片或图表形式呈现
- **搜索引擎**——一个凭直觉写就（vibe-coded）的朴素搜索引擎，覆盖整个维基，可通过 Web UI 使用，也可作为 LLM 的 CLI 工具
- 关键的是，查询的产出会被**归档回维基**，因此每一次探索都在积累

## 第四阶段：检查与维护（Lint and Maintain）

LLM 对维基执行健康检查：

- 扫描不一致的数据
- 通过网络搜索补全缺失的信息
- 发现概念之间可能成为新文章的关联
- 建议进一步探索的问题

检查完成后，循环回到第二阶段——维基持续生长和改进。

## 为什么这样可行

这种方法有几个突出之处：

1. **无需向量数据库**——在个人知识库规模下（约 100 篇文章），索引文件 + LLM 上下文窗口已足以完成检索
2. **探索始终在积累**——每一次查询、图表和答案都会被归档回维基
3. **由 LLM 负责写作**——你几乎不需要手动编辑维基；LLM 负责编译、链接和维护
4. **增量编译**——新的原始数据会被整合到现有维基结构中，而不是从头重新处理

## 下一步

Karpathy 提到了一个未来方向：用维基生成**合成训练数据**，并微调一个 LLM，使其在权重中"记住"这些数据，而不仅仅依赖上下文窗口。那将把一个个人知识库转化为一个个性化模型。

## 自己动手试试

所需的工具很简单：

- **Obsidian** 作为 IDE 和文件查看器
- **Obsidian Web Clipper** 用于摄入文章
- 任何具有足够大上下文窗口的 LLM 用于编译
- 一个 Markdown 目录结构作为维基

关键洞见不在于工具本身——而在于这种工作流模式：让 LLM 从原始来源增量地编译并维护一个结构化知识库，并且每一次交互都反馈回系统中。

## 我的方法：由 Agent 驱动的研究索引

我也一直在为自己的 agent 构建一个类似的个人知识库。和 Karpathy 一样，我用 Obsidian 来管理我的 Markdown 仓库。我的方法不同之处在于摄入层——我每天精选研究论文，并花了几个月时间调优一个 Skill，以自动发现高信号、相关的论文。最初靠人工审查和精选的工作，现在已经完全自动化，而且在捕捉最精华内容方面表现得惊人地出色。

这些论文使用 [qmd CLI 工具](https://github.com/tobi/qmd) 进行索引——全部是带有有用元数据的 Markdown 文件。它在语义搜索和跨数百篇论文浮现洞见方面非常出色，方式上别的东西无法比拟。

然后我将这个索引好的知识库喂给一个交互式产物生成器，它是在我的 agent 编排器内用 MCP 工具构建的。结果是数百篇论文，各种洞见被可视化并可探索。这些可视化产物是交互式的，可以动态更改——不同的视图、不同的交互、按需抛给它们的不同数据。这感觉像是我构建过的最个性化的研究系统，而且远超其他。

当我实验新的 agentic 工程概念时，agent 从这套设置中浮现的知识已经极其有用。研究的好坏取决于研究问题，而研究问题的好坏又取决于 agent 能接触到的洞见。我现在花时间的地方是如何让这些更可执行——自动化和研究循环更容易构建，但它们的好坏只取决于你喂给它们的内容。工作进行中。

---

*想在这个话题上深入了解更多？欢迎参加我们 4 月 29 日的免费线上活动 **[Building LLM Knowledge Bases](https://academy.dair.ai/events/cmnivyzyp001n04k1rnozju2n)**——我们将讲解为你的 AI agent 构建有效知识库的方法论、工具和最佳实践。[在此注册](https://academy.dair.ai/events/cmnivyzyp001n04k1rnozju2n)。*

Newsletter

### 在 AI 领域保持领先

获取实用的 AI 工程洞见、教程和课程更新——直达你的收件箱。
