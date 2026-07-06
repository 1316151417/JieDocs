
## 1. 基本定位

- **全文检索**：对整篇文本建立索引，并支持按词、短语、字段等方式检索。ES 这类搜索引擎的核心能力通常就是全文检索 。[[cloud.google](https://cloud.google.com/discover/what-is-full-text-search?hl=zh-CN)]
    
- **关键词检索**：按查询词在文本中找匹配内容，通常依赖倒排索引来实现 。[[herefreelucky](http://www.herefreelucky.com/index.php/archives/522/)]
    
- **稀疏检索**：一种基于稀疏词项表示的检索范式，BM25、TF-IDF 都属于这一类的典型方法 。[[elastic](https://www.elastic.co/blog/found-similarity-in-elasticsearch)]
    
- **向量检索**：通常指 dense embedding 检索，不是 BM25 这一路；它更偏语义匹配 。[[blog.csdn](https://blog.csdn.net/2501_93903170/article/details/153832733)]
    

## 2. ES 的检索流程

- ES 的典型流程是：**分词 → 建倒排索引 → 查询命中 term → 用相关性算法打分排序** 。[[comate.baidu](https://comate.baidu.com/zh/page/6xdddrbq5tm)]
    
- 这里的核心不是“把文本变成语义向量”，而是把词项映射到文档列表，再根据词项统计关系计算分数 。[[herefreelucky](http://www.herefreelucky.com/index.php/archives/522/)]
    
- 因此，ES 更准确地说是“全文检索引擎”，而 BM25 是它默认使用的相关性评分方法之一 。[[elastic](https://www.elastic.co/cn/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)]
    

## 3. BM25 是什么

- BM25 是一种用于**文档与查询相关性排序**的经典算法 。[[fjdu.github](http://fjdu.github.io/coding/2017/03/16/bm25-elasticsearch-lucene.html)]
    
- 它会综合考虑：
    
    - 词在文档中出现了多少次；
        
    - 词在整个语料中有多稀有；
        
    - 文档长度是否过长 。[[elastic](https://www.elastic.co/cn/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)]
        
- ES 默认的相似度/排序算法就是 BM25 。[[ibm](https://www.ibm.com/docs/en/content-cortex/5.7.0?topic=domain-document-retrieval-ranking)]
    

## 4. BM25 的核心特点

- **词频饱和**：同一个词出现很多次，分数不会无限线性增长，而是逐渐饱和 。[[adg.csdn](https://adg.csdn.net/696f50ab437a6b40336a0038.html)]
    
- **文档长度归一化**：长文档不会天然占优，系统会对文档长度做修正 。[[ibm](https://www.ibm.com/docs/en/content-cortex/5.7.0?topic=domain-document-retrieval-ranking)]
    
- **可调参数**：常见参数有 k1k_1k1​ 和 bbb，用来控制词频饱和程度和长度惩罚强度 。[[fjdu.github](http://fjdu.github.io/coding/2017/03/16/bm25-elasticsearch-lucene.html)]
    
- **工程实用性强**：在真实搜索场景中通常比经典 TF-IDF 更稳定 。[[adg.csdn](https://adg.csdn.net/696f50ab437a6b40336a0038.html)]
    

## 5. TF-IDF 是什么

- TF-IDF 是衡量一个词在某篇文档里重要性的统计方法 。[[alibabacloud](https://www.alibabacloud.com/help/tc/pai/user-guide/tf-idf)]
    
- 它由两部分组成：
    
    - **TF**：词频，词在当前文档里出现得多不多 。[[help.aliyun](https://help.aliyun.com/zh/pai/user-guide/tf-idf)]
        
    - **IDF**：逆文档频率，词在整个语料里稀不稀有 。[[alibabacloud](https://www.alibabacloud.com/help/tc/pai/user-guide/tf-idf)]
        
- 常见理解就是：**TF-IDF = TF × IDF** 。[[blog.csdn](https://blog.csdn.net/asialee_bird/article/details/81486700)]
    

## 6. BM25 相比 TF-IDF 的改进

- **TF-IDF** 往往把词频看成近似线性增长，词出现越多分数越高 。[[blog.csdn](https://blog.csdn.net/keeppractice/article/details/150564008)]
    
- **BM25** 把词频改成“逐渐饱和”的非线性形式，避免高频词无限拉高分数 。[[ibm](https://www.ibm.com/docs/en/content-cortex/5.7.0?topic=domain-document-retrieval-ranking)]
    
- **TF-IDF** 对长文档可能更有偏置，因为长文档更容易包含更多词 。[[kmwllc](https://kmwllc.com/index.php/2020/03/20/understanding-tf-idf-and-bm-25/)]
    
- **BM25** 加入了长度归一化，减少长文档天然占便宜的问题 。[[adg.csdn](https://adg.csdn.net/696f50ab437a6b40336a0038.html)]
    

## 7. 分词的重要性

- BM25 本身不负责分词，它只处理已经切好的词项 。[[learn.microsoft](https://learn.microsoft.com/zh-cn/azure/search/index-similarity-and-scoring)]
    
- 英文通常基于空格、标点、词形规则做分词；中文通常需要额外的中文分词器 。[[cloud.tencent](https://cloud.tencent.com/developer/article/2536406)]
    
- 所以，分词质量会直接影响 BM25 和 ES 的检索效果 。[[learn.microsoft](https://learn.microsoft.com/zh-cn/azure/search/index-similarity-and-scoring)]
    

## 8. 关键词检索、稀疏检索、全文检索的关系

- **全文检索** 是更大的系统能力，ES 就属于这类引擎 。[[cloud.google](https://cloud.google.com/discover/what-is-full-text-search?hl=zh-CN)]
    
- **关键词检索** 是其中一种常见检索方式，通常依赖倒排索引实现 。[[zilliz.com](https://zilliz.com.cn/faq/how-does-fulltext-search-differ-from-keyword-search)]
    
- **稀疏检索** 是更抽象的表示方式，BM25、TF-IDF 这类词项权重方法都可归入其中 。[[cloud.tencent](https://cloud.tencent.com/document/product/1709/110110)]
    
- **BM25 不是 dense embedding 的向量检索**，它是基于词项统计和倒排索引的稀疏检索方法 。[[blog.csdn](https://blog.csdn.net/2501_93903170/article/details/153832733)]
    

## 9. 一句话总结

- **ES**：全文检索引擎，核心机制是分词和倒排索引 。[[comate.baidu](https://comate.baidu.com/zh/page/6xdddrbq5tm)]
    
- **BM25**：ES 默认的相关性评分算法，属于稀疏检索范畴 。[[elastic](https://www.elastic.co/cn/blog/practical-bm25-part-2-the-bm25-algorithm-and-its-variables)]
    
- **TF-IDF**：更早期的词权重统计方法，是 BM25 的重要前身 。[[alibabacloud](https://www.alibabacloud.com/help/tc/pai/user-guide/tf-idf)]
    
- **中文检索**：关键在分词；分词做不好，BM25 再强也会受影响 。[[cloud.tencent](https://cloud.tencent.com/developer/article/2536406)]
    

## 10. 最后纠正一个容易混淆的点

- 你之前的理解是对的：**ES 不是把文本编码成语义向量再检索**，而是建立倒排索引后用 BM25 这类算法算相关性 。[[herefreelucky](http://www.herefreelucky.com/index.php/archives/522/)]
    
- “稀疏检索”在这里更接近“基于词项的稀疏表示检索”，不是 dense vector 检索 。[[cloud.tencent](https://cloud.tencent.com/document/product/1709/110110)]