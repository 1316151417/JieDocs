# **AI-Native 认知层基础设施（LLM Wiki）技术设计方案**

---
# **1. 项目背景**
![[Pasted image 20260525233718.png]]

## **1.1 背景问题**

当前企业研发体系中，长期存在以下问题：

### **1）企业知识无法沉淀**

系统长期演进过程中：

- 文档质量低
- 文档长期过期
- 历史设计无人维护
- 新人理解系统困难
- 核心知识沉淀在人脑中

知识散落在：

- 代码
- SQL
- PR
- 飞书
- Confluence
- 日志
- 排查手册
- 历史事故
- 核心研发经验

最终形成：

```text
代码是真相
文档是解释
人脑是补丁
```

---
## **1.2 当前 AI 工程实践的核心问题**

目前多数 AI 工程方案：

```text
向量库 + ChatBot
```

但实际效果有限。

原因在于：

AI 并不真正理解企业系统。

典型问题：

- 无法理解调用链
- 无法理解模块边界
- 无法理解状态流
- 无法形成长期系统认知
- 无法高效理解老系统

因此：

当前 AI 最大瓶颈不是"生成能力"。

而是：

# **缺少系统级认知能力**

---
# **1.3 本项目目标**

本项目并非传统知识库。

也不是：

```text
ChatGPT + 企业文档
```

而是：

# **构建 AI-Native 系统认知基础设施**

核心目标：

以代码为核心，以外部知识为辅助，形成长期演化的企业知识系统。

最终实现：

- 系统知识可沉淀
- 系统知识可增量更新
- AI 能理解系统
- 人能快速理解系统
- 支撑 AI 进入研发全流程

---
# **1.4 与 OKR 的关系**

本项目属于：

# **AI-Native 研发效能建设的基础设施能力**

支撑方向：

- 业务理解
- 需求设计
- 代码开发
- CR
- 测试
- 故障排查
- 系统演进理解

核心价值：

# **为 AI 提供"系统理解能力"**

---
# **2. 核心设计思想**

---
# **2.1 代码是核心知识源**

核心原则：

# **Code First**

原因：

代码具备天然真实性。

```text
代码改了 = 系统行为改变
```

而文档：

```text
文档改不改
不影响系统运行
```

因此：

|**类型**|**特点**|
|---|---|
|代码|强一致、可解析、可增量更新|
|文档|主观、易过期、质量不稳定|

所以：

# **代码是系统现实（System Reality）**

# **文档是人类解释（Human Explanation）**

---
# **2.2 本系统不是文档系统**

本系统本质是：

# **Knowledge Compiler（知识编译器）**

类似：

```text
源码
 ↓
编译
 ↓
IR（中间表示）
 ↓
最终产物
```

在本系统中：

|**编译概念**|**对应内容**|
|---|---|
|Source|代码 / SQL / 文档|
|Parse|AST / CodeGraph|
|Semantic Layer|系统语义|
|Output|Wiki / Agent Context|

---
# **2.3 Wiki 只是知识视图**

本项目核心不是：

```text
生成 Markdown
```

而是：

# **建立系统认知结构**

最终：

```text
代码
 ↓
语义结构层
 ↓
Wiki / Agent / 搜索
```

其中：

Wiki 只是：

# **人类可视化视图**

---
# **3. 建设目标**

---
# **3.1 第一阶段目标（V1）**

聚焦：

# **"AI 能否稳定理解系统"**

而不是：

- GraphRAG
- AI 搜索平台
- 知识图谱平台

V1 核心目标：

- 基于代码生成高质量 Wiki
- 建立系统认知结构
- 支持增量更新
- 支持 Agent 探索
- 提升老系统理解效率

---
# **3.2 V1 不做的事情**

明确不做：

- GraphRAG
- Runtime 全链路分析
- 复杂知识图谱
- Neo4j
- 多 Agent 协同
- 大规模在线平台化

原因：

当前核心目标仍然是：

# **验证 AI 系统理解能力**

---
# **4. 总体架构设计**

---
# **4.1 架构原则**

采用：

# **Local-first + Remote Enhancement**

架构思想。

原因：

代码分析天然依赖本地环境：

- monorepo
- gradle
- node_modules
- annotation processor
- protobuf
- IDE index

不适合完全中心化。

---
# **4.2 总体架构**

```text
Local Repo
    ↓
AST Parse
    ↓
CodeGraph
    ↓
Semantic Overlay
    ↓
React Agent Exploration
    ↓
Markdown Wiki Generation
    ↓
Git Persist
```

远程服务仅负责：

```text
LLM Gateway
MCP能力
Webhook
飞书API
统一权限
```

---
# **5. 核心模块设计**

---
# **5.1 Code Parse Layer**

## **职责**

负责：

# **将代码从文本变成结构**

输出：

- AST
- Symbol
- Import
- Annotation
- SQL 引用
- 配置引用

---
## **目标**

解决：

# **Agent 无法高效理解代码**

没有 Parse：

Agent 只能：

```text
grep + 猜
```

---
# **5.2 CodeGraph Layer**

## **本质**

CodeGraph：

不是画图工具。

而是：

# **长期代码关系缓存**

---
## **核心职责**

维护：

- Service → Service
- Service → DB
- Service → MQ
- Service → RPC

---
## **V1 原则**

不自研 Graph Engine。

直接复用现有能力。

例如：

