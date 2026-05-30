# **AI-Native 认知层基础设施（LLM Wiki）技术方案**

---
![[Pasted image 20260525234348.png]]
# **1. 项目背景**

## **1.1 背景**

当前企业研发体系存在以下问题：

### **1）系统知识缺少沉淀**

系统长期演进过程中：

- 文档缺失或长期过期
- 核心逻辑依赖研发经验
- 新成员理解系统成本高
- 业务知识分散在多个位置

典型知识来源包括：

- 代码库
- SQL
- 配置
- 飞书文档
- PR
- 日志
- 事故复盘
- 核心研发经验

---

### **2）AI 无法真正理解企业系统**

当前 AI 工程实践大多基于：

- 文档问答
- 向量检索
- 代码片段生成

存在的问题：

- 无法理解系统结构
- 无法理解调用链
- 无法理解上下游关系
- 无法理解数据流与状态流
- 无法长期维护系统认知

导致 AI 很难真正进入：

- 需求分析
- 老系统迭代
- CR
- 故障排查
- 风险分析

等核心研发流程。

---

## **1.2 建设目标**

建设一套：

# **基于代码的长期知识系统**

核心目标：

- 建立系统级认知结构
- 形成长期可维护 Wiki
- 支持 AI 理解复杂系统
- 支持增量更新
- 支持研发全流程辅助

---

## **1.3 设计原则**

### **Code First**

代码作为最高可信知识源。

文档作为辅助解释信息。

---

### **Local First**

代码解析优先依赖本地环境。

避免复杂中心化编译环境。

---

### **Incremental Update**

基于 Git Diff 增量更新。

避免全量重建。

---

### **Domain Oriented**

按业务域组织知识。

而非按代码目录组织。

---

# **2. 系统目标**

---

# **2.1 第一阶段目标（V1）**

V1 聚焦：

# **系统认知建设**

核心能力：

|**能力**|**目标**|
|---|---|
|代码结构分析|理解系统结构|
|调用链分析|理解上下游关系|
|Wiki 自动生成|建立系统知识|
|增量更新|长期维护|
|Agent 探索|支撑 AI 理解系统|

---

# **2.2 V1 不包含内容**

以下能力暂不建设：

- GraphRAG
- 图数据库
- 在线 AI 搜索平台
- Runtime 全链路分析
- 多 Agent 协同系统

原因：

当前阶段优先验证：

# **AI 是否能够稳定理解企业系统**

---

# **3. 总体架构**

## **3.1 架构模式**

采用：

# **Local-first + Remote Enhancement**

架构。

---

## **3.2 总体架构图**

```text
Git Repository
        ↓
Code Parse Layer
        ↓
CodeGraph Layer
        ↓
Semantic Extraction Layer
        ↓
Agent Exploration Layer
        ↓
Wiki Generation Layer
        ↓
Markdown / Git
```

远程服务仅负责：

```text
LLM Gateway
MCP Tool
Webhook
Feishu API
权限控制
```

---

# **4. 核心模块设计**

# **4.1 Code Parse Layer**

## **职责**

负责代码结构解析。

将源码转换为结构化数据。

---

## **输入**

- Java
- Kotlin
- Go
- TypeScript
- SQL
- YAML
- XML

---

## **输出**

统一结构化对象：

```json
{
  "symbol": "",
  "class": "",
  "method": "",
  "imports": [],
  "annotations": [],
  "sql": [],
  "config": []
}
```

---

## **核心能力**

### **1）Symbol 提取**

提取：

- Class
- Method
- Interface
- Enum

---

### **2）调用关系提取**

提取：

- 方法调用
- Service 调用
- RPC 调用

---

### **3）SQL 解析**

提取：

- 表
- 字段
- Mapper

---

### **4）配置关联**

提取：

- MQ
- Redis
- RPC
- 配置项

---

# **4.2 CodeGraph Layer**

## **职责**

维护代码实体之间的关系结构。

---

## **核心关系**

包括：

|**类型**|**示例**|
|---|---|
|Service → Service|调用关系|
|Service → DB|数据依赖|
|Service → MQ|消息依赖|
|API → Service|接口关系|
|Job → Service|调度关系|

---

## **技术方案**

V1 不自研 Graph Engine。

直接复用：

- codegraph
- tree-sitter
- language server

等现有能力。

---

## **设计原则**

### **不侵入三方工具**

系统不修改 CodeGraph 内部实现。

避免：

- Fork
- 编译链维护
- 多语言适配复杂度失控

---

## **结构缓存**

CodeGraph 输出作为长期结构缓存。

避免 Agent 重复全仓扫描。

---

# **4.3 Semantic Extraction Layer**

## **职责**

基于结构信息生成系统语义。

---

## **输入**

- AST
- CodeGraph
- 文档
- Annotation
- SQL
- 配置

---

## **输出**

统一语义节点：

```json
{
  "name": "RefundService",
  "domain": "refund",
  "description": "负责退款主流程",
  "dependencies": [],
  "risk": [],
  "db": [],
  "mq": []
}
```

---

## **核心能力**

### **1）领域识别**

识别：

- 订单域
- 支付域
- 分账域
- 退款域

---

### **2）系统职责提取**

生成：

- 模块职责
- 业务边界
- 核心链路

---

### **3）风险识别**

识别：

- 幂等
- 一致性
- 补偿
- 延迟

