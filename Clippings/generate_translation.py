#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Chinese translation of GPT-3 paper sections 7-end."""

def main():
    out_path = "/Users/zhoujie/Library/Mobile Documents/iCloud~md~obsidian/Documents/JieDocs/Clippings/Language Models are Few-Shot Learners - Sections 7-End Chinese Translation.md"
    
    lines = []
    
    # ===== SECTION 7: Related Work =====
    lines.append("## 7 相关工作\n")
    lines.append("")
    lines.append("多条研究路线致力于增加语言模型中的参数量和/或计算量，以此作为提升生成性能或任务性能的手段。早期的工作将基于 LSTM 的语言模型扩展到超过十亿个参数 [^51]。一条研究路线直接增大 Transformer 模型的规模，按比例扩展参数量和每个 token 的 FLOPS。沿着这一方向的工作已相继将模型规模提升到：原始论文中的 2.13 亿参数 [^134]、3 亿参数 [^20]、15 亿参数 [^117]、80 亿参数 [^125]、110 亿参数 [^116]，以及最近的 170 亿参数 [^132]。第二条研究路线侧重于增加参数量但不增加计算量，以此在不增加计算成本的情况下提高模型存储信息的能力。这些方法依赖于条件计算框架 [^10]，具体来说，混合专家方法 [^124] 已被用于生成 1000 亿参数的模型以及最近 500 亿参数的翻译模型 [^3]，尽管每次前向传播中实际使用的参数只占一小部分。第三种方法在不增加参数量的情况下增加计算量；此类方法的例子包括自适应计算时间 [^35] 和通用 Transformer [^22]。我们的工作侧重于第一种方法（通过直接增大神经网络来同时扩展计算量和参数量），并将模型规模比之前采用此策略的模型提升了 10 倍。\n")
    lines.append("")
    lines.append("多项工作也系统地研究了规模对语言模型性能的影响。[^57] [^114] [^77] [^42] 发现，随着自回归语言模型规模的增大，损失呈现出平滑的幂律趋势。这项工作表明，随着模型继续扩展，这一趋势在很大程度上仍在延续（尽管在图 3.1 中或许可以观察到曲线的轻微弯曲），并且我们还发现在跨越 3 个数量级的规模扩展中，许多（尽管不是全部）下游任务的性能也呈现出相对平滑的提升。\n")
    lines.append("")
    lines.append("另一条研究路线与扩展相反，试图在尽可能小的语言模型中保持强劲性能。这种方法包括 ALBERT [^62]，以及通用 [^44] 和特定任务 [^121] [^52] [^59] 的语言模型蒸馏方法。这些架构和技术可能与我们的工作互补，并可应用于减少巨型模型的延迟和内存占用。\n")
    lines.append("")
    lines.append("随着微调后的语言模型在许多标准基准任务上接近人类水平，大量工作致力于构建更困难或更开放的任务，包括问答 [^58] [^47] [^14] [^84]、阅读理解 [^16] [^106]，以及为现有语言模型设计的对抗性构建数据集 [^118] [^94]。在本工作中，我们在这些数据集上测试了我们的模型。\n")
    lines.append("")
    lines.append("许多先前的工作专门聚焦于问答任务，这构成了我们测试任务中相当大的一部分。最近的工作包括 [^116] [^115]，它们微调了一个 110 亿参数的语言模型，以及 [^33]，它专注于在测试时对大量数据进行注意力处理。我们的工作不同之处在于聚焦于上下文学习，但未来可以与 [^33] [^75] 的工作相结合。\n")
    lines.append("")
    lines.append("语言模型中的元学习已在 [^117] 中被使用，但结果非常有限且没有系统性研究。更广泛地说，语言模型元学习具有内循环-外循环结构，使其在结构上类似于应用于一般机器学习的元学习。这方面有大量的文献，包括匹配网络 [^133]、RL2 [^26]、学会优化 [^109] [^1] [^73] 和 MAML [^30]。我们将先前示例填入模型上下文的方法在结构上最类似于 RL2，也类似于 [^45]，其特点是通过模型在时间步上的激活计算进行内循环适应（无需更新权重），而外循环（这里就是语言模型预训练）则更新权重，并隐式地学习适应或在推理时识别任务的能力。少样本自回归密度估计在 [^107] 中有所探索，[^38] 则将低资源 NMT 作为一个少样本学习问题进行研究。\n")
    lines.append("")
    lines.append("虽然我们少样本方法的机制不同，但先前的工作也探索了利用预训练语言模型结合梯度下降进行少样本学习的方法 [^126]。另一个目标类似的子领域是半监督学习，其中诸如 UDA [^137] 等方法也探索了在标注数据极少的情况下进行微调的方法。\n")
    lines.append("")
    lines.append("在监督设置中，[^87] 首次形式化了以自然语言向多任务模型提供指令的方法，并在 [^117] 中将其用于语言模型中的某些任务（如摘要）。以自然语言呈现任务的概念也在文本到文本 Transformer [^116] 中得到了探索，不过在那里它是用于多任务微调，而非无需权重更新的上下文学习。\n")
    lines.append("")
    lines.append('另一种提升语言模型通用性和迁移学习能力的方法是多任务学习 [^12]，它在多个下游任务的混合数据上共同进行微调，而不是为每个任务分别更新权重。如果成功，多任务学习可以允许单个模型在不更新权重的情况下用于多个任务（类似于我们的上下文学习方法），或者可以在为新任务更新权重时提高样本效率。多任务学习已经显示出一些有前景的初步结果 [^67] [^76]，多阶段微调最近已成为某些数据集上 SOTA 结果的标准组成部分 [^97]，并在某些任务上突破了边界 [^55]，但它仍然受限于需要手动策划数据集集合和设置训练课程。相比之下，足够大规模下的预训练似乎提供了一种\u201c自然\u201d的广泛任务分布，隐含地包含在预测文本本身之中。未来工作的一个方向可能是尝试为多任务学习生成更广泛的任务集，例如通过程序生成 [^128]、人类交互 [^144] 或主动学习 [^80]。\n')
    lines.append("")
    lines.append("过去两年中语言模型的算法创新巨大，包括基于去噪的双向性 [^20]、prefixLM [^24] 和编码器-解码器架构 [^72] [^116]、训练期间的随机排列 [^139]、提高采样效率的架构 [^28]、数据和训练过程的改进 [^74]，以及嵌入参数的效率提升 [^62]。这些技术中有许多在下游任务上带来了显著的性能提升。在本工作中，我们继续专注于纯自回归语言模型，既是为了聚焦于上下文学习性能，也是为了降低我们大型模型实现的复杂性。然而，将这些算法进展与 GPT-3 的规模相结合很可能能够改善 GPT-3 在下游任务上的性能，特别是在微调设置中，将 GPT-3 的规模与这些算法技术结合是未来一个有前景的方向。\n")
    lines.append("")
    
    # ===== SECTION 8: Conclusion =====
    lines.append("## 8 结论\n")
    lines.append("")
    lines.append("我们提出了一个 1750 亿参数的语言模型，它在零样本、单样本和少样本设置下的许多 NLP 任务和基准测试中展现出强劲的性能，在某些情况下几乎达到了最先进微调系统的性能水平，同时还能生成高质量的样本并在即时定义的任务上表现出强大的定性性能。我们记录了在不使用微调的情况下，规模扩展所带来的大致可预测的性能趋势。我们还讨论了这类模型的社会影响。尽管存在许多限制和弱点，但这些结果表明，非常大的语言模型可能是开发适应性、通用语言系统的重要组分。\n")
    lines.append("")
    
    # ===== Acknowledgements =====
    lines.append("## 致谢\n")
    lines.append("")
    lines.append("作者们感谢 Ryan Lowe 对论文草稿提供的详细反馈。感谢 Jakub Pachocki 和 Szymon Sidor 建议任务，感谢 Greg Brockman、Michael Petrov、Brooke Chan 和 Chelsea Voss 协助在 OpenAI 的基础设施上运行评估。感谢 David Luan 在扩展该项目中的初始支持，感谢 Irene Solaiman 讨论接近和评估偏见的方法，感谢 Harrison Edwards 和 Yura Burda 在上下文学习方面的讨论和实验，感谢 Geoffrey Irving 和 Paul Christiano 关于语言模型扩展的早期讨论，感谢 Long Ouyang 在人类评估实验设计方面的建议，感谢 Chris Hallacy 关于数据收集的讨论，感谢 Shan Carter 在视觉设计方面的帮助。感谢数百万为模型训练创建内容的用户，以及参与索引或点赞内容（就 WebText 而言）的用户。此外，我们感谢整个 OpenAI 基础设施和超级计算团队，是他们使如此规模的模型训练成为可能。\n")
    lines.append("")
    
    # ===== Contributions =====
    lines.append("## 贡献\n")
    lines.append("")
    lines.append("Tom Brown、Ben Mann、Prafulla Dhariwal、Dario Amodei、Nick Ryder、Daniel M Ziegler 和 Jeffrey Wu 实现了大规模模型、训练基础设施和模型并行策略。\n")
    lines.append("")
    lines.append("Tom Brown、Dario Amodei、Ben Mann 和 Nick Ryder 进行了预训练实验。\n")
    lines.append("")
    lines.append("Ben Mann 和 Alec Radford 收集、过滤、去重并对训练数据进行了重叠分析。\n")
    lines.append("")
    lines.append("Melanie Subbiah、Ben Mann、Dario Amodei、Jared Kaplan、Sam McCandlish、Tom Brown、Tom Henighan 和 Girish Sastry 实现了下游任务及支持它们的软件框架，包括创建合成任务。\n")
    lines.append("")
    lines.append("Jared Kaplan 和 Sam McCandlish 最初预测巨型语言模型应表现出持续的性能提升，并应用扩展定律来帮助预测和指导模型及数据扩展决策。\n")
    lines.append("")
    lines.append("Ben Mann 实现了训练期间的不放回采样。\n")
    lines.append("")
    lines.append("Alec Radford 最初证明了语言模型中出现少样本学习能力。\n")
    lines.append("")
    lines.append("Jared Kaplan 和 Sam McCandlish 展示了更大的模型在上下文中学习更快，并系统研究了上下文学习曲线、任务提示和评估方法。\n")
    lines.append("")
    lines.append("Prafulla Dhariwal 实现了代码库的早期版本，并开发了全半精度训练的内存优化。\n")
    lines.append("")
    lines.append("Rewon Child 和 Mark Chen 开发了我们模型并行策略的早期版本。\n")
    lines.append("")
    lines.append("Rewon Child 和 Scott Gray 贡献了稀疏 Transformer。\n")
    lines.append("")
    lines.append("Aditya Ramesh 试验了预训练的损失缩放策略。\n")
    lines.append("")
    lines.append("Melanie Subbiah 和 Arvind Neelakantan 实现、实验并测试了束搜索。\n")
    lines.append("")
    lines.append("Pranav Shyam 在 SuperGLUE 上工作，并协助连接少样本学习和元学习文献。\n")
    lines.append("")
    lines.append("Sandhini Agarwal 进行了公平性和代表性分析。\n")
    lines.append("")
    lines.append("Girish Sastry 和 Amanda Askell 进行了模型的人类评估。\n")
    lines.append("")
    lines.append("Ariel Herbert-Voss 进行了恶意使用的威胁分析。\n")
    lines.append("")
    lines.append("Gretchen Krueger 编辑并对论文的政策部分进行了红队测试。\n")
    lines.append("")
    lines.append("Benjamin Chess、Clemens Winter、Eric Sigler、Christopher Hesse、Mateusz Litwin 和 Christopher Berner 优化了 OpenAI 的集群以高效运行最大规模的模型。\n")
    lines.append("")
    lines.append("Scott Gray 开发了训练中使用的高速 GPU 内核。\n")
    lines.append("")
    lines.append("Jack Clark 领导了伦理影响分析——公平性与代表性、模型的人类评估以及更广泛的影响分析，并指导了 Gretchen、Amanda、Girish、Sandhini 和 Ariel 的工作。\n")
    lines.append("")
    lines.append("Dario Amodei、Alec Radford、Tom Brown、Sam McCandlish、Nick Ryder、Jared Kaplan、Sandhini Agarwal、Amanda Askell、Girish Sastry 和 Jack Clark 撰写了论文。\n")
    lines.append("")
    lines.append("Sam McCandlish 领导了模型扩展的分析，并指导了 Tom Henighan 和 Jared Kaplan 的工作。\n")
    lines.append("")
    lines.append("Alec Radford 从 NLP 角度为项目提供建议，建议任务，将结果置于上下文中，并展示了权重衰减对训练的好处。\n")
    lines.append("")
    lines.append("Ilya Sutskever 是扩展大型生成式似然模型的早期倡导者，并指导了 Pranav、Prafulla、Rewon、Alec 和 Aditya 的工作。\n")
    lines.append("")
    lines.append("Dario Amodei 设计并领导了这项研究。\n")
    lines.append("")
    
    # ===== Appendix A =====
    lines.append("## 附录 A Common Crawl 过滤的详细信息\n")
    lines.append("")
    lines.append("如第 2.2 节所述，我们采用了两种技术来提高 Common Crawl 数据集的质量：（1）过滤 Common Crawl 和（2）模糊去重：\n")
    lines.append("")
    lines.append("1. 为了提高 Common Crawl 的质量，我们开发了一种自动过滤方法以移除低质量文档。使用原始 WebText 作为高质量文档的代理，我们训练了一个分类器来区分高质量文档和原始 Common Crawl。然后我们使用这个分类器对 Common Crawl 进行重采样，优先选择被分类器预测为高质量的文档。该分类器使用逻辑回归分类器进行训练，特征来自 Spark 的标准 tokenizer 和 HashingTF <sup>10</sup>。对于正例，我们使用了一系列精选数据集，如 WebText、Wikipedia 和我们的网络书籍语料库；对于负例，我们使用了未经过滤的 Common Crawl。我们使用该分类器对 Common Crawl 文档进行评分。我们将每个文档保留在数据集中当且仅当\n")
    lines.append("$$\n")
    lines.append("\\verb|np.random.pareto|(\\alpha)>1-\\verb|document_score|\n")
    lines.append("$$\n")
    lines.append("我们选择 $\\alpha=9$ 以主要获取分类器评分较高的文档，但仍包括一些分布之外的文档。$\\alpha$ 的选择旨在匹配分类器在 WebText 上的得分分布。我们发现这种重新加权提高了质量，如在一系列分布外生成文本样本上的损失所衡量的。\n")
    lines.append("2. 为了进一步提高模型质量并防止过拟合（随着模型容量的增加，这变得越来越重要），我们在每个数据集内对文档进行了模糊去重（即移除与其他文档高度重叠的文档），使用 Spark 的 MinHashLSH 实现，采用 10 个哈希值，使用与上述分类相同的特征。我们还从 Common Crawl 中模糊地去除了 WebText。总体而言，这使数据集大小平均减少了 10%。\n")
    lines.append("")
    lines.append("在过滤去重和质量之后，我们还部分移除了基准数据集中出现的文本，详见附录 C。\n")
    lines.append("")
    
    # ===== Appendix B =====
    lines.append("## 附录 B 模型训练的详细信息\n")
    lines.append("")
    lines.append("为了训练所有版本的 GPT-3，我们使用 Adam 优化器，参数为 $\\beta_{1}=0.9$、$\\beta_{2}=0.95$ 和 $\\epsilon=10^{-8}$，我们将梯度的全局范数裁剪到 1.0，并使用余弦衰减将学习率降至其初始值的 10%，覆盖 2600 亿个 token（在 2600 亿个 token 之后，训练以原始学习率的 10% 继续进行）。在前 3.75 亿个 token 上进行线性学习率预热。我们还将批量大小从较小值（32k 个 token）线性增加到完整值，根据模型大小不同，在前 40-120 亿个 token 的训练中完成这一过程。训练期间对数据进行不放回采样（直到达到 epoch 边界），以最小化过拟合。所有模型使用 0.1 的权重衰减以提供少量正则化 [^68]。\n")
    lines.append("")
    lines.append("在训练过程中，我们始终在完整的 $n_{\\mathrm{ctx}}=2048$ token 上下文窗口序列上进行训练，当文档长度小于 2048 时，将多个文档打包到一个序列中，以提高计算效率。包含多个文档的序列不会以任何特殊方式进行掩码处理，而是通过特殊的文本结束 token 来分隔序列中的文档，为语言模型提供必要的信息以推断由文本结束 token 分隔的上下文是不相关的。这允许高效训练，无需任何特殊的序列特定掩码。\n")
    lines.append("")
    
    # ===== Appendix C =====
    lines.append("## 附录 C 测试集污染研究的详细信息\n")
    lines.append("")
    lines.append("在第 4.1 节中，我们给出了测试集污染研究的高级概述。在本节中，我们提供方法论和结果的详细信息。\n")
    lines.append("")
    lines.append("##### 初始训练集过滤\n")
    lines.append("")
    lines.append("我们尝试通过搜索本工作中使用的所有测试/开发集与训练数据之间的 $13$ 元语法重叠来移除训练数据中出现在基准测试中的文本，并移除发生冲突的 $13$ 元语法及其周围 200 个字符的窗口，将原始文档分割成多个片段。为了过滤目的，我们将一个语法（gram）定义为小写、空白分隔的单词，不含标点符号。长度小于 $200$ 个字符的片段被丢弃。分割成超过 10 个片段的文档被视为受污染并被完全移除。最初我们会在一次碰撞时就移除整个文档，但这过度惩罚了长文档（如书籍）的误报。一个误报的例子可能是基于 Wikipedia 的测试集，其中 Wikipedia 文章引用了书中的一行。我们忽略了匹配超过 10 个训练文档的 $13$ 元语法，因为检查显示这些大多数包含常见的文化短语、法律模板或类似内容——这些内容我们确实希望模型学习，而不是与测试集的不需要的特定重叠。各种频率的示例可以在 GPT-3 发布仓库中找到 <sup>11</sup>。\n")
    lines.append("")
    lines.append("##### 重叠方法论\n")
    lines.append("")
    lines.append("对于第 4.1 节中的基准重叠分析，我们对每个数据集使用可变数量的单词 $N$ 来检查重叠，其中 $N$ 是示例长度的第 5 百分位数（以单词计），忽略所有标点、空白和大小写。由于在较低的 $N$ 值下会出现虚假碰撞，我们对非合成任务使用最小值 8。出于性能考虑，我们对所有任务设置最大值为 13。$N$ 的值和被标记为脏数据的数量显示在表 C.1 中。与 GPT-2 使用布隆过滤器计算测试污染的概率界限不同，我们使用 Apache Spark 计算所有训练集和测试集之间的精确碰撞。我们计算测试集与整个训练语料库之间的重叠，尽管根据第 2.2 节，我们只训练了经过过滤的 Common Crawl 文档的 40%。\n")
    lines.append("")
    lines.append('我们将一个\u201c脏\u201d示例定义为与任何训练文档有任意 $N$ 元语法重叠的示例，而\u201c干净\u201d示例定义为没有碰撞的示例。\n')
    lines.append("")
    lines.append("测试集和验证集的分割具有相似的污染水平，尽管某些测试分割没有标注。由于此分析揭示的一个错误，上述过滤在长文档（如书籍）上失败。由于成本考虑，无法在修正后的训练数据集版本上重新训练模型。因此，几个语言模型基准测试以及儿童书籍测试（Children's Book Test）显示出几乎完全的重叠，因此未被包含在本论文中。重叠情况显示在表 C.1 中。\n")
    lines.append("")
    
    # Table C.1 - keep as-is (it's data, just translate header description)
    lines.append("| 名称 | 分割 | 指标 | $N$ | Acc/F1/BLEU | 总计数 | 脏数据 Acc/F1/BLEU | 脏数据计数 | 干净数据 Acc/F1/BLEU | 干净数据计数 | 干净数据百分比 | 干净数据 vs 全部相对差异 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    lines.append("| Quac | dev | f1 | 13 | 44.3 | 7353 | 44.3 | 7315 | 54.1 | 38 | 1% | 20% |")
    lines.append("| SQuADv2 | dev | f1 | 13 | 69.8 | 11873 | 69.9 | 11136 | 68.4 | 737 | 6% | \\-2% |")
    lines.append("| DROP | dev | f1 | 13 | 36.5 | 9536 | 37.0 | 8898 | 29.5 | 638 | 7% | \\-21% |")
    lines.append("| Symbol Insertion | dev | acc | 7 | 66.9 | 10000 | 66.8 | 8565 | 67.1 | 1435 | 14% | 0% |")
    lines.append("| CoQa | dev | f1 | 13 | 86.0 | 7983 | 85.3 | 5107 | 87.1 | 2876 | 36% | 1% |")
    lines.append("| ReCoRD | dev | acc | 13 | 89.5 | 10000 | 90.3 | 6110 | 88.2 | 3890 | 39% | \\-1% |")
    lines.append("| Winograd | test | acc | 9 | 88.6 | 273 | 90.2 | 164 | 86.2 | 109 | 40% | \\-3% |")
    lines.append("| BoolQ | dev | acc | 13 | 76.0 | 3270 | 75.8 | 1955 | 76.3 | 1315 | 40% | 0% |")
    lines.append("| MultiRC | dev | acc | 13 | 74.2 | 953 | 73.4 | 558 | 75.3 | 395 | 41% | 1% |")
    lines.append("| RACE-h | test | acc | 13 | 46.8 | 3498 | 47.0 | 1580 | 46.7 | 1918 | 55% | 0% |")
    lines.append("| LAMBADA | test | acc | 13 | 86.4 | 5153 | 86.9 | 2209 | 86.0 | 2944 | 57% | 0% |")
    lines.append("| LAMBADA (No Blanks) | test | acc | 13 | 77.8 | 5153 | 78.5 | 2209 | 77.2 | 2944 | 57% | \\-1% |")
    lines.append("| WSC | dev | acc | 13 | 76.9 | 104 | 73.8 | 42 | 79.0 | 62 | 60% | 3% |")
    lines.append("| PIQA | dev | acc | 8 | 82.3 | 1838 | 89.9 | 526 | 79.3 | 1312 | 71% | \\-4% |")
    lines.append("| RACE-m | test | acc | 13 | 58.5 | 1436 | 53.0 | 366 | 60.4 | 1070 | 75% | 3% |")
    lines.append("| De $\\to$ En 16 | test | bleu-sb | 12 | 43.0 | 2999 | 47.4 | 739 | 40.8 | 2260 | 75% | \\-5% |")
    lines.append("| En $\\to$ De 16 | test | bleu-sb | 12 | 30.9 | 2999 | 32.6 | 739 | 29.9 | 2260 | 75% | \\-3% |")
    lines.append("| En $\\to$ Ro 16 | test | bleu-sb | 12 | 25.8 | 1999 | 24.9 | 423 | 26.1 | 1576 | 79% | 1% |")
    lines.append("| Ro $\\to$ En 16 | test | bleu-sb | 12 | 41.3 | 1999 | 40.4 | 423 | 41.6 | 1576 | 79% | 1% |")
    lines.append("| WebQs | test | acc | 8 | 41.5 | 2032 | 41.6 | 428 | 41.5 | 1604 | 79% | 0% |")
    lines.append("| ANLI R1 | test | acc | 13 | 36.8 | 1000 | 40.5 | 200 | 35.9 | 800 | 80% | \\-3% |")
    lines.append("| ANLI R2 | test | acc | 13 | 34.0 | 1000 | 29.4 | 177 | 35.0 | 823 | 82% | 3% |")
    lines.append("| TriviaQA | dev | acc | 10 | 71.2 | 7993 | 70.8 | 1390 | 71.3 | 6603 | 83% | 0% |")
    lines.append("| ANLI R3 | test | acc | 13 | 40.2 | 1200 | 38.3 | 196 | 40.5 | 1004 | 84% | 1% |")
    lines.append("| En $\\to$ Fr 14 | test | bleu-sb | 13 | 39.9 | 3003 | 38.3 | 411 | 40.3 | 2592 | 86% | 1% |")
    lines.append("| Fr $\\to$ En 14 | test | bleu-sb | 13 | 41.4 | 3003 | 40.9 | 411 | 41.4 | 2592 | 86% | 0% |")
    lines.append("| WiC | dev | acc | 13 | 51.4 | 638 | 53.1 | 49 | 51.3 | 589 | 92% | 0% |")
    lines.append("| RTE | dev | acc | 13 | 71.5 | 277 | 71.4 | 21 | 71.5 | 256 | 92% | 0% |")
    lines.append("| CB | dev | acc | 13 | 80.4 | 56 | 100.0 | 4 | 78.8 | 52 | 93% | \\-2% |")
    lines.append("| Anagrams 2 | dev | acc | 2 | 40.2 | 10000 | 76.2 | 705 | 37.4 | 9295 | 93% | \\-7% |")
    lines.append("| Reversed Words | dev | acc | 2 | 0.4 | 10000 | 1.5 | 660 | 0.3 | 9340 | 93% | \\-26% |")
    lines.append("| OpenBookQA | test | acc | 8 | 65.4 | 500 | 58.1 | 31 | 65.9 | 469 | 94% | 1% |")
    lines.append("| ARC (Easy) | test | acc | 11 | 70.1 | 2268 | 77.5 | 89 | 69.8 | 2179 | 96% | 0% |")
    lines.append("| Anagrams 1 | dev | acc | 2 | 15.0 | 10000 | 49.8 | 327 | 13.8 | 9673 | 97% | \\-8% |")
    lines.append("| COPA | dev | acc | 9 | 93.0 | 100 | 100.0 | 3 | 92.8 | 97 | 97% | 0% |")
    lines.append("| ARC (Challenge) | test | acc | 12 | 51.6 | 1144 | 45.2 | 31 | 51.8 | 1113 | 97% | 0% |")
    lines.append("| HellaSwag | dev | acc | 13 | 79.3 | 10042 | 86.2 | 152 | 79.2 | 9890 | 98% | 0% |")
    lines.append("| NQs | test | acc | 11 | 29.9 | 3610 | 32.7 | 52 | 29.8 | 3558 | 99% | 0% |")
    lines.append("| Cycled Letters | dev | acc | 2 | 38.6 | 10000 | 20.5 | 73 | 38.7 | 9927 | 99% | 0% |")
    lines.append("| SAT Analogies | dev | acc | 9 | 65.8 | 374 | 100.0 | 2 | 65.6 | 372 | 99% | 0% |")
    lines.append("| StoryCloze | test | acc | 13 | 87.7 | 1871 | 100.0 | 2 | 87.6 | 1869 | 100% | 0% |")
    lines.append("| Winogrande | dev | acc | 13 | 77.7 | 1267 | \\- | 0 | 77.7 | 1267 | 100% | 0% |")
    lines.append("")
    lines.append("表 C.1：所有数据集的重叠统计，按从脏到干净排序。如果一个数据集示例与训练语料库中的任何文档有单个 $N$ 元语法碰撞，则视为脏示例。"相对差异（干净 vs 全部）"显示仅使用干净示例与使用基准测试中所有示例之间的性能变化百分比。"计数"显示示例数量。"干净百分比"是干净示例占总数的百分比。对于"Acc/F1/BLEU"，我们使用"指标"列指定的指标。这些分数来自使用不同随机种子进行上下文学习随机示例的评估，因此与论文其他部分中的分数略有不同。\n")
    lines.append("")
    lines.append("##### 重叠结果\n")
    lines.append("")
    lines.append("为了了解模型看到部分数据对其在下游任务上的表现有多大帮助，我们根据脏度过滤每个验证集和测试集。然后我们仅在干净示例上运行评估，并报告干净分数与原始分数之间的相对百分比变化。如果干净分数比总体分数差超过 1% 或 2%，则表明模型可能对已看到的示例过拟合。如果干净分数显著更好，则我们的过滤方案可能优先将较容易的示例标记为脏数据。\n")
    lines.append("")
    lines.append("这种重叠度量往往会对包含从网络提取的背景信息（但不包含答案）的数据集（如 SQuAD，它从 Wikipedia 提取）或长度小于 8 个单词的示例（我们在过滤过程中忽略了这些，除了单词打乱任务）产生较高的误报率。该技术似乎未能给出良好信号的一个实例是 DROP，这是一个阅读理解任务，其中 94% 的示例是脏的。回答问题所需的信息在提供给模型的段落中，因此在训练过程中看到该段落但不看到问题和答案并不构成有意义的作弊。我们确认每个匹配的训练文档只包含源段落，而不包含数据集中的任何问题和答案。性能下降的更可能解释是，过滤后剩余的 6% 示例来自与脏示例略有不同的分布。\n")
    lines.append("")
    lines.append("图 4.2 显示，随着数据集污染程度的增加，干净/全部比例的方差增大，但并没有明显的偏向于性能提高或降低的趋势。这表明 GPT-3 对污染相对不敏感。关于我们标记为需要进一步审查的数据集的详细信息，请参见第 4.1 节。\n")
    lines.append("")
    
    # ===== Appendix D =====
    lines.append("## 附录 D 训练语言模型所使用的总计算量\n")
    lines.append("")
    lines.append("本附录包含用于计算图 2.2 中训练语言模型所用近似计算量的计算过程。作为一个简化假设，我们忽略了注意力操作，因为它通常占我们分析的模型总计算量的不到 10%。\n")
    lines.append("")
    lines.append("计算结果可见于表 D.1，并在表标题中加以说明。\n")
    lines.append("")
    lines.append("| 模型 | 总训练计算量 (PF-days) | 总训练计算量 (flops) | 参数量 (M) | 训练 token 数 (十亿) | 每个参数每个 token 的 Flops | 反向传播乘数 | 前向传播每个活跃参数每个 token 的 Flops | 每个 token 活跃参数比例 |  |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    lines.append("| T5-Small | 2.08E+00 | 1.80E+20 | 60 | 1,000 | 3 | 3 | 1 | 0.5 |  |")
    lines.append("| T5-Base | 7.64E+00 | 6.60E+20 | 220 | 1,000 | 3 | 3 | 1 | 0.5 |  |")
    lines.append("| T5-Large | 2.67E+01 | 2.31E+21 | 770 | 1,000 | 3 | 3 | 1 | 0.5 |  |")
    lines.append("| T5-3B | 1.04E+02 | 9.00E+21 | 3,000 | 1,000 | 3 | 3 | 1 | 0.5 |  |")
    lines.append("| T5-11B | 3.82E+02 | 3.30E+22 | 11,000 | 1,000 | 3 | 3 | 1 | 0.5 |  |")
    lines.append("| BERT-Base | 1.89E+00 | 1.64E+20 | 109 | 250 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| BERT-Large | 6.16E+00 | 5.33E+20 | 355 | 250 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| RoBERTa-Base | 1.74E+01 | 1.50E+21 | 125 | 2,000 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| RoBERTa-Large | 4.93E+01 | 4.26E+21 | 355 | 2,000 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 Small | 2.60E+00 | 2.25E+20 | 125 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 Medium | 7.42E+00 | 6.41E+20 | 356 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 Large | 1.58E+01 | 1.37E+21 | 760 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 XL | 2.75E+01 | 2.38E+21 | 1,320 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 2.7B | 5.52E+01 | 4.77E+21 | 2,650 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 6.7B | 1.39E+02 | 1.20E+22 | 6,660 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 13B | 2.68E+02 | 2.31E+22 | 12,850 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("| GPT-3 175B | 3.64E+03 | 3.14E+23 | 174,600 | 300 | 6 | 3 | 2 | 1.0 |  |")
    lines.append("")
    lines.append("表 D.1：从右侧开始向左移动，我们从每个模型训练所用的训练 token 数量开始。接下来我们注意到，由于 T5 使用编码器-解码器模型，在每次前向或反向传播中只有一半的参数对于每个 token 是活跃的。然后我们注意到，在前向传播中，每个 token 对于每个活跃参数涉及一次加法和一次乘法（忽略注意力）。然后我们添加一个 3 倍乘数来计及反向传播（因为计算 $\\frac{\\partial{params}}{\\partial{loss}}$ 和 $\\frac{\\partial{acts}}{\\partial{loss}}$ 使用的计算量与正向传播相似）。结合前两个数字，我们得到每个参数每个 token 的总 flops。我们将该值乘以总训练 token 数和总参数量，得到训练期间使用的总 flops 数。我们同时报告 flops 和 petaflop/s-day（每个等于 8.64e+19 flops）。\n")
    lines.append("")
    
    # ===== Appendix E =====
    lines.append("## 附录 E 合成新闻文章的人类质量评估\n")
    lines.append("")
    lines.append("本附录包含衡量人类区分 GPT-3 生成的合成新闻文章与真实新闻文章能力的实验详情。我们首先描述关于 $\\sim 200$ 词新闻文章的实验，然后描述关于 GPT-3 生成的 $\\sim 500$ 词新闻文章的初步研究。\n")
    lines.append("")
    lines.append("参与者：我们招募了 718 名不同的参与者参与 6 项实验。97 名参与者因未通过互联网检查问题而被排除，最终共有 621 名参与者：343 名男性、271 名女性和 7 名其他。参与者平均年龄约为 $\\sim 38$ 岁。所有参与者均通过 Positly 招募，该平台维护着一个来自 Mechanical Turk 的优秀工人白名单。所有参与者均位于美国，但无其他人口统计学限制。参与者因参与获得 12 美元报酬，该报酬基于试点运行确定的 60 分钟任务时间预估。为了确保每项实验测验的参与者样本是唯一的，参与者不得多次参加同一项实验。\n")
    lines.append("")
    lines.append("流程与设计：我们任意选择了 25 篇 2020 年初出现在 [newser.com](https://ar5iv.labs.arxiv.org/html/newser.com) 上的新闻文章。我们使用文章标题和副标题，从 125M、350M、760M、1.3B、2.7B、6.7B、13.0B 和 200B（GPT-3）参数的语言模型中生成输出。每个模型为每个问题生成五个输出，并自动选择词数最接近人类撰写文章的生成结果。这是为了最小化补全长度可能对参与者判断造成的影响。每个模型的输出流程相同，只是移除了故意设置的差控制模型，如正文所述。\n")
    lines.append("")
    lines.append("在每项实验中，一半参与者被随机分配到测验 A，另一半被随机分配到测验 B。每个测验包含 25 篇文章：一半（12-13 篇）为人类撰写，一半（12-13 篇）为模型生成：在测验 A 中有人类撰写补全的文章在测验 B 中有模型生成的补全，反之亦然。每个参与者的测验问题顺序被随机打乱。参与者可以留下评论，并被要求说明他们之前是否见过这些文章。参与者被指示在测验期间不要查找文章或其内容，在测验结束时被询问是否在测验期间查找了任何信息。\n")
    lines.append("")
    lines.append("| 模型 | 招募参与者数 | 排除参与者数 | 性别 (男:女:其他) | 平均年龄 | 平均词数 (人类:模型) |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    lines.append("| Control | 76 | 7 | 32:37:0 | 39 | 216:216 |")
    lines.append("| GPT-3 Small | 80 | 7 | 41:31:1 | 40 | 216:188 |")
    lines.append("| GPT-3 Medium | 80 | 7 | 46:28:2 | 39 | 216:202 |")
    lines.append("| GPT-3 Large | 81 | 24 | 46:28:2 | 37 | 216:200 |")
    lines.append("| GPT-3 XL | 79 | 14 | 32:32:1 | 38 | 216:199 |")
    lines.append("| GPT-3 2.7B | 80 | 11 | 36:33:0 | 40 | 216:202 |")
    lines.append("| GPT-3 6.7B | 76 | 5 | 46:28:2 | 37 | 216:195 |")
    lines.append("| GPT-3 13.0B | 81 | 13 | 46:28:2 | 37 | 216:209 |")
    lines.append("| GPT-3 175B | 80 | 9 | 42:29:0 | 37 | 216:216 |")
    lines.append("")
    lines.append("表 E.1：每项评估人类检测 $\\sim 200$ 词模型生成新闻文章的实验的参与者详情和文章长度。参与者因互联网检查失败而被排除。\n")
    lines.append("")
    lines.append("统计检验：为了比较不同运行的平均值，我们对每个模型相对于控制模型进行了独立组的两样本 t 检验。这是在 Python 中使用 `scipy.stats.ttest_ind` 函数实现的。在绘制参与者平均准确率与模型大小的回归线时，我们拟合了形式为 $ax^{-b}$ 的幂律。95% 置信区间根据样本均值的 t 分布估计。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/img/newsduration.png)\n")
    lines.append("")
    lines.append("图 E.1：随着模型规模的增大，参与者花费更多时间试图判断每篇新闻文章是否为机器生成的。控制模型上的持续时间以虚线表示。最佳拟合线是对数尺度上的线性模型，带 95% 置信区间。\n")
    lines.append("")
    lines.append("持续时间统计：在正文中，我们讨论了人类参与者区分模型生成和人类撰写的新闻文章的能力随着我们模型规模的增大而下降的发现。我们还发现，特定问题集的平均花费时间随着模型规模的增大而增加，如图 E.1 所示。尽管参与者投入了更多时间，但准确率分数却更低，这支持了较大模型生成的新闻文章更难以区分的发现。\n")
    lines.append("")
    lines.append("$\\sim 500$ 词文章的初步研究：我们通过 Positly 招募了 160 名不同的美国参与者参加 2 项实验（详情见表 E.2）。我们随机选择了 12 篇 2019 年末的路透社世界新闻文章，并为 GPT-3 175B 创建了一个上下文，其中包含一篇不在该 12 篇文章中的路透社文章。然后我们使用文章标题和路透社地点从 GPT-3 175B 和先前实验中的 160M 控制模型生成补全。这些被用于为每个模型创建两个 12 题测验，每个测验包含一半人类撰写和一半模型生成的文章。添加了理解问题，并以 30 秒为间隔分 3 个阶段向参与者展示文章，以鼓励更仔细的阅读。参与者为此任务获得 12 美元报酬。模型生成选择方法、排除标准和统计检验与之前的实验相同。\n")
    lines.append("")
    lines.append("| 模型 | 招募参与者数 | 排除参与者数 | 性别 (男:女:其他) | 平均年龄 | 平均词数 (人类:模型) |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    lines.append("| Control | 79 | 17 | 32:37:0 | 39 | 569:464 |")
    lines.append("| GPT-3 175B | 81 | 19 | 32:30:0 | 40 | 569:498 |")
    lines.append("")
    lines.append("表 E.2：调查人类检测 $\\sim 500$ 词模型生成新闻文章的实验的参与者详情和文章长度。参与者因互联网检查失败而被排除。\n")
    lines.append("")
    
    # ===== Appendix F =====
    lines.append("## 附录 F GPT-3 的更多样本\n")
    lines.append("")
    lines.append("GPT-3 能够很好地适应除论文主体部分探索的任务之外的许多其他任务。例如，在图 F.1 中，我们展示了从一个提示生成的四个未经筛选的样本，该提示建议模型以 Wallace Stevens 的风格写一首给定标题的诗。我们首先尝试了几个提示，然后生成了四个样本，未进行额外的编辑或筛选（使用温度 $1$ 进行采样，采用 $P=0.9$ 的核采样 [^40]）。补全在模型开始写入新的标题和作者头或转入散文式评论时被截断。\n")
    lines.append("")
    lines.append("| 上下文 $\\to$ | The City |")
    lines.append("| --- | --- |")
    lines.append("|  | BY C. P. CAVAFY |")
    lines.append("|  | TRANSLATED BY EDMUND KEELEY |")
    lines.append("|  | \\[Poem text omitted\\] |")
    lines.append("|  | SOME TREES |")
    lines.append("|  | John Ashbery |")
    lines.append("|  | \\[Poem text omitted\\] |")
    lines.append("|  | Shadows on the Way |")
    lines.append("|  | Wallace Stevens |")
    lines.append("| \\-------- Generated Poem 1 -------- | \\-------- Generated Poem 3 -------- |")
    lines.append("| I must have shadows on the way | The sun was all we had. Now, in the shade |")
    lines.append("| If I am to walk I must have | All is changed. The mind must dwell on those |")
    lines.append("| Each step taken slowly and alone | White fields, that to its eyes were always old; |")
    lines.append("| To have it ready made | Those ancient gleams, convoluting |")
    lines.append("|  | The way they lay among the huge roots, |")
    lines.append("| And I must think in lines of grey | The great dark tomes of reverie, |")
    lines.append("| To have dim thoughts to be my guide | The plumed labyrinth of the sea. |")
    lines.append("| Must look on blue and green |  |")
    lines.append("| And never let my eye forget | When our own breath gonne faint and fade |")
    lines.append("| That color is my friend | Up the long stairway of the dead |")
    lines.append("| And purple must surround me too | We shall remember well |")
    lines.append("|  | The blindness of the light, the whiteness |")
    lines.append("| The yellow of the sun is no more | Of that white land. The footsteps, and |")
    lines.append("| Intrusive than the bluish snow | The grasses in that light, and in the shade |")
    lines.append("| That falls on all of us. I must have | The menacing life. |")
    lines.append("| Grey thoughts and blue thoughts walk with me |  |")
    lines.append("| If I am to go away at all. | We played, too, once, in the warmest rooms. |")
    lines.append("|  | To one content, there is one content |")
    lines.append("| \\-------- Generated Poem 2 -------- | For all mankind. The forest glades |")
    lines.append("|  | Are all the more for being in fable, |")
    lines.append("| There is a way in the world. | And wood and town in legend shadowed- |")
    lines.append("| That way a man may live in a small town | Once more to return. The one content |")
    lines.append("| His lifetime and see no man come, | Has in it every happiness, more brave |")
    lines.append("| Never the stir of men about a market, | For being purposeless; and so |")
    lines.append("| Never the bobbing of covered carts, | Those island gardens, deep in the mind, |")
    lines.append("| Never the creak passed on the stair | Make of remoteness familiarity |")
    lines.append("| Closing some other life; an old man | And of the unspoken name a friend. |")
    lines.append("| Can prosper in that town, can prosper |  |")
    lines.append("| When his store is seen to close, his wife | \\-------- Generated Poem 4 -------- |")
    lines.append("| Fades in his house, and the world shouts in vain |  |")
    lines.append("| That no one comes to hear him | Nobody will come to this place. It is a road that leads nowhere. |")
    lines.append("| Where his small bell tolls. | The solitude is deep. The mountains are high. |")
    lines.append("| In that small town | But they are desolate, and they turn the traveler's face |")
    lines.append("| Everything is known. | Towards the North. All the sounds of the world are far away. |")
    lines.append("| The ways of the young men are known, | When the wind rises above the trees, |")
    lines.append("| And the ways of the young women | The boughs bow to the ground. |")
    lines.append("| As they walk to the Spring; | Even the birds that inhabit the tangle of weeds |")
    lines.append("| The rumors are all known, | That is the roadside cover, are silent. One listens, |")
    lines.append("| The quarrels, the hurt, the envy | But hears no roar of the forest. One is alone. |")
    lines.append("| Of the men and the women. | One will be taken. |")
    lines.append("| Till a day comes | One will be taken. |")
    lines.append("| That way out of the world | There is no utterance, there is no conversation, |")
    lines.append("| That leads to a wood. | But one is uneasy all the same.... |")
    lines.append("| Young, the young man | There is a thin blue mist, |")
    lines.append("| Walks, a lover now, | A darkness rising like smoke, |")
    lines.append("| Knows the streets as they are and is of them. | And within that darkness |")
    lines.append("|  | A possession of the heart. |")
    lines.append("| Comes to the wood. | One will be taken.... It was here, and it will be here again- |")
    lines.append("|  | Here, under this sky empty and full of light. |")
    lines.append("| There, in the wood, among trees, |  |")
    lines.append("| He sees shadows on the way, hears voices, |  |")
    lines.append("| hears the wind and the rustling of leaves; |  |")
    lines.append("| Through an open glade |  |")
    lines.append("| He sees a shape and the shape hears: |  |")
    lines.append("| It waits as he waits, |  |")
    lines.append("| Waits as the shadows wait, |  |")
    lines.append("| As the voices wait; |  |")
    lines.append("| Shadows on the way, voices in the wind. |  |")
    lines.append("")
    lines.append("图 F.1：从一个提示生成的四个未经筛选的补全，该提示建议模型以 Wallace Stevens 的风格创作一首题为"Shadows on the Way"的诗。\n")
    lines.append("")
    
    # ===== Appendix G =====
    lines.append("## 附录 G 任务措辞和规格的详细信息\n")
    lines.append("")
    lines.append("以下图示展示了论文中包含的所有任务的格式和措辞。所有数据均来自本节中的真实数据集，此处不包含 GPT-3 的任何样本。\n")
    lines.append("")
    
    # G.1 - RACE-h
    lines.append("| 上下文 $\\to$ | 文章： |")
    lines.append("| --- | --- |")
    lines.append("|  | Informal conversation is an important part of any business relationship.Before you start a discussion,however,make sure you understand which topics are suitable and which are considered taboo in a particular culture. Latin Americans enjoy sharing information about their local history, art and customs.You may expect questions about your family,and be sure to show pictures of your children.You may feel free to ask similar questions of your Latin American friends.The French think of conversation as an art form,and they enjoy the value of lively discussions as well as disagreements. For them,arguments can be interesting and they can cover pretty much or any topic ---- as long as they occur in are respectful and intelligent manner. |")
    lines.append("|  | In the United States,business people like to discuss a wide range of topics,including opinions about work,family,hobbies,and politics. In Japan,China,and Korea,however,people are much more private.They do not share much about their thoughts,feelings,or emotions because they feel that doing so might take away from the harmonious business relationship they're trying to build.Middle Easterners are also private about their personal lives and family matters.It is considered rude,for example,to ask a businessman from Saudi Arabia about his wife or children. |")
    lines.append("|  | As a general rule,it's best not to talk about politics or religion with your business friends.This can get you into trouble,even in the United States,where people hold different religious views.In addition,discussing one's salary is usually considered unsuitable.Sports is typically a friendly subject in most parts of the world,although be careful not to criticize national sport.Instead,be friendly and praise your host's team. |")
    lines.append("|  | Q: What shouldn't you do when talking about sports with colleagues from another country? |")
    lines.append("|  | A: Criticizing the sports of your colleagues' country. |")
    lines.append("|  | Q: Which is typically a friendly topic in most places according to the author? |")
    lines.append("|  | A: Sports. |")
    lines.append("|  | Q: Why are people from Asia more private in their conversation with others? |")
    lines.append("|  | A: They don't want to have their good relationship with others harmed by informal conversation. |")
    lines.append("|  | Q: The author considers politics and religion \\_. |")
    lines.append("|  | A: |")
    lines.append("| 正确答案 $\\to$ | taboo |")
    lines.append("| 错误答案 $\\to$ | cheerful topics |")
    lines.append("| 错误答案 $\\to$ | rude topics |")
    lines.append("| 错误答案 $\\to$ | topics that can never be talked about |")
    lines.append("")
    lines.append("图 G.1：RACE-h 的格式化数据集示例。预测时，我们按照第 2 节所述对每个答案的无条件概率进行归一化处理。\n")
    lines.append("")
    
    # G.2 - ANLI R2
    lines.append("| 上下文 $\\to$ | anli 2: anli 2: The Gold Coast Hotel & Casino is a hotel and casino located in Paradise, Nevada. This locals' casino is owned and operated by Boyd Gaming. The Gold Coast is located one mile ($\\sim 1.6\\mathrm{km}$) west of the Las Vegas Strip on West Flamingo Road. It is located across the street from the Palms Casino Resort and the Rio All Suite Hotel and Casino. |")
    lines.append("| --- | --- |")
    lines.append("|  | Question: The Gold Coast is a budget-friendly casino. True, False, or Neither? |")
    lines.append("| 正确答案 $\\to$ | Neither |")
    lines.append("| 错误答案 $\\to$ | True |")
    lines.append("| 错误答案 $\\to$ | False |")
    lines.append("")
    lines.append("图 G.2：ANLI R2 的格式化数据集示例\n")
    lines.append("")
    
    # G.3 - RACE-m
    lines.append("| 上下文 $\\to$ | 文章： |")
    lines.append("| --- | --- |")
    lines.append("|  | Mrs. Smith is an unusual teacher. Once she told each student to bring along a few potatoes in plastic bag. On each potato the students had to write a name of a person that they hated And the next day, every child brought some potatoes. Some had two potatoes;some three;some up to five. |")
    lines.append("|  | Mrs. Smith then told the children to carry the bags everywhere they went, even to the toilet, for two weeks. As day after day passed, the children started to complain about the awful smell of the rotten potatoes. |")
    lines.append("|  | Those children who brought five potatoes began to feel the weight trouble of the bags. After two weeks, the children were happy to hear that the game was finally ended. Mrs. Smith asked,\"How did you feel while carrying the potatoes for two weeks?\" The children started complaining about the trouble loudly. |")
    lines.append("|  | Then Mrs. Smith told them why she asked them to play the game. She said,\"This is exactly the situation when you carry your hatred for somebody inside your heart. The terrible smell of the hatred will pollute your heart and you will carry something unnecessary with you all the time. If you cannot stand the smell of the rotten potatoes for just two weeks, can you imagine how heavy it would be to have the hatred in your heart for your lifetime? So throw away any hatred from your heart, and you'll be really happy.\" |")
    lines.append("|  | Q: Which of the following is True according to the passage? |")
    lines.append("|  | A: If a kid hated four people,he or she had to carry four potatoes. |")
    lines.append("|  | Q: We can learn from the passage that we should \\_. |")
    lines.append("|  | A: throw away the hatred inside |")
    lines.append("|  | Q: The children complained about \\_ besides the weight trouble. |")
    lines.append("|  | A: the smell |")
    lines.append("|  | Q: Mrs.Smith asked her students to write \\_ on the potatoes. |")
    lines.append("|  | A: |")
    lines.append("| 正确答案 $\\to$ | names |")
    lines.append("| 错误答案 $\\to$ | numbers |")
    lines.append("| 错误答案 $\\to$ | time |")
    lines.append("| 错误答案 $\\to$ | places |")
    lines.append("")
    lines.append("图 G.3：RACE-m 的格式化数据集示例。预测时，我们按照第 2 节所述对每个答案的无条件概率进行归一化处理。\n")
    lines.append("")
    
    # G.4 - PIQA
    lines.append("| 上下文 $\\to$ | How to apply sealant to wood. |")
    lines.append("| --- | --- |")
    lines.append("| 正确答案 $\\to$ | Using a brush, brush on sealant onto wood until it is fully saturated with the sealant. |")
    lines.append("| 错误答案 $\\to$ | Using a brush, drip on sealant onto wood until it is fully saturated with the sealant. |")
    lines.append("")
    lines.append("图 G.4：PIQA 的格式化数据集示例\n")
    lines.append("")
    
    # G.5 - COPA
    lines.append("| 上下文 $\\to$ | My body cast a shadow over the grass because |")
    lines.append("| --- | --- |")
    lines.append("| 正确答案 $\\to$ | the sun was rising. |")
    lines.append("| 错误答案 $\\to$ | the grass was cut. |")
    lines.append("")
    lines.append("图 G.5：COPA 的格式化数据集示例\n")
    lines.append("")
    
    # G.6 - ReCoRD
    lines.append("| 上下文 $\\to$ | (CNN) Yuval Rabin, whose father, Yitzhak Rabin, was assassinated while serving as Prime Minister of Israel, criticized Donald Trump for appealing to \"Second Amendment people\" in a speech and warned that the words that politicians use can incite violence and undermine democracy. \"Trump's words are an incitement to the type of political violence that touched me personally,\" Rabin wrote in USAToday. He said that Trump's appeal to \"Second Amendment people\" to stop Hillary Clinton -- comments that were criticized as a call for violence against Clinton, something Trump denied -- \"were a new level of ugliness in an ugly campaign season.\" |")
    lines.append("| --- | --- |")
    lines.append("|  | \\- The son of a former Israeli Prime Minister who was assassinated wrote an op ed about the consequence of violent political rhetoric. |")
    lines.append("|  | \\- Warns of \"parallels\" between Israel of the 1990s and the U.S. today. |")
    lines.append("| 正确答案 $\\to$ | \\- Referencing his father, who was shot and killed by an extremist amid political tension in Israel in 1995, Rabin condemned Donald Trump's aggressive rhetoric. |")
    lines.append("| 正确答案 $\\to$ | \\- Referencing his father, who was shot and killed by an extremist amid political tension in Israel in 1995, Rabin condemned Trump's aggressive rhetoric. |")
    lines.append("| 错误答案 $\\to$ | \\- Referencing his father, who was shot and killed by an extremist amid political tension in Israel in 1995, Rabin condemned Hillary Clinton's aggressive rhetoric. |")
    lines.append("| 错误答案 $\\to$ | \\- Referencing his father, who was shot and killed by an extremist amid political tension in Israel in 1995, Rabin condemned U.S.'s aggressive rhetoric. |")
    lines.append("| 错误答案 $\\to$ | \\- Referencing his father, who was shot and killed by an extremist amid political tension in Israel in 1995, Rabin condemned Yitzhak Rabin's aggressive rhetoric. |")
    lines.append("")
    lines.append('图 G.6：ReCoRD 的格式化数据集示例。我们将上述上下文视为单个\u201c问题\u201d，因为这是 ReCoRD 数据集呈现任务的方式，也是 ReCoRD 评估脚本评分的方式。\n')
    lines.append("")
    
    # G.7 - ANLI R1
    lines.append("| 上下文 $\\to$ | anli 1: anli 1: Fulton James MacGregor MSP is a Scottish politician who is a Scottish National Party (SNP) Member of Scottish Parliament for the constituency of Coatbridge and Chryston. MacGregor is currently Parliamentary Liaison Officer to Shona Robison, Cabinet Secretary for Health & Sport. He also serves on the Justice and Education & Skills committees in the Scottish Parliament. |")
    lines.append("| --- | --- |")
    lines.append("|  | Question: Fulton James MacGregor is a Scottish politican who is a Liaison officer to Shona Robison who he swears is his best friend. True, False, or Neither? |")
    lines.append("| 正确答案 $\\to$ | Neither |")
    lines.append("| 错误答案 $\\to$ | True |")
    lines.append("| 错误答案 $\\to$ | False |")
    lines.append("")
    lines.append("图 G.7：ANLI R1 的格式化数据集示例\n")
    lines.append("")
    
    # G.8 - OpenBookQA
    lines.append("| 上下文 $\\to$ | Organisms require energy in order to do what? |")
    lines.append("| --- | --- |")
    lines.append("| 正确答案 $\\to$ | mature and develop. |")
    lines.append("| 错误答案 $\\to$ | rest soundly. |")
    lines.append("| 错误答案 $\\to$ | absorb light. |")
    lines.append("| 错误答案 $\\to$ | take in nutrients. |")
    lines.append("")
    lines.append("图 G.8：OpenBookQA 的格式化数据集示例。预测时，我们按照第 2 节所述对每个答案的无条件概率进行归一化处理。\n")
    lines.append("")
    
    # G.9 - HellaSwag
    lines.append("| 上下文 $\\to$ | Making a cake: Several cake pops are shown on a display. A woman and girl are shown making the cake pops in a kitchen. They |")
    lines.append("| --- | --- |")
    lines.append("| 正确答案 $\\to$ | bake them, then frost and decorate. |")
    lines.append("| 错误答案 $\\to$ | taste them as they place them on plates. |")
    lines.append("| 错误答案 $\\to$ | put the frosting on the cake as they pan it. |")
    lines.append("| 错误答案 $\\to$ | come out and begin decorating the cake as well. |")
    lines.append("")
    lines.append("图 G.9：HellaSwag 的格式化数据集示例\n")
    lines.append("")
    
    # G.10 - ANLI R3
    lines.append("| 上下文 $\\to$ | anli 3: anli 3: We shut the loophole which has American workers actually subsidizing the loss of their own job. They just passed an expansion of that loophole in the last few days: $43 billion of giveaways, including favors to the oil and gas industry and the people importing ceiling fans from China. |")
    lines.append("| --- | --- |")
    lines.append("|  | Question: The loophole is now gone True, False, or Neither? |")
    lines.append("| 正确答案 $\\to$ | False |")
    lines.append("| 错误答案 $\\to$ | True |")
    lines.append("| 错误答案 $\\to$ | Neither |")
    lines.append("")
    lines.append("图 G.10：ANLI R3 的格式化数据集示例\n")
    lines.append("")
    
    # G.11 - ARC Challenge
    lines.append("| 上下文 $\\to$ | Question: George wants to warm his hands quickly by rubbing them. Which skin surface will produce the most heat? |")
    lines.append("| --- | --- |")
    lines.append("|  | Answer: |")
    lines.append("| 正确答案 $\\to$ | dry palms |")
    lines.append("| 错误答案 $\\to$ | wet palms |")
    lines.append("| 错误答案 $\\to$ | palms covered with oil |")
    lines.append("| 错误答案 $\\to$ | palms covered with lotion |")
    lines.append("")
    lines.append("图 G.11：ARC (Challenge) 的格式化数据集示例。预测时，我们按照第 2 节所述对每个答案的无条件概率进行归一化处理。\n")
    lines.append("")
    
    # G.12 - SAT Analogies
    lines.append("| 上下文 $\\to$ | lull is to trust as |")
    lines.append("| --- | --- |")
    lines.append("| 正确答案 $\\to$ | cajole is to compliance |")
    lines.append("| 错误答案 $\\to$ | balk is to fortitude |")
    lines.append("| 错误答案 $\\to$ | betray is to loyalty |")
    lines.append("| 错误答案 $\\to$ | hinder is to destination |")
    lines.append("| 错误答案 $\\to$ | soothe is to passion |")
    lines.append("")
    lines.append("图 G.12：SAT Analogies 的格式化数据集示例\n")
    lines.append("")
    
    # G.13 - Winograd
    lines.append("| 正确上下文 $\\to$ | Grace was happy to trade me her sweater for my jacket. She thinks the sweater |")
    lines.append("| --- | --- |")
    lines.append("| 错误上下文 $\\to$ | Grace was happy to trade me her sweater for my jacket. She thinks the jacket |")
    lines.append("| 目标补全 $\\to$ | looks dowdy on her. |")
    lines.append("")
    lines.append('图 G.13：Winograd 的格式化数据集示例。我们使用的\u201c部分\u201d评估方法比较在正确和错误上下文下补全的概率。\n')
    lines.append("")
    
    # G.14 - Winogrande
    lines.append("| 正确上下文 $\\to$ | Johnny likes fruits more than vegetables in his new keto diet because the fruits |")
    lines.append("| --- | --- |")
    lines.append("| 错误上下文 $\\to$ | Johnny likes fruits more than vegetables in his new keto diet because the vegetables |")
    lines.append("| 目标补全 $\\to$ | are saccharine. |")
    lines.append("")
    lines.append('图 G.14：Winogrande 的格式化数据集示例。我们使用的\u201c部分\u201d评估方法比较在正确和错误上下文下补全的概率。\n')
    lines.append("")
    
    # G.15 - MultiRC
    lines.append("| 上下文 $\\to$ | READING COMPREHENSION ANSWER KEY |")
    lines.append("| --- | --- |")
    lines.append("|  | While this process moved along, diplomacy continued its rounds. Direct pressure on the Taliban had proved unsuccessful. As one NSC staff note put it, \"Under the Taliban, Afghanistan is not so much a state sponsor of terrorism as it is a state sponsored by terrorists.\" In early 2000, the United States began a high-level effort to persuade Pakistan to use its influence over the Taliban. In January 2000, Assistant Secretary of State Karl Inderfurth and the State Department's counterterrorism coordinator, Michael Sheehan, met with General Musharraf in Islamabad, dangling before him the possibility of a presidential visit in March as a reward for Pakistani cooperation. Such a visit was coveted by Musharraf, partly as a sign of his government's legitimacy. He told the two envoys that he would meet with Mullah Omar and press him on Bin Laden. They left, however, reporting to Washington that Pakistan was unlikely in fact to do anything,\" given what it sees as the benefits of Taliban control of Afghanistan.\" President Clinton was scheduled to travel to India. The State Department felt that he should not visit India without also visiting Pakistan. The Secret Service and the CIA, however, warned in the strongest terms that visiting Pakistan would risk the President's life. Counterterrorism officials also argued that Pakistan had not done enough to merit a presidential visit. But President Clinton insisted on including Pakistan in the itinerary for his trip to South Asia. His one-day stopover on March 25, 2000, was the first time a U.S. president had been there since 1969. At his meeting with Musharraf and others, President Clinton concentrated on tensions between Pakistan and India and the dangers of nuclear proliferation, but also discussed Bin Laden. President Clinton told us that when he pulled Musharraf aside for a brief, one-on-one meeting, he pleaded with the general for help regarding Bin Laden.\" I offered him the moon when I went to see him, in terms of better rel... [truncated] |")
    lines.append("|  | Who did The State Department feel should visit both India and Pakistan? |")
    lines.append("| 正确答案 $\\to$ | \\- \\[False\\] Bin Laden |")
    lines.append("| 错误答案 $\\to$ | \\- \\[True\\] Bin Laden |")
    lines.append("")
    lines.append("图 G.15：MultiRC 的格式化数据集示例。MultiRC 包含三个层级：（1）段落，（2）问题，和（3）答案。评估时，准确率在问题级别确定，当且仅当问题内的所有答案都被正确标注时，该问题才算正确。因此，我们使用 $K$ 来表示上下文中显示的问题数量。\n")
    lines.append("")
    
    # G.16 - ARC Easy
    lines.append("| 上下文 $\\to$ | Question: Which factor will most likely cause a person to develop a fever? |")
    lines.append("| --- | --- |")
    lines.append("|  | Answer: |")
    lines.append("| 正确答案 $\\to$ | a bacterial population in the bloodstream |")
    lines.append("| 错误答案 $\\to$ | a leg muscle relaxing after exercise |")
    lines.append("| 错误答案 $\\to$ | several viral particles on the skin |")
    lines.append("| 错误答案 $\\to$ | carbohydrates being digested in the stomach |")
    lines.append("")
    lines.append("图 G.16：ARC (Easy) 的格式化数据集示例。预测时，我们按照第 2 节所述对每个答案的无条件概率进行归一化处理。\n")
    lines.append("")
    
    # G.17 - StoryCloze
    lines.append("| 上下文 $\\to$ | Bob went to the gas station to fill up his car. His tank was completely empty and so was his wallet. The cashier offered to pay for his gas if he came back later to pay. Bob felt grateful as he drove home. |")
    lines.append("| --- | --- |")
    lines.append("| 正确答案 $\\to$ | Bob believed that there were good people in the world. |")
    lines.append("| 错误答案 $\\to$ | Bob contemplated how unfriendly the world was. |")
    lines.append("")
    lines.append("图 G.17：StoryCloze 的格式化数据集示例\n")
    lines.append("")
    
    # G.18 - CoQA
    lines.append("| 上下文 $\\to$ | Helsinki is the capital and largest city of Finland. It is in the region of Uusimaa, in southern Finland, on the shore of the Gulf of Finland. Helsinki has a population of, an urban population of, and a metropolitan population of over 1.4 million, making it the most populous municipality and urban area in Finland. Helsinki is some north of Tallinn, Estonia, east of Stockholm, Sweden, and west of Saint Petersburg, Russia. Helsinki has close historical connections with these three cities. |")
    lines.append("| --- | --- |")
    lines.append("|  | The Helsinki metropolitan area includes the urban core of Helsinki, Espoo, Vantaa, Kauniainen, and surrounding commuter towns. It is the world's northernmost metro area of over one million people, and the city is the northernmost capital of an EU member state. The Helsinki metropolitan area is the third largest metropolitan area in the Nordic countries after Stockholm and Copenhagen, and the City of Helsinki is the third largest after Stockholm and Oslo. Helsinki is Finland's major political, educational, financial, cultural, and research center as well as one of northern Europe's major cities. Approximately 75% of foreign companies that operate in Finland have settled in the Helsinki region. The nearby municipality of Vantaa is the location of Helsinki Airport, with frequent service to various destinations in Europe and Asia. |")
    lines.append("|  | Q: what is the most populous municipality in Finland? |")
    lines.append("|  | A: Helsinki |")
    lines.append("|  | Q: how many people live there? |")
    lines.append("|  | A: 1.4 million in the metropolitan area |")
    lines.append("|  | Q: what percent of the foreign companies that operate in Finland are in Helsinki? |")
    lines.append("|  | A: 75% |")
    lines.append("|  | Q: what towns are a part of the metropolitan area? |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | Helsinki, Espoo, Vantaa, Kauniainen, and surrounding commuter towns |")
    lines.append("")
    lines.append("图 G.18：CoQA 的格式化数据集示例\n")
    lines.append("")
    
    # G.19 - Cycled Letters
    lines.append("| 上下文 $\\to$ | Please unscramble the letters into a word, and write that word: |")
    lines.append("| --- | --- |")
    lines.append("|  | asinoc = |")
    lines.append("| 目标补全 $\\to$ | casino |")
    lines.append("")
    lines.append("图 G.19：Cycled Letters 的格式化数据集示例\n")
    lines.append("")
    
    # G.20 - DROP
    lines.append("| 上下文 $\\to$ | Passage: Saint Jean de Brébeuf was a French Jesuit missionary who travelled to New France in 1625. There he worked primarily with the Huron for the rest of his life, except for a few years in France from 1629 to 1633. He learned their language and culture, writing extensively about each to aid other missionaries. In 1649, Brébeuf and another missionary were captured when an Iroquois raid took over a Huron village. Together with Huron captives, the missionaries were ritually tortured and killed on March 16, 1649. Brébeuf was beatified in 1925 and among eight Jesuit missionaries canonized as saints in the Roman Catholic Church in 1930. |")
    lines.append("| --- | --- |")
    lines.append("|  | Question: How many years did Saint Jean de Brébeuf stay in New France before he went back to France for a few years? |")
    lines.append("|  | Answer: |")
    lines.append("| 目标补全 $\\to$ | 4 |")
    lines.append("")
    lines.append("图 G.20：DROP 的格式化数据集示例\n")
    lines.append("")
    
    # G.21 - LAMBADA
    lines.append("| 上下文 $\\to$ | Fill in blank: |")
    lines.append("| --- | --- |")
    lines.append("|  | She held the torch in front of her. |")
    lines.append("|  | She caught her breath. |")
    lines.append("|  | \"Chris? There's a step.\" |")
    lines.append("|  | \"What?\" |")
    lines.append("|  | \"A step. Cut in the rock. About fifty feet ahead.\" She moved faster. They both moved faster. \"In fact,\" she said, raising the torch higher, \"there's more than a \\_\\_\\_\\_. - $>$ |")
    lines.append("| 目标补全 $\\to$ | step |")
    lines.append("")
    lines.append("图 G.21：LAMBADA 的格式化数据集示例\n")
    lines.append("")
    
    # G.22 - Anagrams 1
    lines.append("| 上下文 $\\to$ | Please unscramble the letters into a word, and write that word: |")
    lines.append("| --- | --- |")
    lines.append("|  | skicts = |")
    lines.append("| 目标补全 $\\to$ | sticks |")
    lines.append("")
    lines.append("图 G.22：Anagrams 1 (A1) 的格式化数据集示例\n")
    lines.append("")
    
    # G.23 - Anagrams 2
    lines.append("| 上下文 $\\to$ | Please unscramble the letters into a word, and write that word: |")
    lines.append("| --- | --- |")
    lines.append("|  | volwskagen = |")
    lines.append("| 目标补全 $\\to$ | volkswagen |")
    lines.append("")
    lines.append("图 G.23：Anagrams 2 的格式化数据集示例\n")
    lines.append("")
    
    # G.24 - Natural Questions
    lines.append("| 上下文 $\\to$ | Q: Who played tess on touched by an angel? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | Delloreese Patricia Early (July 6, 1931 – November 19, 2017), known professionally as Della Reese |")
    lines.append("")
    lines.append("图 G.24：Natural Questions 的格式化数据集示例\n")
    lines.append("")
    
    # G.25 - QuAC
    lines.append("| 上下文 $\\to$ | TITLE: William Perry (American football) - Professional career |")
    lines.append("| --- | --- |")
    lines.append("|  | PARAGRAPH: In 1985, he was selected in the first round of the 1985 NFL Draft by the Chicago Bears; he had been hand-picked by coach Mike Ditka. However, defensive coordinator Buddy Ryan, who had a highly acrimonious relationship with Ditka, called Perry a \"wasted draft-pick\". Perry soon became a pawn in the political power struggle between Ditka and Ryan. Perry's \"Refrigerator\" nickname followed him into the NFL and he quickly became a favorite of the Chicago Bears fans. Teammates called him \"Biscuit,\" as in \"one biscuit shy of 350 pounds.\" While Ryan refused to play Perry, Ditka decided to use Perry as a fullback when the team was near the opponents' goal line or in fourth and short situations, either as a ball carrier or a lead blocker for star running back Walter Payton. Ditka stated the inspiration for using Perry as a fullback came to him during five-yard sprint exercises. During his rookie season, Perry rushed for two touchdowns and caught a pass for one. Perry even had the opportunity to run the ball during Super Bowl XX, as a nod to his popularity and contributions to the team's success. The first time he got the ball, he was tackled for a one-yard loss while attempting to throw his first NFL pass on a halfback option play. The second time he got the ball, he scored a touchdown (running over Patriots linebacker Larry McGrew in the process). About halfway through his rookie season, Ryan finally began to play Perry, who soon proved that he was a capable defensive lineman. His Super Bowl ring size is the largest of any professional football player in the history of the event. His ring size is 25, while the ring size for the average adult male is between 10 and 12. Perry went on to play for ten years in the NFL, retiring after the 1994 season. In his ten years as a pro, he regularly struggled with his weight, which hampered his performance at times. He played in 138 games, recording 29.5 sacks and five fumble recoveries, which he returned for a total of 71 ... [truncated] |")
    lines.append("|  | Q: what team did he play for? |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | the Chicago Bears |")
    lines.append("")
    lines.append("图 G.25：QuAC 的格式化数据集示例\n")
    lines.append("")
    
    # G.26 - Symbol Insertion
    lines.append("| 上下文 $\\to$ | Please unscramble the letters into a word, and write that word: |")
    lines.append("| --- | --- |")
    lines.append("|  | r e!c.i p r o.c a/l = |")
    lines.append("| 目标补全 $\\to$ | reciprocal |")
    lines.append("")
    lines.append("图 G.26：Symbol Insertion 的格式化数据集示例\n")
    lines.append("")
    
    # G.27 - Reversed Words
    lines.append("| 上下文 $\\to$ | Please unscramble the letters into a word, and write that word: |")
    lines.append("| --- | --- |")
    lines.append("|  | taefed = |")
    lines.append("| 目标补全 $\\to$ | defeat |")
    lines.append("")
    lines.append("图 G.27：Reversed Words 的格式化数据集示例\n")
    lines.append("")
    
    # G.28 - SQuADv2
    lines.append("| 上下文 $\\to$ | Title: The\\_Blitz |")
    lines.append("| --- | --- |")
    lines.append("|  | Background: From the German point of view, March 1941 saw an improvement. The Luftwaffe flew 4,000 sorties that month, including 12 major and three heavy attacks. The electronic war intensified but the Luftwaffe flew major inland missions only on moonlit nights. Ports were easier to find and made better targets. To confuse the British, radio silence was observed until the bombs fell. X- and Y-Gerät beams were placed over false targets and switched only at the last minute. Rapid frequency changes were introduced for X-Gerät, whose wider band of frequencies and greater tactical flexibility ensured it remained effective at a time when British selective jamming was degrading the effectiveness of Y-Gerät. |")
    lines.append("|  | Q: How many sorties were flown in March 1941? |")
    lines.append("|  | A: 4,000 |")
    lines.append("|  | Q: When did the Luftwaffe fly inland missions? |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | only on moonlit nights |")
    lines.append("")
    lines.append("图 G.28：SQuADv2 的格式化数据集示例\n")
    lines.append("")
    
    # G.29 - BoolQ
    lines.append("| 上下文 $\\to$ | Normal force -- In a simple case such as an object resting upon a table, the normal force on the object is equal but in opposite direction to the gravitational force applied on the object (or the weight of the object), that is, N = m g (\\\\displaystyle N=mg), where m is mass, and g is the gravitational field strength (about 9.81 m/s on Earth). The normal force here represents the force applied by the table against the object that prevents it from sinking through the table and requires that the table is sturdy enough to deliver this normal force without breaking. However, it is easy to assume that the normal force and weight are action-reaction force pairs (a common mistake). In this case, the normal force and weight need to be equal in magnitude to explain why there is no upward acceleration of the object. For example, a ball that bounces upwards accelerates upwards because the normal force acting on the ball is larger in magnitude than the weight of the ball. |")
    lines.append("| --- | --- |")
    lines.append("|  | question: is the normal force equal to the force of gravity? |")
    lines.append("|  | answer: |")
    lines.append("| 目标补全 $\\to$ | yes |")
    lines.append("")
    lines.append("图 G.29：BoolQ 的格式化数据集示例\n")
    lines.append("")
    
    # G.30 - CB
    lines.append("| 上下文 $\\to$ | The trend toward lower rents may seem surprising given that some communities in New York are bemoaning the loss of favorite local businesses to high rents. But, despite the recent softening, for many of these retailers there's still been too big a jump from the rental rates of the late 1970s, when their leases were signed. Certainly, the recent drop in prices doesn't mean Manhattan comes cheap. |")
    lines.append("| --- | --- |")
    lines.append("|  | question: Manhattan comes cheap. true, false, or neither? |")
    lines.append("|  | answer: |")
    lines.append("| 目标补全 $\\to$ | false |")
    lines.append("")
    lines.append("图 G.30：CB 的格式化数据集示例\n")
    lines.append("")
    
    # G.31 - RTE
    lines.append("| 上下文 $\\to$ | The bet, which won him dinner for four, was regarding the existence and mass of the top quark, an elementary particle discovered in 1995. |")
    lines.append("| --- | --- |")
    lines.append("|  | question: The Top Quark is the last of six flavors of quarks predicted by the standard model theory of particle physics. True or False? |")
    lines.append("|  | answer: |")
    lines.append("| 目标补全 $\\to$ | False |")
    lines.append("")
    lines.append("图 G.31：RTE 的格式化数据集示例\n")
    lines.append("")
    
    # G.32 - WiC
    lines.append("| 上下文 $\\to$ | An outfitter provided everything needed for the safari. |")
    lines.append("| --- | --- |")
    lines.append("|  | Before his first walking holiday, he went to a specialist outfitter to buy some boots. |")
    lines.append("|  | question: Is the word 'outfitter' used in the same way in the two sentences above? |")
    lines.append("|  | answer: |")
    lines.append("| 目标补全 $\\to$ | no |")
    lines.append("")
    lines.append("图 G.32：WiC 的格式化数据集示例\n")
    lines.append("")
    
    # G.33 - WSC
    lines.append("| 上下文 $\\to$ | Final Exam with Answer Key |")
    lines.append("| --- | --- |")
    lines.append("|  | Instructions: Please carefully read the following passages. For each passage, you must identify which noun the pronoun marked in \\*bold\\* refers to. |")
    lines.append("|  | \\===== |")
    lines.append("|  | Passage: Mr. Moncrieff visited Chester's luxurious New York apartment, thinking that it belonged to his son Edward. The result was that Mr. Moncrieff has decided to cancel Edward's allowance on the ground that he no longer requires \\*his\\* financial support. |")
    lines.append("|  | Question: In the passage above, what does the pronoun \"\\*his\\*\" refer to? |")
    lines.append("|  | Answer: |")
    lines.append("| 目标补全 $\\to$ | mr. moncrieff |")
    lines.append("")
    lines.append("图 G.33：WSC 的格式化数据集示例\n")
    lines.append("")
    
    # G.34 - TriviaQA
    lines.append("| 上下文 $\\to$ | Q: 'Nude Descending A Staircase' is perhaps the most famous painting by which 20th century artist? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | MARCEL DUCHAMP |")
    lines.append("| 目标补全 $\\to$ | r mutt |")
    lines.append("| 目标补全 $\\to$ | duchamp |")
    lines.append("| 目标补全 $\\to$ | marcel duchamp |")
    lines.append("| 目标补全 $\\to$ | R.Mutt |")
    lines.append("| 目标补全 $\\to$ | Marcel duChamp |")
    lines.append("| 目标补全 $\\to$ | Henri-Robert-Marcel Duchamp |")
    lines.append("| 目标补全 $\\to$ | Marcel du Champ |")
    lines.append("| 目标补全 $\\to$ | henri robert marcel duchamp |")
    lines.append("| 目标补全 $\\to$ | Duchampian |")
    lines.append("| 目标补全 $\\to$ | Duchamp |")
    lines.append("| 目标补全 $\\to$ | duchampian |")
    lines.append("| 目标补全 $\\to$ | marcel du champ |")
    lines.append("| 目标补全 $\\to$ | Marcel Duchamp |")
    lines.append("| 目标补全 $\\to$ | MARCEL DUCHAMP |")
    lines.append("")
    lines.append("图 G.34：TriviaQA 的格式化数据集示例。TriviaQA 允许有多个有效的补全。\n")
    lines.append("")
    
    # G.35 - WebQA
    lines.append("| 上下文 $\\to$ | Q: What school did burne hogarth establish? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | School of Visual Arts |")
    lines.append("")
    lines.append("图 G.35：WebQA 的格式化数据集示例\n")
    lines.append("")
    
    # G.36 - De->En
    lines.append("| 上下文 $\\to$ | Keinesfalls dürfen diese für den kommerziellen Gebrauch verwendet werden. = |")
    lines.append("| --- | --- |")
    lines.append("| 目标补全 $\\to$ | In no case may they be used for commercial purposes. |")
    lines.append("")
    lines.append("图 G.36：De $\\to$ En 的格式化数据集示例。这是单样本和少样本学习的格式，对于此语言任务和其他语言任务，零样本学习的格式是"Q: What is the {language} translation of {sentence} A: {translation}."\n")
    lines.append("")
    
    # G.37 - En->De
    lines.append("| 上下文 $\\to$ | In no case may they be used for commercial purposes. = |")
    lines.append("| --- | --- |")
    lines.append("| 目标补全 $\\to$ | Keinesfalls dürfen diese für den kommerziellen Gebrauch verwendet werden. |")
    lines.append("")
    lines.append("图 G.37：En $\\to$ De 的格式化数据集示例\n")
    lines.append("")
    
    # G.38 - En->Fr
    lines.append("| 上下文 $\\to$ | Analysis of instar distributions of larval I. verticalis collected from a series of ponds also indicated that males were in more advanced instars than females. = |")
    lines.append("| --- | --- |")
    lines.append("| 目标补全 $\\to$ | L'analyse de la distribution de fréquence des stades larvaires d'I. verticalis dans une série d'étangs a également démontré que les larves mâles étaient à des stades plus avancés que les larves femelles. |")
    lines.append("")
    lines.append("图 G.38：En $\\to$ Fr 的格式化数据集示例\n")
    lines.append("")
    
    # G.39 - Fr->En
    lines.append("| 上下文 $\\to$ | L'analyse de la distribution de fréquence des stades larvaires d'I. verticalis dans une série d'étangs a également démontré que les larves mâles étaient à des stades plus avancés que les larves femelles. = |")
    lines.append("| --- | --- |")
    lines.append("| 目标补全 $\\to$ | Analysis of instar distributions of larval I. verticalis collected from a series of ponds also indicated that males were in more advanced instars than females. |")
    lines.append("")
    lines.append("图 G.39：Fr $\\to$ En 的格式化数据集示例\n")
    lines.append("")
    
    # G.40 - En->Ro
    lines.append("| 上下文 $\\to$ | The truth is that you want, at any price, and against the wishes of the peoples of Europe, to continue the negotiations for Turkey's accession to the European Union, despite Turkey's continuing refusal to recognise Cyprus and despite the fact that the democratic reforms are at a standstill. = |")
    lines.append("| --- | --- |")
    lines.append("| 目标补全 $\\to$ | Adevărul este că vă doriţi, cu orice preţ şi împotriva dorinţei europenilor, să continuaţi negocierile de aderare a Turciei la Uniunea Europeană, în ciuda refuzului continuu al Turciei de a recunoaşte Ciprul şi în ciuda faptului că reformele democratice au ajuns într-un punct mort. |")
    lines.append("")
    lines.append("图 G.40：En $\\to$ Ro 的格式化数据集示例\n")
    lines.append("")
    
    # G.41 - Ro->En
    lines.append("| 上下文 $\\to$ | Adevărul este că vă doriţi, cu orice preţ şi împotriva dorinţei europenilor, să continuaţi negocierile de aderare a Turciei la Uniunea Europeană, în ciuda refuzului continuu al Turciei de a recunoaşte Ciprul şi în ciuda faptului că reformele democratice au ajuns într-un punct mort. = |")
    lines.append("| --- | --- |")
    lines.append("| 目标补全 $\\to$ | The truth is that you want, at any price, and against the wishes of the peoples of Europe, to continue the negotiations for Turkey's accession to the European Union, despite Turkey's continuing refusal to recognise Cyprus and despite the fact that the democratic reforms are at a standstill. |")
    lines.append("")
    lines.append("图 G.41：Ro $\\to$ En 的格式化数据集示例\n")
    lines.append("")
    
    # G.42-G.51: Arithmetic tasks
    lines.append("| 上下文 $\\to$ | Q: What is (2 \\* 4) \\* 6? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 48 |")
    lines.append("")
    lines.append("图 G.42：Arithmetic 1DC 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 17 minus 14? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 3 |")
    lines.append("")
    lines.append("图 G.43：Arithmetic 2D- 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 98 plus 45? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 143 |")
    lines.append("")
    lines.append("图 G.44：Arithmetic 2D+ 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 95 times 45? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 4275 |")
    lines.append("")
    lines.append("图 G.45：Arithmetic 2Dx 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 509 minus 488? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 21 |")
    lines.append("")
    lines.append("图 G.46：Arithmetic 3D- 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 556 plus 497? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 1053 |")
    lines.append("")
    lines.append("图 G.47：Arithmetic 3D+ 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 6209 minus 3365? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 2844 |")
    lines.append("")
    lines.append("图 G.48：Arithmetic 4D- 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 9923 plus 617? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 10540 |")
    lines.append("")
    lines.append("图 G.49：Arithmetic 4D+ 的格式化数据集示例\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 40649 minus 78746? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | \\-38097 |")
    lines.append("")
    lines.append("图 G.50：Arithmetic 5D $-$\n")
    lines.append("")
    
    lines.append("| 上下文 $\\to$ | Q: What is 65360 plus 16204? |")
    lines.append("| --- | --- |")
    lines.append("|  | A: |")
    lines.append("| 目标补全 $\\to$ | 81564 |")
    lines.append("")
    lines.append("图 G.51：Arithmetic 5D+ 的格式化数据集示例\n")
    lines.append("")
    
    # ===== Appendix H =====
    lines.append("## 附录 H 所有模型规模在所有任务上的结果\n")
    lines.append("")
    lines.append("<table><tbody><tr><td></td><th></th><th></th><th></th><th></th><th colspan=\"8\">零样本 (Zero-Shot)</th><th colspan=\"8\">单样本 (One-Shot)</th><th colspan=\"8\">少样本 (Few-Shot)</th><td></td></tr><tr><th>名称</th><th>指标</th><th>分割</th><th>微调 SOTA</th><th>K</th><th>Small</th><th>Med</th><th>Large</th><th>XL</th><th>2.7B</th><th>6.7B</th><th>13B</th><th>175B</th><th>Small</th><th>Med</th><th>Large</th><th>XL</th><th>2.7B</th><th>6.7B</th><th>13B</th><th>175B</th><th>Small</th><th>Med</th><th>Large</th><th>XL</th><th>2.7B</th><th>6.7B</th><th>13B</th><th>175B</th><th>175B (测试服务器)</th></tr><tr><td>HellaSwag</td><td>acc</td><td>dev</td><td>85.6</td><td>20</td><td>33.7</td><td>43.6</td><td>51.0</td><td>54.7</td><td>62.8</td><td>67.4</td><td>70.9</td><td>78.9</td><td>33.0</td><td>42.9</td><td>50.5</td><td>53.5</td><td>61.9</td><td>66.5</td><td>70.0</td><td>78.1</td><td>33.5</td><td>43.1</td><td>51.3</td><td>54.9</td><td>62.9</td><td>67.3</td><td>71.3</td><td>79.3</td><td></td></tr><tr><td>LAMBADA</td><td>acc</td><td>test</td><td>68.0</td><td>15</td><td>42.7</td><td>54.3</td><td>60.4</td><td>63.6</td><td>67.1</td><td>70.3</td><td>72.5</td><td>76.2</td><td>22.0</td><td>47.1</td><td>52.6</td><td>58.3</td><td>61.1</td><td>65.4</td><td>69.0</td><td>72.5</td><td>22.0</td><td>40.4</td><td>63.2</td><td>57.0</td><td>78.1</td><td>79.1</td><td>81.3</td><td>86.4</td><td></td></tr><tr><td>LAMBADA</td><td>ppl</td><td>test</td><td>8.63</td><td>15</td><td>18.6</td><td>9.09</td><td>6.53</td><td>5.44</td><td>4.60</td><td>4.00</td><td>3.56</td><td>3.00</td><td>165.0</td><td>11.6</td><td>8.29</td><td>6.46</td><td>5.53</td><td>4.61</td><td>4.06</td><td>3.35</td><td>165.0</td><td>27.6</td><td>6.63</td><td>7.45</td><td>2.89</td><td>2.56</td><td>2.56</td><td>1.92</td><td></td></tr><tr><td>StoryCloze</td><td>acc</td><td>test</td><td>91.8</td><td>70</td><td>63.3</td><td>68.5</td><td>72.4</td><td>73.4</td><td>77.2</td><td>77.7</td><td>79.5</td><td>83.2</td><td>62.3</td><td>68.7</td><td>72.3</td><td>74.2</td><td>... [truncated]</td></tr></tbody></table>")
    lines.append("")
    lines.append("表 H.1：我们在本文中研究的每项任务、设置和模型的分数。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/superglue_--_boolq.png)\n")
    lines.append("")
    lines.append("图 H.1：所有 SuperGLUE 任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/sat_analogies.png)\n")
    lines.append("")
    lines.append("图 H.2：SAT 任务的结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/arithmetic.png)\n")
    lines.append("")
    lines.append("图 H.4：所有算术任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/hellaswag.png)\n")
    lines.append("")
    lines.append("图 H.5：所有完形填空和补全任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/piqa.png)\n")
    lines.append("")
    lines.append("图 H.6：所有常识推理任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/naturalqs_--_open_domain_test.png)\n")
    lines.append("")
    lines.append("图 H.7：所有 QA 任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/quac.png)\n")
    lines.append("")
    lines.append("图 H.8：所有阅读理解任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/anli_r1_test.png)\n")
    lines.append("")
    lines.append("图 H.9：所有 ANLI 轮次的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/wordscramble_cycle_letters.png)\n")
    lines.append("")
    lines.append("图 H.10：所有打乱任务的所有结果。\n")
    lines.append("")
    lines.append("![参见标题](https://ar5iv.labs.arxiv.org/html/2005.14165/assets/graphs/scale_plots/translation_sacrebleu_detoen16_test.png)\n")
    lines.append("")
    lines.append("图 H.11：所有翻译任务的所有结果。\n")
    lines.append("")
    
    # ===== References =====
    lines.append("## 参考文献\n")
    lines.append("")
    
    # References [^1]-[^144] - keep English text
    refs = [
        '[^1]: Marcin Andrychowicz, Misha Denil, Sergio Gomez, Matthew W Hoffman, David Pfau, Tom Schaul, Brendan Shillingford, and Nando De Freitas. Learning to learn by gradient descent by gradient descent. In Advances in neural information processing systems, pages 3981–3989, 2016.',
        '',
        '[^2]: WeChat AI. Tr-mt (ensemble), December 2019.',
        '',
        '[^3]: Roee Aharoni, Melvin Johnson, and Orhan Firat. Massively multilingual neural machine translation. In Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers), 2019.',
        '',
        '[^4]: Su Lin Blodgett, Solon Barocas, Hal Daumé III, and Hanna Wallach. Language (technology) is power: A critical survey of "bias" in nlp. arXiv preprint arXiv:2005.14050, 2020.',
        '',
        '[^5]: Jonathan Berant, Andrew Chou, Roy Frostig, and Percy Liang. Semantic parsing on freebase from question-answer pairs. In Proceedings of the 2013 conference on empirical methods in natural language processing, pages 1533–1544, 2013.',
        '',
        '[^6]: Luisa Bentivogli, Ido Dagan, Hoa Trang Dang, Danilo Giampiccolo, and Bernardo Magnini. The fifth PASCAL recognizing textual entailment challenge. 2009.',
        '',
        '[^7]: Stefano Baccianella, Andrea Esuli, and Fabrizio Sebastiani. Sentiwordnet 3.0: an enhanced lexical resource for sentiment analysis and opinion mining. In Lrec, volume 10, pages 2200–2204, 2010.',
        '',
        '[^8]: Roy Bar Haim, Ido Dagan, Bill Dolan, Lisa Ferro, Danilo Giampiccolo, Bernardo Magnini, and Idan Szpektor. The second PASCAL recognising textual entailment challenge. 2006.',
        '',
        '[^9]: Yonatan Bisk, Ari Holtzman, Jesse Thomason, Jacob Andreas, Yoshua Bengio, Joyce Chai, Mirella Lapata, Angeliki Lazaridou, Jonathan May, Aleksandr Nisnevich, et al. Experience grounds language. arXiv preprint arXiv:2004.10151, 2020.',
        '',
        '[^10]: Yoshua Bengio, Nicholas Léonard, and Aaron C. Courville. Estimating or propagating gradients through stochastic neurons for conditional computation. Arxiv, 2013.',
        '',
        '[^11]: Yonatan Bisk, Rowan Zellers, Ronan Le Bras, Jianfeng Gao, and Yejin Choi. Piqa: Reasoning about physical commonsense in natural language. arXiv preprint arXiv:1911.11641, 2019.',
        '',
        '[^12]: Rich Caruana. Multitask learning. Machine learning, 28(1), 1997.',
        '',
        '[^13]: Susan Carey and Elsa Bartlett. Acquiring a single new word. Proceedings of the Stanford Child Language Conference, 1978.',
        '',
        '[^14]: Peter Clark, Isaac Cowhey, Oren Etzioni, Tushar Khot, Ashish Sabharwal, Carissa Schoenick, and Oyvind Tafjord. Think you have solved question answering? try arc, the ai2 reasoning challenge. ArXiv, abs/1803.05457, 2018.',
        '',
        '[^15]: Rewon Child, Scott Gray, Alec Radford, and Ilya Sutskever. Generating long sequences with sparse transformers, 2019.',
        '',
        '[^16]: Eunsol Choi, He He, Mohit Iyyer, Mark Yatskar, Wen-tau Yih, Yejin Choi, Percy Liang, and Luke Zettlemoyer. Quac: Question answering in context. Arxiv, 2018.',
        '',
        '[^17]: Christopher Clark, Kenton Lee, Ming-Wei Chang, Tom Kwiatkowski, Michael Collins, and Kristina Toutanova. BoolQ: Exploring the surprising difficulty of natural yes/no questions. arXiv preprint arXiv:1905.10044, 2019.',
        '',
        '[^18]: Yen-Chun Chen, Linjie Li, Licheng Yu, Ahmed El Kholy, Faisal Ahmed, Zhe Gan, Yu Cheng, and Jingjing Liu. Uniter: Learning universal image-text representations. arXiv preprint arXiv:1909.11740, 2019.',
        '',
        '[^19]: Kate Crawford. The trouble with bias. NIPS 2017 Keynote, 2017.',
        '',
        '[^20]: Jacob Devlin, Ming-Wei Chang, Kenton Lee, and Kristina Toutanova. BERT: Pre-training of deep bidirectional transformers for language understanding. arXiv preprint arXiv:1810.04805, 2018.',
        '',
        '[^21]: Ido Dagan, Oren Glickman, and Bernardo Magnini. The PASCAL recognising textual entailment challenge. In Machine learning challenges. evaluating predictive uncertainty, visual object classification, and recognising textual entailment, pages 177–190. Springer, 2006.',
        '',
        '[^22]: Mostafa Dehghani, Stephan Gouws, Oriol Vinyals, Jakob Uszkoreit, and Lukasz Kaiser. Universal transformers. Arxiv, 2018.',
        '',
        '[^23]: Nadir Durrani, Barry Haddow, Philipp Koehn, and Kenneth Heafield. Edinburgh\'s phrase-based machine translation systems for wmt-14. In Proceedings of the Ninth Workshop on Statistical Machine Translation, pages 97–104, 2014.',
        '',
        '[^24]: Andrew M. Dai and Quoc V. Le. Semi-supervised sequence learning. In Advances in neural information processing systems, 2015.',
        '',
        '[^25]: Marie-Catherine De Marneffe, Mandy Simons, and Judith Tonhauser. The CommitmentBank: Investigating projection in naturally occurring discourse. 2019. To appear in proceedings of Sinn und Bedeutung 23. Data can be found at https://github.com/mcdm/CommitmentBank/.',
        '',
        '[^26]: Yan Duan, John Schulman, Xi Chen, Peter L. Bartlett, Ilya Sutskever, and Pieter Abbeel. Rl <sup>2</sup>: Fast reinforcement learning via slow reinforcement learning. ArXiv, abs/1611.02779, 2016.',
        '',
        '[^27]: Dheeru Dua, Yizhong Wang, Pradeep Dasigi, Gabriel Stanovsky, Sameer Singh, and Matt Gardner. Drop: A reading comprehension benchmark requiring discrete reasoning over paragraphs. arXiv preprint arXiv:1903.00161, 2019.',
        '',
        '[^28]: Zihang Dai, Zhilin Yang, Yiming Yang, Jaime G. Carbonell, Quoc V. Le, and Ruslan Salakhutdinov. Transformer-xl: Attentive language models beyond a fixed-length context. Arxiv, 2019.',
        '',
        '[^29]: Sergey Edunov, Myle Ott, Michael Auli, and David Grangier. Understanding back-translation at scale. arXiv preprint arXiv:1808.09381, 2018.',
        '',
        '[^30]: Chelsea Finn, Pieter Abbeel, and Sergey Levine. Model-agnostic meta-learning for fast adaptation of deep networks. ArXiv, abs/1703.03400, 2017.',
        '',
        '[^31]: Yaroslav Fyodorov. A natural logic inference system, 2000.',
        '',
        '[^32]: Hila Gonen and Yoav Goldberg. Lipstick on a pig: Debiasing methods cover up systematic gender biases in word embeddings but do not remove them. arXiv preprint arXiv:1903.03862, 2019.',
        '',
        '[^33]: Kelvin Guu, Kenton Lee, Zora Tung, Panupong Pasupat, and Ming-Wei Chang. Realm: Retrieval-augmented language model pre-training. arXiv preprint arXiv:2002.08909, 2020.',
        '',
        '[^34]: Danilo Giampiccolo, Bernardo Magnini, Ido Dagan, and Bill Dolan. The third PASCAL recognizing textual entailment challenge. In Proceedings of the ACL-PASCAL workshop on textual entailment and paraphrasing, pages 1–9. Association for Computational Linguistics, 2007.',
        '',
        '[^35]: Alex Graves. Adaptive computation time for recurrent neural networks. Arxiv, 2016.',
        '',
        '[^36]: Suchin Gururangan, Swabha Swayamdipta, Omer Levy, Roy Schwartz, Samuel R Bowman, and Noah A Smith. Annotation artifacts in natural language inference data. arXiv preprint arXiv:1803.02324, 2018.',
        '',
        '[^37]: Sebastian Gehrmann, Hendrik Strobelt, and Alexander M. Rush. Gltr: Statistical detection and visualization of generated text. arXiv preprint arXiv: 1906.04043, 2019.',
        '',
        '[^38]: Jiatao Gu, Yong Wang, Yun Chen, Kyunghyun Cho, and Victor OK Li. Meta-learning for low-resource neural machine translation. arXiv preprint arXiv:1808.08437, 2018.',
        '',
        '[^39]: Daniel Hernandez and Tom Brown. Ai and efficiency, May 2020.',
        '',
        '[^40]: Ari Holtzman, Jan Buys, Maxwell Forbes, and Yejin Choi. The curious case of neural text degeneration. CoRR, abs/1904.09751, 2019.',
        '',
        '[^41]: Dan Hendrycks, Xiaoyuan Liu, Eric Wallace, Adam Dziedzic, Rishabh Krishnan, and Dawn Song. Pretrained transformers improve out of distribution robustness. arXiv preprint arXiv:2004.06100, 2020.',
        '',
        '[^42]: Joel Hestness, Sharan Narang, Newsha Ardalani, Gregory Diamos, Heewoo Jun, Hassan Kianinejad, Md. Mostofa Ali Patwary, Yang Yang, and Yanqi Zhou. Deep learning scaling is predictable, empirically. arXiv preprint arXiv:1712.00409, 2017.',
        '',
        '[^43]: Jeremy Howard and Sebastian Ruder. Universal language model fine-tuning for text classification. arXiv preprint arXiv:1801.06146, 2018.',
        '',
        '[^44]: Geoffrey Hinton, Oriol Vinyals, and Jeff Dean. Distilling the knowledge in a neural network. arXiv preprint arXiv:1503.02531, 2015.',
        '',
        '[^45]: Sepp Hochreiter, A Steven Younger, and Peter R Conwell. Learning to Learn Using Gradient Descent. In International Conference on Artificial Neural Networks, pages 87–94. Springer, 2001.',
        '',
        '[^46]: Po-Sen Huang, Huan Zhang, Ray Jiang, Robert Stanforth, Johannes Welbl, Jack Rae, Vishal Maini, Dani Yogatama, and Pushmeet Kohli. Reducing sentiment bias in language models via counterfactual evaluation. arXiv preprint arXiv:1911.03064, 2019.',
        '',
        '[^47]: Mohit Iyyer, Jordan Boyd-Graber, Leonardo Claudino, Richard Socher, and Hal Daumé III. A neural network for factoid question answering over paragraphs. In Empirical Methods in Natural Language Processing, 2014.',
        '',
        '[^48]: Daphne Ippolito, Daniel Duckworth, Chris Callison-Burch, and Douglas Eck. Automatic detection of generated text is easiest when humans are fooled. arXiv preprint arXiv:1911.00650, 2019.',
        '',
        '[^49]: Mandar Joshi, Eunsol Choi, Daniel S. Weld, and Luke Zettlemoyer. TriviaQA: A large scale distantly supervised challenge dataset for reading comprehension. arXiv preprint arXiv:1705.03551, 2017.',
        '',
        '[^50]: Zheng Junyuan and Gamma Lab NYC. Numeric transformer - albert, March 2020.',
        '',
        '[^51]: Rafal Jozefowicz, Oriol Vinyals, Mike Schuster, Noam Shazeer, and Yonghui Wu. Exploring the limits of language modeling. arXiv preprint arXiv:1602.02410, 2016.',
        '',
        '[^52]: Xiaoqi Jiao, Yichun Yin, Lifeng Shang, Xin Jiang, Xiao Chen, Linlin Li, Fang Wang, and Qun Liu. TinyBERT: Distilling BERT for natural language understanding. arXiv preprint arXiv:1909.10351, 2019.',
        '',
        '[^53]: Ying Ju, Fubang Zhao, Shijie Chen, Bowen Zheng, Xuefeng Yang, and Yunfeng Liu. Technical report on conversational question answering. arXiv preprint arXiv:1909.10772, 2019.',
        '',
        '[^54]: Daniel Khashabi, Snigdha Chaturvedi, Michael Roth, Shyam Upadhyay, and Dan Roth. Looking beyond the surface: A challenge set for reading comprehension over multiple sentences. In Proceedings of North American Chapter of the Association for Computational Linguistics (NAACL), 2018.',
        '',
        '[^55]: Daniel Khashabi, Tushar Khot, Ashish Sabharwal, Oyvind Tafjord, Peter Clark, and Hannaneh Hajishirzi. Unifiedqa: Crossing format boundaries with a single qa system. arXiv preprint arXiv:2005.00700, 2020.',
        '',
        '[^56]: Sarah E. Kreps, Miles McCain, and Miles Brundage. All the news that\'s fit to fabricate: Ai-generated text as a tool of media misinformation, 2020.',
        '',
        '[^57]: Jared Kaplan, Sam McCandlish, Tom Henighan, Tom B. Brown, Benjamin Chess, Rewon Child, Scott Gray, Alec Radford, Jeffrey Wu, and Dario Amodei. Scaling laws for neural language models, 2020.',
        '',
        '[^58]: Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield, Michael Collins, Ankur Parikh, Chris Alberti, Danielle Epstein, Illia Polosukhin, Matthew Kelcey, Jacob Devlin, Kenton Lee, Kristina N. Toutanova, Llion Jones, Ming-Wei Chang, Andrew Dai, Jakob Uszkoreit, Quoc Le, and Slav Petrov. Natural questions: a benchmark for question answering research. Transactions of the Association of Computational Linguistics, 2019.',
        '',
        '[^59]: Yoon Kim and Alexander M. Rush. Sequence-level knowledge distillation. Arxiv, 2016.',
        '',
        '[^60]: Edward Loper and Steven Bird. Nltk: The natural language toolkit, 2002.',
        '',
        '[^61]: Guillaume Lample and Alexis Conneau. Cross-lingual language model pretraining. arXiv preprint arXiv:1901.07291, 2019.',
        '',
        '[^62]: Zhenzhong Lan, Mingda Chen, Sebastian Goodman, Kevin Gimpel, Piyush Sharma, and Radu Soricut. ALBERT: A lite BERT for self-supervised learning of language representations. arXiv preprint arXiv:1909.11942, 2019.',
        '',
        '[^63]: Xiaodong Liu, Hao Cheng, Pengcheng He, Weizhu Chen, Yu Wang, Hoifung Poon, and Jianfeng Gao. Adversarial training for large neural language models. arXiv preprint arXiv:2004.08994, 2020.',
        '',
        '[^64]: Zhongyang Li, Xiao Ding, and Ting Liu. Story ending prediction by transferable bert. arXiv preprint arXiv:1905.07504, 2019.',
        '',
        '[^65]: Hector Levesque, Ernest Davis, and Leora Morgenstern. The Winograd schema challenge. In Thirteenth International Conference on the Principles of Knowledge Representation and Reasoning, 2012.',
        '',
        '[^66]: Yinhan Liu, Jiatao Gu, Naman Goyal, Xian Li, Sergey Edunov, Marjan Ghazvininejad, Mike Lewis, and Luke Zettlemoyer. Multilingual denoising pre-training for neural machine translation. arXiv preprint arXiv:2001.08210, 2020.',
        '',
        '[^67]: Xiaodong Liu, Jianfeng Gao, Xiaodong He, Li Deng, Kevin Duh, and Ye-Yi Wang. Representation learning using multi-task deep neural networks for semantic classification and information retrieval. In Proceedings of the 2015 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, 2015.',
        '',
        '[^68]: Ilya Loshchilov and Frank Hutter. Decoupled weight decay regularization. arXiv preprint arXiv:1711.05101, 2017.',
        '',
        '[^69]: Xiaodong Liu, Pengcheng He, Weizhu Chen, and Jianfeng Gao. Improving multi-task deep neural networks via knowledge distillation for natural language understanding. arXiv preprint arXiv:1904.09482, 2019.',
        '',
        '[^70]: Xiaodong Liu, Pengcheng He, Weizhu Chen, and Jianfeng Gao. Multi-task deep neural networks for natural language understanding. arXiv preprint arXiv:1901.11504, 2019.',
        '',
        '[^71]: Tal Linzen. How can we accelerate progress towards human-like linguistic generalization? arXiv preprint arXiv:2005.00955, 2020.',
        '',
        '[^72]: Mike Lewis, Yinhan Liu, Naman Goyal, Marjan Ghazvininejad, Abdelrahman Mohamed, Omer Levy, Ves Stoyanov, and Luke Zettlemoyer. Bart: Denoising sequence-to-sequence pre-training for natural language generation, translation, and comprehension. arXiv preprint arXiv:1910.13461, 2019.',
        '',
        '[^73]: Ke Li and Jitendra Malik. Learning to optimize neural nets. arXiv preprint arXiv:1703.00441, 2017.',
        '',
        '[^74]: Yinhan Liu, Myle Ott, Naman Goyal, Jingfei Du, Mandar Joshi, Danqi Chen, Omer Levy, Mike Lewis, Luke Zettlemoyer, and Veselin Stoyanov. RoBERTa: A robustly optimized BERT pretraining approach. arXiv preprint arXiv:1907.11692, 2019.',
        '',
        '[^75]: Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Kiela Douwe. Retrieval-augmented generation for knowledge-intensive nlp tasks. arXiv preprint arXiv:2005.11401, 2020.',
        '',
        '[^76]: Peter J. Liu, Mohammad Saleh, Etienne Pot, Ben Goodrich, Ryan Sepassi, Lukasz Kaiser, and Noam Shazeer. Generating Wikipedia by summarizing long sequences. arXiv preprint arXiv:1801.10198, 2018.',
        '',
        '[^77]: Zhuohan Li, Eric Wallace, Sheng Shen, Kevin Lin, Kurt Keutzer, Dan Klein, and Joseph E. Gonzalez. Train large, then compress: Rethinking model size for efficient training and inference of transformers, 2020.',
        '',
        '[^78]: Guokun Lai, Qizhe Xie, Hanxiao Liu, Yiming Yang, and Eduard Hovy. Race: Large-scale reading comprehension dataset from examinations. arXiv preprint arXiv:1704.04683, 2017.',
        '',
        '[^79]: Sheng-Chieh Lin, Jheng-Hong Yang, Rodrigo Nogueira, Ming-Feng Tsai, Chuan-Ju Wang, and Jimmy Lin. Tttttackling winogrande schemas. arXiv preprint arXiv:2003.08380, 2020.',
        '',
        '[^80]: David. MacKay. Information-based objective functions for active data selection. Neural Computation, 1992.',
        '',
        '[^81]: Bryan McCann, James Bradbury, Caiming Xiong, and Richard Socher. Learned in translation: Contextualized word vectors. In Advances in Neural Information Processing Systems, pages 6294–6305, 2017.',
        '',
        '[^82]: Tomas Mikolov, Kai Chen, Greg Corrado, and Jeffrey Dean. Efficient estimation of word representations in vector space. arXiv preprint arXiv:1301.3781, 2013.',
        '',
        '[^83]: Nasrin Mostafazadeh, Nathanael Chambers, Xiaodong He, Devi Parikh, Dhruv Batra, Lucy Vanderwende, Pushmeet Kohli, and James Allen. A corpus and evaluation framework for deeper understanding of commonsense stories. arXiv preprint arXiv:1604.01696, 2016.',
        '',
        '[^84]: Todor Mihaylov, Peter Clark, Tushar Khot, and Ashish Sabharwal. Can a suit of armor conduct electricity? a new dataset for open book question answering. ArXiv, abs/1809.02789, 2018.',
        '',
        '[^85]: Sam McCandlish, Jared Kaplan, Dario Amodei, and OpenAI Dota Team. An empirical model of large-batch training, 2018.',
        '',
        '[^86]: Mitchell Marcus, Grace Kim, Mary Ann Marcinkiewicz, Robert MacIntyre, Ann Bies, Mark Ferguson, Karen Katz, and Britta Schasberger. The penn treebank: annotating predicate argument structure. In Proceedings of the workshop on Human Language Technology, pages 114–119. Association for Computational Linguistics, 1994.',
        '',
        '[^87]: Bryan McCann, Nitish Shirish Keskar, Caiming Xiong, and Richard Socher. The natural language decathlon: Multitask learning as question answering. arXiv preprint arXiv:1806.08730, 2018.',
        '',
        '[^88]: R Thomas McCoy, Ellie Pavlick, and Tal Linzen. Right for the wrong reasons: Diagnosing syntactic heuristics in natural language inference. arXiv preprint arXiv:1902.01007, 2019.',
        '',
        '[^89]: Margaret Mitchell, Simone Wu, Andrew Zaldivar, Parker Barnes, Lucy Vasserman, Ben Hutchinson, Elena Spitzer, Inioluwa Deborah Raji, and Timnit Gebru. Model cards for model reporting, 2018.',
        '',
        '[^90]: Moin Nadeem, Anna Bethke, and Siva Reddy. Stereoset: Measuring stereotypical bias in pretrained language models. arXiv preprint arXiv:2004.09456, 2020.',
        '',
        '[^91]: Timothy Niven and Hung-Yu Kao. Probing neural network comprehension of natural language arguments. arXiv preprint arXiv:1907.07355, 2019.',
        '',
        '[^92]: Peter Norvig. Natural language corpus data, 2009.',
        '',
        '[^93]: Malvina Nissim, Rik van Noord, and Rob van der Goot. Fair is better than sensational: Man is to doctor as woman is to doctor. arXiv preprint arXiv:1905.09866, 2019.',
        '',
        '[^94]: Yixin Nie, Adina Williams, Emily Dinan, Mohit Bansal, Jason Weston, and Douwe Kiela. Adversarial nli: A new benchmark for natural language understanding. arXiv preprint arXiv:1910.14599, 2019.',
        '',
        '[^95]: University of Regensburg. Fascha, 2016.',
        '',
        '[^96]: Mohammad Taher Pilehvar and Jose Camacho-Collados. WIC: 10,000 example pairs for evaluating context-sensitive representations. arXiv preprint arXiv:1808.09121, 2018.',
        '',
        '[^97]: Jason Phang, Thibault Févry, and Samuel R. Bowman. Sentence encoders on STILTs: Supplementary training on intermediate labeled-data tasks. arXiv preprint arXiv:1811.01088, 2018.',
        '',
        '[^98]: Adam Poliak, Aparajita Haldar, Rachel Rudinger, J. Edward Hu, Ellie Pavlick, Aaron Steven White, and Benjamin Van Durme. Collecting diverse natural language inference problems for sentence representation evaluation. In Proceedings of EMNLP, 2018.',
        '',
        '[^99]: Denis Paperno, Germán Kruszewski, Angeliki Lazaridou, Quan Ngoc Pham, Raffaella Bernardi, Sandro Pezzelle, Marco Baroni, Gemma Boleda, and Raquel Fernández. The lambada dataset: Word prediction requiring a broad discourse context. arXiv preprint arXiv:1606.06031, 2016.',
        '',
        '[^100]: Matthew E. Peters, Mark Neumann, Luke Zettlemoyer, and Wen tau Yih. Dissecting contextual word embeddings: Architecture and representation, 2018.',
        '',
        '[^101]: Matt Post. A call for clarity in reporting BLEU scores. arXiv preprint arXiv:1804.08771, 2018.',
        '',
        '[^102]: Jeffrey Pennington, Richard Socher, and Christopher Manning. GloVe: Global vectors for word representation. In Proceedings of the 2014 conference on empirical methods in natural language processing (EMNLP), 2014.',
        '',
        '[^103]: QIANXIN. Sa-net on albert (ensemble), April 2020.',
        '',
        '[^104]: Yusu Qian, Urwa Muaz, Ben Zhang, and Jae Won Hyun. Reducing gender bias in word-level language models with a gender-equalizing loss function. arXiv preprint arXiv:1905.12801, 2019.',
        '',
        '[^105]: Melissa Roemmele, Cosmin Adrian Bejan, and Andrew S Gordon. Choice of plausible alternatives: An evaluation of commonsense causal reasoning. In 2011 AAAI Spring Symposium Series, 2011.',
        '',
        '[^106]: Siva Reddy, Danqi Chen, and Christopher D Manning. Coqa: A conversational question answering challenge. Transactions of the Association for Computational Linguistics, 7:249–266, 2019.',
        '',
        '[^107]: Scott Reed, Yutian Chen, Thomas Paine, Aäron van den Oord, SM Eslami, Danilo Rezende, Oriol Vinyals, and Nando de Freitas. Few-shot autoregressive density estimation: Towards learning to learn distributions. arXiv preprint arXiv:1710.10304, 2017.',
        '',
        '[^108]: Pranav Rajpurkar, Robin Jia, and Percy Liang. Know what you don\'t know: Unanswerable questions for squad. arXiv preprint arXiv:1806.03822, 2018.',
        '',
        '[^109]: Sachin Ravi and Hugo Larochelle. Optimization as a model for few-shot learning. ICLR 2017 (oral), 2016.',
        '',
        '[^110]: Qiu Ran, Yankai Lin, Peng Li, Jie Zhou, and Zhiyuan Liu. NumNet: Machine reading comprehension with numerical reasoning. In Proceedings of EMNLP, 2019.',
        '',
        '[^111]: Rachel Rudinger, Jason Naradowsky, Brian Leonard, and Benjamin Van Durme. Gender bias in coreference resolution. arXiv preprint arXiv:1804.09301, 2018.',
        '',
        '[^112]: Alec Radford, Karthik Narasimhan, Tim Salimans, and Ilya Sutskever. Improving language understanding by generative pre-training, 2018.',
        '',
        '[^113]: R.S. Ross. Guide for conducting risk assessments. NIST Special Publication, 2012.',
        '',
        '[^114]: Jonathan S. Rosenfeld, Amir Rosenfeld, Yonatan Belinkov, and Nir Shavit. A constructive prediction of the generalization error across scales, 2019.',
        '',
        '[^115]: Adam Roberts, Colin Raffel, and Noam Shazeer. How much knowledge can you pack into the parameters of a language model? arXiv preprint arXiv:2002.08910, 2020.',
        '',
        '[^116]: Colin Raffel, Noam Shazeer, Adam Roberts, Katherine Lee, Sharan Narang, Michael Matena, Yanqi Zhou, Wei Li, and Peter J. Liu. Exploring the limits of transfer learning with a unified text-to-text transformer, 2019.',
        '',
        '[^117]: Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, and Ilya Sutskever. Language models are unsupervised multitask learners, 2019.',
        '',
        '[^118]: Keisuke Sakaguchi, Ronan Le Bras, Chandra Bhagavatula, and Yejin Choi. Winogrande: An adversarial winograd schema challenge at scale, 2019.',
        '',
        '[^119]: Irene Solaiman, Miles Brundage, Jack Clark, Amanda Askell, Ariel Herbert-Voss, Jeff Wu, Alec Radford, Gretchen Krueger, Jong Wook Kim, Sarah Kreps, Miles McCain, Alex Newhouse, Jason Blazakis, Kris McGuffie, and Jasmine Wang. Release strategies and the social impacts of language models, 2019.',
        '',
        '[^120]: Emily Sheng, Kai-Wei Chang, Premkumar Natarajan, and Nanyun Peng. The woman worked as a babysitter: On biases in language generation. arXiv preprint arXiv:1909.01326, 2019.',
        '',
        '[^121]: Victor Sanh, Lysandre Debut, Julien Chaumond, and Thomas Wolf. DistilBERT, a distilled version of BERT: smaller, faster, cheaper and lighter. arXiv preprint arXiv:1910.01108, 2019.',
        '',
        '[^122]: Roy Schwartz, Jesse Dodge, Noah A. Smith, and Oren Etzioni. Green AI. CoRR, abs/1907.10597, 2019.',
        '',
        '[^123]: Rico Sennrich, Barry Haddow, and Alexandra Birch. Improving neural machine translation models with monolingual data. arXiv preprint arXiv:1511.06709, 2015.',
        '',
        '[^124]: Noam Shazeer, Azalia Mirhoseini, Krzysztof Maziarz, Andy Davis, Quoc Le, Geoffrey Hinton, and Jeff Dean. Outrageously large neural networks: The sparsely-gated mixture-of-experts layer. arXiv preprint arXiv:1701.06538, 2017.',
        '',
        '[^125]: Mohammad Shoeybi, Mostofa Patwary, Raul Puri, Patrick LeGresley, Jared Casper, and Bryan Catanzaro. Megatron-lm: Training multi-billion parameter language models using model parallelism, 2019.',
        '',
        '[^126]: Timo Schick and Hinrich Schütze. Exploiting cloze questions for few-shot text classification and natural language inference. arXiv preprint arXiv:2001.07676, 2020.',
        '',
        '[^127]: Kaitao Song, Xu Tan, Tao Qin, Jianfeng Lu, and Tie-Yan Liu. MASS: Masked sequence to sequence pre-training for language generation. arXiv preprint arXiv:1905.02450, 2019.',
        '',
        '[^128]: Josh Tobin, Rachel Fong, Alex Ray, Jonas Schneider, Wojciech Zaremba, and Pieter Abbeel. Domain randomization for transferring deep neural networks from simulation to the real world. In 2017 IEEE/RSJ international conference on intelligent robots and systems (IROS), pages 23–30. IEEE, 2017.',
        '',
        '[^129]: Peter D. Turney and Michael L. Littman. Corpus-based learning of analogies and semantic relations. CoRR, abs/cs/0508103, 2005.',
        '',
        '[^130]: Trieu H. Trinh and Quoc V. Le. A simple method for commonsense reasoning. arXiv preprint arXiv:1806.02847, 2018.',
        '',
        '[^131]: Peter D. Turney, Michael L. Littman, Jeffrey Bigham, and Victor Shnayder. Combining independent modules to solve multiple-choice synonym and analogy problems. CoRR, cs.CL/0309035, 2003.',
        '',
        '[^132]: Project Turing. Microsoft research blog, Feb 2020.',
        '',
        '[^133]: Oriol Vinyals, Charles Blundell, Timothy Lillicrap, Daan Wierstra, et al. Matching Networks for One Shot Learning. In Advances in neural information processing systems, pages 3630–3638, 2016.',
        '',
        '[^134]: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is all you need. In Advances in neural information processing systems, 2017.',
        '',
        '[^135]: Alex Wang, Yada Pruksachatkun, Nikita Nangia, Amanpreet Singh, Julian Michael, Felix Hill, Omer Levy, and Samuel Bowman. Superglue: A stickier benchmark for general-purpose language understanding systems. In Advances in Neural Information Processing Systems, pages 3261–3275, 2019.',
        '',
        '[^136]: Yiren Wang, Yingce Xia, Tianyu He, Fei Tian, Tao Qin, ChengXiang Zhai, and Tie-Yan Liu. Multi-agent dual learning. ICLR 2019, 2018.',
        '',
        '[^137]: Qizhe Xie, Zihang Dai, Eduard Hovy, Minh-Thang Luong, and Quoc V. Le. Unsupervised data augmentation for consistency training, 2019.',
        '',
        '[^138]: Dani Yogatama, Cyprien de Masson d\'Autume, Jerome Connor, Tomas Kocisky, Mike Chrzanowski, Lingpeng Kong, Angeliki Lazaridou, Wang Ling, Lei Yu, Chris Dyer, et al. Learning and evaluating general linguistic intelligence. arXiv preprint arXiv:1901.11373, 2019.',
        '',
        '[^139]: Zhilin Yang, Zihang Dai, Yiming Yang, Jaime Carbonell, Ruslan Salakhutdinov, and Quoc V. Le. XLNet: Generalized autoregressive pretraining for language understanding. arXiv preprint arXiv:1906.08237, 2019.',
        '',
        '[^140]: Rowan Zellers, Ari Holtzman, Yonatan Bisk, Ali Farhadi, and Yejin Choi. Hellaswag: Can a machine really finish your sentence? arXiv preprint arXiv:1905.07830, 2019.',
        '',
        '[^141]: Rowan Zellers, Ari Holtzman, Hannah Rashkin, Yonatan Bisk, Ali Farhadi, Franziska Roesner, and Yejin Choi. Defending against neural fake news. arXiv preprint arXiv:1905.12616, 2019.',
        '',
        '[^142]: Sheng Zhang, Xiaodong Liu, Jingjing Liu, Jianfeng Gao, Kevin Duh, and Benjamin Van Durme. ReCoRD: Bridging the gap between human and machine commonsense reading comprehension. arXiv preprint arXiv:1810.12885, 2018.',
        '',
        '[^143]: Daniel M. Ziegler, Nisan Stiennon, Jeffrey Wu, Tom B. Brown, Alec Radford, Dario Amodei, Paul Christiano, and Geoffrey Irving. Fine-tuning language models from human preferences, 2019.',
        '',
        '[^144]: Stuart Russell and Peter Norvig. Artificial Intelligence: A Modern Approach. Prentice Hall, 3 edition, 2009.',
    ]
    
    lines.extend(refs)
    
    # Write the file
    content = '\n'.join(lines)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Translation written to: {out_path}")
    print(f"Total characters: {len(content)}")

if __name__ == '__main__':
    main()