- codegraph
- tree-sitter
- language server

---
## **核心目标**

帮助 Agent：

# **高效导航系统**

而不是重复全仓探索。

---
# **5.3 Semantic Overlay Layer**

这是本系统真正核心。

---
## **为什么需要这一层？**

CodeGraph 只能提供：

```text
结构关系
```

例如：

```text
RefundService → PaymentClient
```

但无法理解：

```text
负责退款主流程
存在幂等风险
```

因此：

需要增加：

# **业务语义层**

---
## **示例**

CodeGraph：

```json
{
  "service": "RefundService",
  "calls": ["PaymentClient"]
}
```

Semantic Overlay：

```json
{
  "service": "RefundService",
  "description": "负责退款主流程",
  "risk": ["幂等"]
}
```

---
## **核心原则**

Semantic Overlay：

# **不侵入 CodeGraph**

避免：

- Fork 三方项目
- 自研编译器
- 后续维护失控

---
# **5.4 Agent Exploration Layer**

---
## **Agent 的角色**

不是：

```text
代码总结器
```

而是：

# **系统分析师**

---
## **核心任务**

建立：

- 系统职责
- 业务边界
- 数据流
- 状态流
- 上下游依赖
- 风险点

---
## **Prompt 核心原则**

错误方式：

```text
请总结代码
```

正确方式：

```text
请建立系统认知
```

---
## **推荐 Prompt 思路**

```text
你是一位资深系统架构师。

你的目标不是逐文件总结代码。

而是理解：

1. 系统职责
2. 业务边界
3. 核心链路
4. 数据流
5. 状态变化
6. 上下游依赖
7. 风险点
8. 历史演进
```

---
# **5.5 Wiki Generation Layer**

---
# **V1 采用 Markdown + Git**

原因：

- 可读
- 可编辑
- Git Friendly
- 天然支持 Diff
- 易增量更新

---
## **推荐技术方案**

- Markdown
- Docusaurus / MkDocs
- Git 持久化

---
## **Wiki 本质**

不是：

```text
README
```

而是：

# **系统认知地图**

---
# **6. 知识分层设计**

---
# **6.1 Code Truth Layer（最高可信）**

来源：

- 代码
- SQL
- API
- 配置
- MQ

特点：

- 自动更新
- 高可信
- 可验证

这是：

# **系统现实层**

---
# **6.2 Human Knowledge Layer**

来源：

- RFC
- 技术方案
- PRD
- 事故复盘
- 排查手册

特点：

- 主观
- 可能过期
- 质量不稳定

因此：

# **不允许覆盖 Code Truth**

只能：

# **作为解释层挂载**

---
# **6.3 Runtime Layer（后续阶段）**

后续逐步接入：

- Trace
- Log
- Metrics
- Incident

形成：

# **系统运行现实**

V1 暂不建设。

---
# **7. Wiki 组织结构设计**

---
# **7.1 不按代码目录组织**

错误方式：

```text
package
module
repo
```

这是代码视角。

---
# **7.2 按业务域组织**

推荐：

```text
订单域
支付域
退款域
分账域
```

因为：

人是按业务理解系统。

---
# **7.3 推荐 Wiki 结构**

每篇 Wiki 推荐包含：

---
## **1. 系统职责**

为什么存在。

---
## **2. 业务边界**

负责什么。

不负责什么。

---
## **3. 核心链路**

例如：

```text
退款申请
 → 风控
 → 支付退款
 → 状态更新
 → MQ通知
```

---
## **4. 数据模型**

包括：

- 核心表
- 生命周期
- 状态

---
## **5. 状态机**

企业系统本质上：

# **是状态机网络**

---
## **6. 外部依赖**

包括：

- RPC
- MQ
- Redis
- DB

---
## **7. 风险点**

例如：

- 幂等
- 一致性
- 补偿
- 延迟

---
## **8. 历史演进**

解释：

```text
为什么现在这样设计
```

---
# **8. 增量更新设计**

---
# **8.1 核心原则**

不全量重建。

采用：

# **Node-based Incremental Update**

---
# **8.2 流程**

```text
Git Diff
   ↓
AST Diff
   ↓
影响分析
   ↓
更新相关 Wiki
```

---
# **8.3 优势**

- 成本低
- 更新快
- 更稳定
- 更适合长期维护

---
# **9. 远程增强能力设计**

远程服务仅负责：

# **企业公共能力**

例如：

|**能力**|**作用**|
|---|---|
|LLM Gateway|统一模型调用|
|MCP|CodeGraph / Tool|
|Feishu API|文档写入|
|Webhook|自动更新|
|Auth|权限控制|

---
# **10. 项目阶段规划**

---
# **Phase 1：系统认知验证**

目标：

- 基于代码生成高质量 Wiki
- 建立核心业务域认知
- 跑通增量更新

---
# **Phase 2：知识结构增强**

增加：

- Semantic Node
- 更稳定的领域建模
- 更强上下文组织

---
# **Phase 3：运行时认知**

接入：

- Trace
- 日志
- Incident

---
# **Phase 4：全局 AI 推理**

引入：

- GraphRAG
- 全局系统推理
- AI Architect

---
# **11. 最终系统定位**

本系统最终不是：

```text
企业文档系统
```

也不是：

```text
AI ChatBot
```

而是：

# **企业长期认知基础设施**

核心目标：

# **为 AI 与人类共同建立长期系统记忆。**