---

## **Semantic Overlay**

语义层不修改 CodeGraph 原始结果。

采用：

# **Overlay 方式增强**

例如：

```text
CodeGraph
   +
Semantic Overlay
   ↓
Agent Context
```

---

# **4.4 Agent Exploration Layer**

## **职责**

负责系统级分析。

不是逐文件总结。

---

## **输入**

- Semantic Node
- CodeGraph
- AST
- 外部文档

---

## **输出**

系统认知结果：

- 核心链路
- 上下游依赖
- 数据流
- 状态流
- 风险点

---

## **探索策略**

采用：

# **React Agent**

多轮探索模式。

---

## **Agent Prompt 设计**

Prompt 聚焦：

- 系统职责
- 业务边界
- 核心状态流
- 数据模型
- 风险点

避免：

- 逐文件总结
- 代码解释型输出

---

## **上下文控制**

避免一次性加载全仓代码。

采用：

- Domain Partition
- CodeGraph 导航
- Symbol 定位
- 分层探索

控制上下文规模。

---

# **4.5 Wiki Generation Layer**

## **职责**

生成可维护知识文档。

---

## **输出格式**

V1 采用：

- Markdown
- Git

---

## **推荐技术栈**

|**类型**|**技术**|
|---|---|
|文档生成|Markdown|
|静态站点|Docusaurus / MkDocs|
|存储|Git|
|Diff|Git Diff|

---

## **Wiki 组织结构**

按业务域组织：

```text
支付域
退款域
订单域
分账域
```

不按：

```text
package
module
repo
```

组织。

---

## **单篇 Wiki 结构**

### **1）系统职责**

说明模块核心功能。

---

### **2）业务边界**

说明：

- 负责内容
- 不负责内容

---

### **3）核心链路**

例如：

```text
退款申请
→ 风控校验
→ 支付退款
→ 状态更新
→ MQ通知
```

---

### **4）数据模型**

包括：

- 核心表
- 生命周期
- 状态

---

### **5）状态机**

描述状态流转。

---

### **6）依赖关系**

包括：

- RPC
- MQ
- Redis
- DB

---

### **7）风险点**

包括：

- 幂等
- 一致性
- 补偿

---

### **8）历史演进**

记录：

- 设计变更
- 历史原因
- 兼容逻辑

---

# **5. 增量更新设计**

# **5.1 目标**

避免全量重建。

降低长期维护成本。

---

# **5.2 更新流程**

```text
Git Diff
    ↓
AST Diff
    ↓
影响分析
    ↓
Semantic Node Update
    ↓
Wiki Update
```

---

# **5.3 影响分析**

根据：

- Symbol 变化
- 调用链变化
- SQL 变化

分析受影响节点。

---

# **5.4 更新粒度**

采用：

# **Node-based Update**

只更新受影响节点。

---

# **6. 知识分层设计**

# **6.1 Code Truth Layer**

最高可信层。

来源：

- 代码
- SQL
- 配置
- API

特点：

- 自动生成
- 强一致
- 可验证

---

# **6.2 Human Knowledge Layer**

来源：

- RFC
- 技术方案
- PRD
- 事故复盘

特点：

- 可能过期
- 质量不稳定

---

## **设计原则**

Human Knowledge：

# **不覆盖 Code Truth**

仅作为补充信息挂载。

---

# **6.3 Runtime Layer（后续阶段）**

后续可接入：

- Trace
- Log
- Metrics
- Incident

形成运行时认知层。

V1 暂不建设。

---

# **7. 远程增强能力**

远程服务仅提供公共能力。

不承担代码解析职责。

---

# **7.1 LLM Gateway**

统一：

- 模型配置
- Token 管理
- 限流
- 日志

---

# **7.2 MCP Tool Service**

统一封装：

- CodeGraph
- SQL Tool
- Git Tool

---

# **7.3 Feishu Integration**

负责：

- Wiki 发布
- 文档更新
- 权限控制

---

# **7.4 Webhook**

支持：

- Git Push 自动更新
- 定时增量更新

---

# **8. 目录结构设计**

推荐：

```text
wiki/
├── domain/
│   ├── payment/
│   ├── refund/
│   ├── order/
│   └── settlement/
│
├── architecture/
│
├── runtime/
│
├── incidents/
│
└── glossary/
```

---

# **9. 工程阶段规划**

# **Phase 1**

目标：

- 跑通代码解析
- 跑通 Wiki 生成
- 跑通增量更新

---

# **Phase 2**

目标：

- 增强 Semantic Layer
- 增强领域识别
- 增强 Agent 探索能力

---

# **Phase 3**

目标：

- 接入 Runtime 数据
- 接入日志与 Trace

---

# **Phase 4**

目标：

- GraphRAG
- 全局推理
- AI 架构分析

---

# **10. 风险与限制**

|**风险**|**说明**|
|---|---|
|多语言复杂度|不同语言解析能力不同|
|大仓库上下文|需要严格控制 Agent 上下文|
|文档可信度|外部文档可能过期|
|Domain 划分困难|业务边界可能不清晰|
|Agent 稳定性|输出质量存在波动|

---

# **11. 最终目标**

构建一套：

# **面向 AI 的系统认知基础设施**

实现：

- 企业知识长期沉淀
- AI 理解复杂系统
- 系统认知可持续演进
- 支撑 AI 进入研发核心流程