---
title: "MemMachine: A Ground-Truth-Preserving Memory System for Personalized AI Agents"
source: "https://arxiv.org/html/2604.04853v1"
author:
published:
created: 2026-07-01
description:
tags:
  - "clippings"
---
Shu Wang shu.wang@memverge.com MemVerge, Inc. Edwin Yu edwin.yu@memverge.com MemVerge, Inc. Oscar Love oscar.love@memverge.com MemVerge, Inc. Tom Zhang tom.zhang@memverge.com MemVerge, Inc. Tom Wong tom.wong@memverge.com MemVerge, Inc. Steve Scargall steve.scargall@memverge.com MemVerge, Inc. Charles Fan charles.fan@memverge.com MemVerge, Inc.

###### Abstract

Large language model (LLM) agents require persistent memory to maintain personalization, factual continuity, and long-horizon task performance, yet standard context-window and retrieval-augmented generation (RAG) workflows remain brittle under multi-session interactions. We present MemMachine, an open-source memory system that combines short-term memory, long-term episodic memory, and profile memory in a ground-truth-preserving architecture that stores raw conversational episodes and minimizes routine LLM-based extraction. MemMachine introduces contextualized retrieval that expands nucleus matches with neighboring episode context, improving recall for conversational queries where semantically related evidence is distributed across turns.

Across multiple benchmarks, MemMachine demonstrates strong accuracy-efficiency tradeoffs. On LoCoMo, it achieves an overall score of 0.9169 with gpt-4.1-mini. On LongMemEval <sub>S</sub> (ICLR 2025), a systematic ablation study across six optimization dimensions yields 93.0% overall accuracy, with retrieval-stage optimizations contributing more than ingestion-stage changes: retrieval depth tuning (+4.2%), context formatting (+2.0%), search prompt design (+1.8%), and query bias correction (+1.4%) each outweigh sentence chunking (+0.8%). A surprising finding is that GPT-5-mini outperforms GPT-5 as the answer LLM (+2.6%) when paired with optimized prompts, yielding the most cost-efficient configuration. In matched memory-mode comparisons, MemMachine uses approximately 80% fewer input tokens than Mem0. We further evaluate a Retrieval Agent that routes queries to direct retrieval, parallel decomposition, or iterative chain-of-query strategies, reaching 93.2% on HotpotQA hard and 92.6% on WikiMultiHop under randomized-noise conditions.

These results suggest that preserving episodic ground truth while layering adaptive retrieval strategies yields robust long-term memory behavior for personalized agents.

Table 1: Benchmark snapshot (quick overview). Detailed setup and full breakdowns are provided in later sections.

<table><tbody><tr><th>Benchmark</th><td>Metric</td><td>Result</td></tr><tr><th>LoCoMo</th><td>Overall score (gpt-4.1-mini)</td><td>91.69%</td></tr><tr><th>LongMemEval <sub>S</sub></th><td>Ablation best (gpt-5-mini)</td><td>93.0%</td></tr><tr><th>HotpotQA hard</th><td>Retrieval Agent accuracy</td><td>93.2%</td></tr><tr><th>WikiMultiHop <sup>†</sup></th><td>Retrieval Agent accuracy</td><td>92.6%</td></tr><tr><th>Mem0 comparison</th><td>Input token reduction</td><td>~80% less</td></tr></tbody><tfoot><tr><th colspan="3"><sup>†</sup> Randomized-noise setting.</th></tr></tfoot></table>

## 1 Introduction

Transformer-based large language models (LLMs) have become the computational foundation for a rapidly growing class of autonomous AI applications, from conversational assistants and customer-facing agents to complex multi-agent workflows [^1] [^2]. Despite their broad capabilities, LLMs exhibit two fundamental limitations that constrain their utility in persistent, personalized applications:

1. Static Parameters. Once trained, an LLM’s weights are fixed. The model cannot acquire new knowledge from interactions without costly fine-tuning or re-training.
2. Restricted Context Window. LLMs operate within a finite context window, requiring applications to carefully curate and compress inference data, often at the cost of losing relevant historical context.

Retrieval-Augmented Generation (RAG) [^3] has emerged as the dominant paradigm for injecting external knowledge into LLM workflows. However, conventional RAG architectures are designed for static document collections and do not support the dynamic, bidirectional interactions characteristic of AI agents that must learn from, and adapt to, evolving user contexts across sessions.

What AI agents require is a *memory system* —a mechanism that goes beyond document retrieval to store, organize, recall, and reason over past experiences. Drawing on established models from cognitive science [^10] [^11], such a system should provide:

- Short-term memory (STM): An immediate workspace maintaining current context, with limited capacity.
- Long-term episodic memory: A store of specific past experiences, providing ground truth about what occurred.
- Semantic memory: High-level summaries, facts, and user profiles distilled from raw experience.
- Procedural memory: Learned rules, strategies, and action patterns that guide agent behavior.

A growing body of systems have begun to address this challenge. MemGPT [^1] explored virtual memory management for LLMs. Mem0 [^4] and Zep [^5] provide long-term memory layers for AI agents. However, these systems primarily rely on LLMs for data extraction, update, aggregation, and deletion—a design that introduces high operational cost, accuracy concerns from probabilistic extraction, and compounding error over time.

### 1.1 Contributions

In this paper, we present MemMachine, an open-source memory system that takes a fundamentally different approach. Our key contributions are:

1. Ground-truth-preserving architecture. MemMachine stores raw conversational episodes and indexes them at the sentence level, minimizing LLM dependence for routine memory operations and preserving factual integrity.
2. Contextualized retrieval. A novel retrieval mechanism that expands nucleus episodes with neighboring context to form episode clusters, addressing the embedding dissimilarity problem inherent in conversational data.
3. Cost-efficient operation. By reserving LLM calls for summarization and high-level abstraction rather than per-message extraction, MemMachine achieves approximately 80% reduction in token usage compared to competing systems.
4. Personalization support. A profile memory system that extracts and maintains user preferences, facts, and behavioral patterns to enable personalized agent interactions across sessions.
5. Leading LoCoMo performance (as of March 2026). MemMachine achieves 0.9169 on LoCoMo with gpt-4.1-mini, among the strongest published results for open memory frameworks and above reported Mem0, Zep, Memobase, LangMem, and OpenAI baseline scores.
6. LongMemEval <sub>S</sub> ablation study. A systematic evaluation on LongMemEval (ICLR 2025) across six optimization dimensions—sentence chunking, query bias correction, context formatting, retrieval depth, search prompt design, and answer-model selection—achieving 93.0% overall accuracy and revealing that retrieval-stage optimizations dominate over ingestion-stage changes.
7. Comprehensive evaluation. We provide reproducible benchmark scripts and analyze the impact of embedding models, reranking strategies, LLM model selection, and retrieval parameters on memory performance.
8. Retrieval Agent for multi-hop reasoning. An LLM-orchestrated retrieval pipeline that classifies queries into structural types and routes them to purpose-built strategies (direct search, parallel decomposition, or iterative chain-of-query), achieving 93.2% accuracy on the HotpotQA hard set while maintaining bounded cost.

MemMachine is released under the Apache 2.0 license and is available at [https://github.com/MemMachine/MemMachine](https://github.com/MemMachine/MemMachine).

## 2 Related Work

### 2.1 Memory for AI Agents

The need for persistent memory in LLM-based agents has been recognized across multiple research threads. Hu et al. [^9] provide a comprehensive survey organizing agent memory by forms (token-level, parametric, latent), functions (factual, experiential, working), and dynamics (formation, evolution, retrieval). Park et al. [^2] demonstrated the power of memory in generative agents that simulate human behavior, using a memory stream architecture with retrieval, reflection, and planning.

MemGPT [^1] introduced an operating-system-inspired virtual memory hierarchy for LLMs, managing context by paging information between a main context and external storage. While pioneering, MemGPT’s approach requires complex memory management that can introduce latency and depends on LLM-driven decisions for memory operations.

### 2.2 Existing Memory Systems

Mem0 [^4] provides a production-oriented memory layer that extracts facts from conversations using LLM calls, stores them in hybrid vector and graph databases, and retrieves them for agent inference. While effective, the per-message LLM extraction approach incurs significant cost and can introduce factual drift through accumulated extraction errors.

Zep [^5] implements a temporal knowledge graph architecture that tracks how facts evolve over time, combining graph-based memory with vector search. Zep excels at relationship modeling and temporal reasoning but introduces complexity in deployment and configuration.

Memobase <sup>1</sup> and LangMem <sup>2</sup> represent additional approaches, with Memobase providing structured memory storage and LangMem integrating memory into the LangChain ecosystem.

More recently, Mastra [^15] introduced *observational memory*, which uses two background agents (Observer and Reflector) to compress conversation history into a dated observation log that stays in context, eliminating retrieval entirely. This approach achieves strong LongMemEval scores (94.87% with GPT-5-mini) and enables aggressive prompt caching, but trades away the ability to search a broader external corpus—making it less suitable for open-ended knowledge discovery or compliance-heavy recall use cases where ground truth access is required.

MemOS [^16] takes the most ambitious architectural stance, proposing a full *memory operating system* that treats memory as a first-class schedulable resource analogous to CPU or storage in traditional operating systems. MemOS unifies three memory types under a single abstraction called *MemCube*: *plaintext memory* (externally injected text, akin to RAG), *activation memory* (KV-cache states from inference), and *parametric memory* (knowledge embedded in model weights, e.g., LoRA adapters). MemCubes carry rich metadata including provenance, versioning, access policies, and lifecycle state, enabling cross-type transformations—for example, promoting frequently accessed plaintext into KV-cache templates for faster inference, or distilling stable knowledge into parametric weights. The system implements a three-layer architecture (interface, operation, infrastructure) with a memory scheduler that orchestrates predictive preloading and multi-user session management. On LoCoMo, MemOS reports 75.80 using GPT-4o-mini as the processing LLM, with a claimed 159% improvement in temporal reasoning over OpenAI’s global memory.

While MemOS represents a compelling long-term vision—particularly its memory lifecycle governance and cross-type transformation pathways—its scope is significantly broader than the other systems discussed here. The parametric and activation memory types require direct access to model internals (weights, KV-caches), which limits portability across LLM providers and closed-source APIs. By contrast, MemMachine, Mem0, Zep, and Mastra operate at the *application layer*, interfacing with LLMs through standard text-based APIs, which enables them to work with any model provider without modification.

These diverse approaches highlight a fundamental design tension in agent memory: *compression vs. preservation*. Systems that aggressively compress (Mastra, Mem0) achieve smaller context windows and lower per-query cost but risk losing critical detail. Systems that preserve raw data (MemMachine) maintain factual integrity at the cost of requiring efficient retrieval mechanisms. A related tension exists between *retrieval-based* approaches (MemMachine, Mem0, Zep) that search selectively and *context-based* approaches (Mastra) that keep compressed history always in context. MemOS introduces a third dimension: *memory-layer depth*, spanning from application-level text memory through inference-level activation caching to model-level parametric adaptation. Table 16 compares these architectural choices.

### 2.3 Memory Benchmarks

The evaluation landscape for agent memory has matured significantly. LoCoMo [^6] evaluates very long-term conversational memory through multi-session dialogues with single-hop, multi-hop, temporal, and open-domain question types. LongMemEval [^7] benchmarks five core long-term memory abilities—information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention—using scalable chat histories. EpBench [^8] focuses on episodic memory evaluation through synthetic narrative corpora ranging from 100K to 1M tokens.

### 2.4 Memory Types in Cognitive Science

Our design draws on the established taxonomy from cognitive science. Tulving [^10] distinguished *episodic memory* (memory of specific personal experiences bound to time and place) from *semantic memory* (general knowledge abstracted from experience). The Atkinson-Shiffrin model [^11] formalized the multi-store architecture with sensory, short-term, and long-term stores. In the AI agent context, we adopt these distinctions while acknowledging that current implementations approximate rather than replicate human memory processes.

## 3 Memory Types for AI Agents

AI agent memory systems draw inspiration from cognitive science while adapting to the practical requirements of LLM-based applications. This section describes the primary memory types and their roles, with emphasis on those implemented in MemMachine.

### 3.1 Episodic Memory

Episodic memory stores specific past experiences— *what* happened, *when*, *where*, and with *whom*. In the agent context, each conversational turn or interaction constitutes an *episode*, a discrete unit of experience with associated metadata (timestamp, participants, session identifier).

Episodic memory serves as ground truth. When an agent needs to recall what a user said, what was decided, or what sequence of events occurred, it queries episodic memory for the raw record. This is essential for factual accuracy, auditability, and trust.

When to use: Factual recall, reconstructing conversation history, answering questions about specific past interactions, providing evidence for decisions, and maintaining conversational continuity across sessions.

### 3.2 Semantic Memory (Profile Memory)

Semantic memory stores generalized knowledge abstracted from episodic experience—user preferences, facts, behavioral patterns, and stable attributes. In MemMachine, this is implemented as Profile Memory, which extracts and maintains structured user profiles from conversational data.

Unlike episodic memory, which preserves the raw record, semantic/profile memory distills high-level patterns: “The user prefers vegetarian restaurants,” “The user works in financial services,” or “The user’s preferred communication style is concise and technical.”

When to use: Personalization, preference-aware recommendations, adapting tone and content, and providing context that does not require recalling a specific episode.

### 3.3 Procedural Memory

Procedural memory encodes learned skills, strategies, and behavioral rules— *how* to do things. In agent systems, this includes tool-use patterns, workflow steps, and decision heuristics. MemMachine does not currently implement procedural memory, though the architecture can be extended to support it.

When to use: Multi-step task execution, tool selection, workflow automation, and strategy reuse.

### 3.4 Temporal Awareness

While not a separate memory type, temporal awareness is a cross-cutting capability. MemMachine tags all episodes with timestamps and supports temporal filtering during search, enabling agents to reason about event ordering, recency, and duration. This provides limited but valuable temporal reasoning without requiring a dedicated temporal memory module.

### 3.5 Episodic vs. Semantic: When to Use Each

The choice between episodic and semantic retrieval depends on the query type:

Table 2: Episodic vs. Semantic Memory Usage

| Criterion | Episodic | Semantic |
| --- | --- | --- |
| Query type | Specific past events | General preferences |
| Accuracy need | Ground truth | Approximate |
| Temporal scope | Point-in-time | Cross-session |
| Data form | Raw conversation | Extracted facts |
| Example | “What did I say about X?” | “What foods do I like?” |

In practice, effective agents combine both: episodic memory for factual grounding and semantic/profile memory for personalization.

## 4 MemMachine Architecture

MemMachine implements a client-server architecture with a two-tier memory system comprising episodic memory (short-term and long-term) and profile memory (semantic). This section describes the system’s components, data flow, and key design decisions.

### 4.1 System Overview

Figure 1 illustrates the high-level architecture. Agents interact with MemMachine through three API interfaces: a RESTful API (v2), a Python SDK, and a Model Context Protocol (MCP) server. The server manages memory processing, while the storage layer persists data across PostgreSQL (with pgvector for vector search), SQLite, and Neo4j (for graph-structured long-term memory).

<svg id="S4.F1.pic1" height="294.62" overflow="visible" version="1.1" viewBox="0 0 261.18 294.62" width="261.18"><g transform="translate(0,294.62) matrix(1 0 0 -1 0 0) translate(32.9,0) translate(0,237.12)"><g style="--ltx-stroke-color:#808080;--ltx-fill-color:#F5F5F5;" stroke="#808080" fill="#F5F5F5" stroke-width="0.7pt"><path d="M 164.42 -184.62 L 13.2 -184.62 C 9.38 -184.62 6.28 -187.72 6.28 -191.54 L 6.28 -229.72 C 6.28 -233.54 9.38 -236.64 13.2 -236.64 L 164.42 -236.64 C 168.24 -236.64 171.34 -233.54 171.34 -229.72 L 171.34 -191.54 C 171.34 -187.72 168.24 -184.62 164.42 -184.62 Z M 6.28 -236.64"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.7pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 13.36 -210.63)"></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke="#000000" fill="#000000" stroke-width="0.4pt"><g style="--ltx-stroke-color:#FAFAFA;--ltx-fill-color:#FAFAFA;--ltx-fg-color:#FAFAFA;" stroke="#FAFAFA" fill="#FAFAFA" color="#FAFAFA"><path style="stroke:none" d="M -23.62 13.78 M -23.62 4.09 L -23.62 -161.57 C -23.62 -166.92 -19.29 -171.26 -13.94 -171.26 L 204.88 -171.26 C 210.23 -171.26 214.57 -166.92 214.57 -161.57 L 214.57 4.09 C 214.57 9.44 210.23 13.78 204.88 13.78 L -13.94 13.78 C -19.29 13.78 -23.62 9.44 -23.62 4.09 Z M 214.57 -171.26"></path></g><g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#4D4D4D;--ltx-fg-color:#4D4D4D;" stroke="#4D4D4D" fill="#4D4D4D" stroke-width="1.0pt" color="#4D4D4D"><path style="fill:none" d="M -23.62 13.78 M -23.62 4.09 L -23.62 -161.57 C -23.62 -166.92 -19.29 -171.26 -13.94 -171.26 L 204.88 -171.26 C 210.23 -171.26 214.57 -166.92 214.57 -161.57 L 214.57 4.09 C 214.57 9.44 210.23 13.78 204.88 13.78 L -13.94 13.78 C -19.29 13.78 -23.62 9.44 -23.62 4.09 Z M 214.57 -171.26"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 38.9 0.45)" fill="#000000" stroke="#000000"><foreignObject style="--ltx-fo-width:7.57em;--ltx-fo-height:0.58em;--ltx-fo-depth:0em;" width="111.59" height="8.54" transform="matrix(1 0 0 -1 0 8.54)" overflow="visible"><span id="S4.F1.pic1.2.2.2.1.1.1" style="font-size:90%;">MEMMACHINE</span></foreignObject></g> <g style="--ltx-stroke-color:#F2F2FF;--ltx-fill-color:#F2F2FF;--ltx-fg-color:#F2F2FF;" stroke="#F2F2FF" fill="#F2F2FF" color="#F2F2FF"><path style="stroke:none" d="M -9.84 -84.65 M -9.84 -91.56 L -9.84 -154.5 C -9.84 -158.32 -6.75 -161.42 -2.92 -161.42 L 121.03 -161.42 C 124.86 -161.42 127.95 -158.32 127.95 -154.5 L 127.95 -91.56 C 127.95 -87.74 124.86 -84.65 121.03 -84.65 L -2.92 -84.65 C -6.75 -84.65 -9.84 -87.74 -9.84 -91.56 Z M 127.95 -161.42"></path></g><g style="--ltx-stroke-color:#808080;--ltx-fill-color:#808080;--ltx-fg-color:#808080;" stroke="#808080" fill="#808080" stroke-width="0.7pt" color="#808080"><path style="fill:none" d="M -9.84 -84.65 M -9.84 -91.56 L -9.84 -154.5 C -9.84 -158.32 -6.75 -161.42 -2.92 -161.42 L 121.03 -161.42 C 124.86 -161.42 127.95 -158.32 127.95 -154.5 L 127.95 -91.56 C 127.95 -87.74 124.86 -84.65 121.03 -84.65 L -2.92 -84.65 C -6.75 -84.65 -9.84 -87.74 -9.84 -91.56 Z M 127.95 -161.42"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 10.83 -81.16)" fill="#000000" stroke="#000000"><foreignObject style="--ltx-fo-width:7.67em;--ltx-fo-height:0.54em;--ltx-fo-depth:0.15em;" width="96.11" height="8.61" transform="matrix(1 0 0 -1 0 6.73)" overflow="visible"><span id="S4.F1.pic1.3.3.3.2.1.1" style="font-size:70%;">Episodic Memory</span></foreignObject></g> <g style="--ltx-stroke-color:#FBF0F4;--ltx-fill-color:#FBF0F4;--ltx-fg-color:#FBF0F4;" stroke="#FBF0F4" fill="#FBF0F4" color="#FBF0F4"><path style="stroke:none" d="M 135.83 -84.65 M 135.83 -91.56 L 135.83 -154.5 C 135.83 -158.32 138.92 -161.42 142.75 -161.42 L 195.84 -161.42 C 199.66 -161.42 202.76 -158.32 202.76 -154.5 L 202.76 -91.56 C 202.76 -87.74 199.66 -84.65 195.84 -84.65 L 142.75 -84.65 C 138.92 -84.65 135.83 -87.74 135.83 -91.56 Z M 202.76 -161.42"></path></g><g style="--ltx-stroke-color:#808080;--ltx-fill-color:#808080;--ltx-fg-color:#808080;" stroke="#808080" fill="#808080" stroke-width="0.7pt" color="#808080"><path style="fill:none" d="M 135.83 -84.65 M 135.83 -91.56 L 135.83 -154.5 C 135.83 -158.32 138.92 -161.42 142.75 -161.42 L 195.84 -161.42 C 199.66 -161.42 202.76 -158.32 202.76 -154.5 L 202.76 -91.56 C 202.76 -87.74 199.66 -84.65 195.84 -84.65 L 142.75 -84.65 C 138.92 -84.65 135.83 -87.74 135.83 -91.56 Z M 202.76 -161.42"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 119.31 -81.16)" fill="#000000" stroke="#000000"><foreignObject style="--ltx-fo-width:8em;--ltx-fo-height:0.54em;--ltx-fo-depth:0.15em;" width="100.3" height="8.61" transform="matrix(1 0 0 -1 0 6.73)" overflow="visible"><span id="S4.F1.pic1.4.4.4.3.1.1" style="font-size:70%;">Semantic Memory</span></foreignObject></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E0FFE0;" stroke="#4D4D4D" fill="#E0FFE0" stroke-width="0.6pt"><path d="M 28.33 57.09 L -28.33 57.09 C -30.62 57.09 -32.48 55.23 -32.48 52.94 L -32.48 41.55 C -32.48 39.26 -30.62 37.4 -28.33 37.4 L 28.33 37.4 C 30.62 37.4 32.48 39.26 32.48 41.55 L 32.48 52.94 C 32.48 55.23 30.62 57.09 28.33 57.09 Z M -32.48 37.4"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 -25.55 44.86)"><text transform="matrix(1 0 0 -1 0 0)">AI Agent</text></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E0FFE0;" stroke="#4D4D4D" fill="#E0FFE0" stroke-width="0.6pt"><path d="M 130.26 57.09 L 58.72 57.09 C 56.42 57.09 54.57 55.23 54.57 52.94 L 54.57 41.55 C 54.57 39.26 56.42 37.4 58.72 37.4 L 130.26 37.4 C 132.55 37.4 134.41 39.26 134.41 41.55 L 134.41 52.94 C 134.41 55.23 132.55 57.09 130.26 57.09 Z M 54.57 37.4"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 59.18 44.82)"><text transform="matrix(1 0 0 -1 0 0)">Python SDK</text></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E0FFE0;" stroke="#4D4D4D" fill="#E0FFE0" stroke-width="0.6pt"><path d="M 223.72 57.09 L 154.24 57.09 C 151.94 57.09 150.08 55.23 150.08 52.94 L 150.08 41.55 C 150.08 39.26 151.94 37.4 154.24 37.4 L 223.72 37.4 C 226.01 37.4 227.87 39.26 227.87 41.55 L 227.87 52.94 C 227.87 55.23 226.01 57.09 223.72 57.09 Z M 150.08 37.4"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 154.7 43.92)"><text transform="matrix(1 0 0 -1 0 0)">MCP Server</text></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#FFECD9;" stroke="#4D4D4D" fill="#FFECD9" stroke-width="0.6pt"><path d="M 77.63 -9.84 L 16.85 -9.84 C 14.56 -9.84 12.7 -11.7 12.7 -13.99 L 12.7 -25.38 C 12.7 -27.67 14.56 -29.53 16.85 -29.53 L 77.63 -29.53 C 79.93 -29.53 81.78 -27.67 81.78 -25.38 L 81.78 -13.99 C 81.78 -11.7 79.93 -9.84 77.63 -9.84 Z M 12.7 -29.53"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 17.32 -23.01)"><text transform="matrix(1 0 0 -1 0 0)">REST API</text></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#FFECD9;" stroke="#4D4D4D" fill="#FFECD9" stroke-width="0.6pt"><path d="M 169.63 -9.84 L 98.09 -9.84 C 95.79 -9.84 93.94 -11.7 93.94 -13.99 L 93.94 -25.38 C 93.94 -27.67 95.79 -29.53 98.09 -29.53 L 169.63 -29.53 C 171.92 -29.53 173.78 -27.67 173.78 -25.38 L 173.78 -13.99 C 173.78 -11.7 171.92 -9.84 169.63 -9.84 Z M 93.94 -29.53"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 98.55 -22.11)"><text transform="matrix(1 0 0 -1 0 0)">Python SDK</text></g> <g style="--ltx-stroke-color:#A6A6A6;--ltx-fill-color:#A6A6A6;--ltx-fg-color:#A6A6A6;" stroke-dasharray="3.0pt,3.0pt" stroke-dashoffset="0.0pt" fill="#A6A6A6" stroke="#A6A6A6" stroke-width="0.5pt" color="#A6A6A6"><path style="fill:none" d="M 82.2 -19.69 L 93.52 -19.69"></path></g><g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E6E6FF;" stroke="#4D4D4D" fill="#E6E6FF" stroke-width="0.6pt"><path d="M 51.68 -103.45 L -0.5 -103.45 C -2.8 -103.45 -4.65 -105.31 -4.65 -107.6 L -4.65 -132.55 C -4.65 -134.85 -2.8 -136.71 -0.5 -136.71 L 51.68 -136.71 C 53.98 -136.71 55.83 -134.85 55.83 -132.55 L 55.83 -107.6 C 55.83 -105.31 53.98 -103.45 51.68 -103.45 Z M -4.65 -136.71"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 -0.04 -130.36)"><g transform="matrix(1 0 0 -1 0 22.3)"><g transform="matrix(1 0 0 1 0 15.23)"><g transform="matrix(1 0 0 -1 5.3 0)"><g transform="matrix(1 0 0 -1 0 15.23)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 0 0)"><text transform="matrix(1 0 0 -1 0 0)">Working</text></g></g> <g transform="matrix(1 0 0 1 0 15.23)"><g transform="matrix(1 0 0 -1 0.52 0)"><text transform="matrix(1 0 0 -1 0 0)">Memory</text></g></g></g></g></g> <g transform="matrix(1 0 0 1 0 22.3)"><g transform="matrix(1 0 0 -1 0 0)"><foreignObject style="--ltx-fo-width:5.44em;--ltx-fo-height:0.55em;--ltx-fo-depth:0.18em;" width="51.26" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S4.F1.pic1.5.5.5.4.1.1.1.1.1" style="font-size:50%;">(short-term)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E6E6FF;" stroke="#4D4D4D" fill="#E6E6FF" stroke-width="0.6pt"><path d="M 118.88 -104.45 L 70.1 -104.45 C 67.8 -104.45 65.94 -106.31 65.94 -108.6 L 65.94 -131.56 C 65.94 -133.85 67.8 -135.71 70.1 -135.71 L 118.88 -135.71 C 121.17 -135.71 123.03 -133.85 123.03 -131.56 L 123.03 -108.6 C 123.03 -106.31 121.17 -104.45 118.88 -104.45 Z M 65.94 -135.71"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 70.66 -129.37)"><g transform="matrix(1 0 0 -1 0 20.31)"><g transform="matrix(1 0 0 1 0 13.24)"><g transform="matrix(1 0 0 -1 0 0)"><g transform="matrix(1 0 0 -1 0 13.24)"><g transform="matrix(1 0 0 1 0 6.62)"><g transform="matrix(1 0 0 -1 0 0)"><text transform="matrix(1 0 0 -1 0 0)">Persistent</text></g></g> <g transform="matrix(1 0 0 1 0 13.24)"><g transform="matrix(1 0 0 -1 4.02 0)"><text transform="matrix(1 0 0 -1 0 0)">Memory</text></g></g></g></g></g> <g transform="matrix(1 0 0 1 0 20.31)"><g transform="matrix(1 0 0 -1 0.1 0)"><foreignObject style="--ltx-fo-width:5.04em;--ltx-fo-height:0.55em;--ltx-fo-depth:0.18em;" width="47.47" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S4.F1.pic1.6.6.6.5.1.1.1.1.1" style="font-size:50%;">(long-term)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E6E6FF;" stroke="#4D4D4D" fill="#E6E6FF" stroke-width="0.6pt"><path d="M 193.68 -110.24 L 144.9 -110.24 C 142.61 -110.24 140.75 -112.09 140.75 -114.39 L 140.75 -133.64 C 140.75 -135.94 142.61 -137.8 144.9 -137.8 L 193.68 -137.8 C 195.98 -137.8 197.83 -135.94 197.83 -133.64 L 197.83 -114.39 C 197.83 -112.09 195.98 -110.24 193.68 -110.24 Z M 140.75 -137.8"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 149.48 -129.75)"><g transform="matrix(1 0 0 -1 0 13.35)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 3.86 0)"><text transform="matrix(1 0 0 -1 0 0)">Profile</text></g></g> <g transform="matrix(1 0 0 1 0 13.35)"><g transform="matrix(1 0 0 -1 0 0)"><text transform="matrix(1 0 0 -1 0 0)">Memory</text></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E8E8E8;" stroke="#4D4D4D" fill="#E8E8E8" stroke-width="0.6pt"><path d="M 52.94 -200.79 L 17.93 -200.79 C 15.64 -200.79 13.78 -202.65 13.78 -204.94 L 13.78 -216.32 C 13.78 -218.61 15.64 -220.47 17.93 -220.47 L 52.94 -220.47 C 55.23 -220.47 57.09 -218.61 57.09 -216.32 L 57.09 -204.94 C 57.09 -202.65 55.23 -200.79 52.94 -200.79 Z M 13.78 -220.47"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 23.52 -213.01)"><text transform="matrix(1 0 0 -1 0 0)">SQL</text></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E8E8E8;" stroke="#4D4D4D" fill="#E8E8E8" stroke-width="0.6pt"><path d="M 107.04 -200.79 L 70.12 -200.79 C 67.83 -200.79 65.97 -202.65 65.97 -204.94 L 65.97 -216.32 C 65.97 -218.61 67.83 -220.47 70.12 -220.47 L 107.04 -220.47 C 109.34 -220.47 111.19 -218.61 111.19 -216.32 L 111.19 -204.94 C 111.19 -202.65 109.34 -200.79 107.04 -200.79 Z M 65.97 -220.47"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 70.58 -213.95)"><text transform="matrix(1 0 0 -1 0 0)">Vector</text></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E8E8E8;" stroke="#4D4D4D" fill="#E8E8E8" stroke-width="0.6pt"><path d="M 159.69 -200.79 L 123.78 -200.79 C 121.49 -200.79 119.63 -202.65 119.63 -204.94 L 119.63 -216.32 C 119.63 -218.61 121.49 -220.47 123.78 -220.47 L 159.69 -220.47 C 161.98 -220.47 163.84 -218.61 163.84 -216.32 L 163.84 -204.94 C 163.84 -202.65 161.98 -200.79 159.69 -200.79 Z M 119.63 -220.47"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 124.24 -213.05)"><text transform="matrix(1 0 0 -1 0 0)">Graph</text></g> <g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 60.91 -195.49)" fill="#000000" stroke="#000000"><foreignObject style="--ltx-fo-width:4.41em;--ltx-fo-height:0.54em;--ltx-fo-depth:0em;" width="55.34" height="6.73" transform="matrix(1 0 0 -1 0 6.73)" overflow="visible"><span id="S4.F1.pic1.7.7.7.6.1.1" style="font-size:70%;">Databases</span></foreignObject></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 0 36.99 L 0 25.18 L 43.31 25.18 L 43.31 -4.85"></path><g transform="matrix(0.0 -1.0 1.0 0.0 43.31 -2.34)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 94.49 36.99 L 94.49 25.18 L 51.18 25.18 L 51.18 -4.85"></path><g transform="matrix(0.0 -1.0 1.0 0.0 51.18 -2.34)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 188.98 36.99 L 188.98 25.18 L 133.86 25.18 L 133.86 -4.85"></path><g transform="matrix(0.0 -1.0 1.0 0.0 133.86 -2.34)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 35.43 -29.94 L 35.43 -51.6 L 25.59 -51.6 L 25.59 -98.46"></path><g transform="matrix(0.0 -1.0 1.0 0.0 25.59 -95.95)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 59.05 -29.94 L 59.05 -51.6 L 94.49 -51.6 L 94.49 -99.45"></path><g transform="matrix(0.0 -1.0 1.0 0.0 94.49 -96.95)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 133.86 -29.94 L 133.86 -51.6 L 169.29 -51.6 L 169.29 -105.24"></path><g transform="matrix(0.0 -1.0 1.0 0.0 169.29 -102.73)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 59.06 -161.42 L 59.06 -173.23 L 88.58 -173.23 L 88.58 -195.79"></path><g transform="matrix(0.0 -1.0 1.0 0.0 88.58 -193.29)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 169.29 -161.42 L 169.29 -169.29 L 141.73 -169.29 L 141.73 -195.79"></path><g transform="matrix(0.0 -1.0 1.0 0.0 141.73 -193.29)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g></g></svg>

Figure 1: MemMachine system architecture. Clients (AI agents, Python SDK, MCP servers) access MemMachine through REST API and SDK interfaces. Internally, episodic memory comprises working memory (short-term) and persistent memory (long-term), while semantic memory stores user profiles. All memory types are backed by SQL, vector, and graph databases.

### 4.2 Data Ingestion

Raw messages are submitted to MemMachine with metadata. The system organizes each message into an internal data structure called an Episode. Each episode represents one conversational turn and carries required metadata:

- Producer: The source of the message (user, agent, system).
- Timestamp: When the message was produced.
- Session ID: Grouping episodes into conversational sessions.
- Custom metadata: Arbitrary key-value pairs for domain-specific filtering.

Episodes are stored in a central database as a raw data repository and simultaneously dispatched to episodic memory and profile memory for ingestion and indexing.

### 4.3 Short-Term Memory

Short-term memory (STM) maintains a configurable context window of the most recent episodes, providing immediate conversational context. Key behaviors:

- Holds a predefined number of recent episodes.
- Generates compressed summaries of session-level interactions via LLM-based abstraction.
- When content exceeds the window, both episodes and summaries are compressed for efficient storage and eventually transferred to long-term memory.

STM ensures that agents always have access to the immediate conversational context without requiring a retrieval step, while the summarization mechanism preserves the gist of older context within the window.

### 4.4 Long-Term Memory

Long-term memory (LTM) provides persistent, searchable storage for all episodes that have exited the STM window. The indexing pipeline comprises four stages:

1. Sentence Extraction: Each episode is segmented into individual sentences using NLTK’s Punkt tokenizer [^12]. This fine-grained decomposition enables precise embedding and retrieval at the sentence level rather than the episode level.
2. Metadata Augmentation: Each sentence inherits metadata from its parent episode (timestamp, producer, session) and receives a unique identifier.
3. Relational Mapping: Sentences are linked to their originating episodes, maintaining provenance.
4. Embedding Generation: Semantic embeddings are generated for each sentence. MemMachine supports configurable embedding models, enabling domain-specific models for improved performance.

The original episodes, augmented sentences, and embeddings are persisted in the database. Neo4j provides graph-based storage that enables relational traversal, while PostgreSQL with pgvector supports efficient vector similarity search.

### 4.5 Memory Search and Recall

Memory search in MemMachine follows a staged recall pipeline that balances speed, coverage, and factual grounding. The system first checks near-term context, then expands into long-term episodic retrieval, and finally refines candidates before returning results. Figure 2 (Figure 2) summarizes this end-to-end workflow.

<svg id="S4.F2.pic1" height="285.92" overflow="visible" version="1.1" viewBox="0 0 118.66 285.92" width="118.66"><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="translate(0,285.92) matrix(1 0 0 -1 0 0) translate(59.33,0) translate(0,275.8)" fill="#000000" stroke="#000000"><g stroke-width="0.4pt"><g style="--ltx-fill-color:#FFF2E6;" fill="#FFF2E6"><path d="M 56.29 9.84 L -56.29 9.84 C -57.82 9.84 -59.06 8.6 -59.06 7.08 L -59.06 -7.08 C -59.06 -8.6 -57.82 -9.84 -56.29 -9.84 L 56.29 -9.84 C 57.82 -9.84 59.06 -8.6 59.06 -7.08 L 59.06 7.08 C 59.06 8.6 57.82 9.84 56.29 9.84 Z M -59.06 -9.84"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -51.25 -2.42)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">User Query + Filters</text></g> <g style="--ltx-fill-color:#E6E6FF;" fill="#E6E6FF"><path d="M 56.29 -28.11 L -56.29 -28.11 C -57.82 -28.11 -59.06 -29.35 -59.06 -30.88 L -59.06 -45.03 C -59.06 -46.56 -57.82 -47.8 -56.29 -47.8 L 56.29 -47.8 C 57.82 -47.8 59.06 -46.56 59.06 -45.03 L 59.06 -30.88 C 59.06 -29.35 57.82 -28.11 56.29 -28.11 Z M -59.06 -47.8"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -29.65 -41.32)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">STM Search</text></g> <g style="--ltx-fill-color:#D9D9FF;" fill="#D9D9FF"><path d="M 56.29 -66.07 L -56.29 -66.07 C -57.82 -66.07 -59.06 -67.31 -59.06 -68.83 L -59.06 -82.99 C -59.06 -84.51 -57.82 -85.75 -56.29 -85.75 L 56.29 -85.75 C 57.82 -85.75 59.06 -84.51 59.06 -82.99 L 59.06 -68.83 C 59.06 -67.31 57.82 -66.07 56.29 -66.07 Z M -59.06 -85.75"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -47.07 -79.27)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">LTM Vector Search</text></g> <g style="--ltx-fill-color:#FFFFE6;" fill="#FFFFE6"><path d="M 56.29 -104.02 L -56.29 -104.02 C -57.82 -104.02 -59.06 -105.26 -59.06 -106.79 L -59.06 -120.94 C -59.06 -122.47 -57.82 -123.71 -56.29 -123.71 L 56.29 -123.71 C 57.82 -123.71 59.06 -122.47 59.06 -120.94 L 59.06 -106.79 C 59.06 -105.26 57.82 -104.02 56.29 -104.02 Z M -59.06 -123.71"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -43.01 -117.23)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">Contextualization</text></g> <g style="--ltx-fill-color:#E6FFE6;" fill="#E6FFE6"><path d="M 56.29 -141.98 L -56.29 -141.98 C -57.82 -141.98 -59.06 -143.22 -59.06 -144.75 L -59.06 -158.9 C -59.06 -160.42 -57.82 -161.66 -56.29 -161.66 L 56.29 -161.66 C 57.82 -161.66 59.06 -160.42 59.06 -158.9 L 59.06 -144.75 C 59.06 -143.22 57.82 -141.98 56.29 -141.98 Z M -59.06 -161.66"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -53.64 -154.24)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">De-duplicate Episodes</text></g> <g style="--ltx-fill-color:#E6FFE6;" fill="#E6FFE6"><path d="M 56.29 -179.93 L -56.29 -179.93 C -57.82 -179.93 -59.06 -181.17 -59.06 -182.7 L -59.06 -196.85 C -59.06 -198.38 -57.82 -199.62 -56.29 -199.62 L 56.29 -199.62 C 57.82 -199.62 59.06 -198.38 59.06 -196.85 L 59.06 -182.7 C 59.06 -181.17 57.82 -179.93 56.29 -179.93 Z M -59.06 -199.62"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -38.96 -193.14)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">Rerank Clusters</text></g> <g style="--ltx-fill-color:#D9FFD9;" fill="#D9FFD9"><path d="M 56.29 -217.89 L -56.29 -217.89 C -57.82 -217.89 -59.06 -219.13 -59.06 -220.66 L -59.06 -234.81 C -59.06 -236.33 -57.82 -237.57 -56.29 -237.57 L 56.29 -237.57 C 57.82 -237.57 59.06 -236.33 59.06 -234.81 L 59.06 -220.66 C 59.06 -219.13 57.82 -217.89 56.29 -217.89 Z M -59.06 -237.57"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -49.65 -230.15)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">Sort Chronologically</text></g> <g style="--ltx-fill-color:#FFF2E6;" fill="#FFF2E6"><path d="M 56.29 -255.84 L -56.29 -255.84 C -57.82 -255.84 -59.06 -257.08 -59.06 -258.61 L -59.06 -272.76 C -59.06 -274.29 -57.82 -275.53 -56.29 -275.53 L 56.29 -275.53 C 57.82 -275.53 59.06 -274.29 59.06 -272.76 L 59.06 -258.61 C 59.06 -257.08 57.82 -255.84 56.29 -255.84 Z M -59.06 -275.53"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" transform="matrix(1.0 0.0 0.0 1.0 -36.42 -269.05)" fill="#000000" stroke="#000000"><text transform="matrix(1 0 0 -1 0 0)">Return Results</text></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -10.12 L 0 -22.72"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -19.96)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -48.07 L 0 -60.68"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -57.92)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -86.03 L 0 -98.63"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -95.87)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -123.98 L 0 -136.59"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -133.83)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -161.94 L 0 -174.54"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -171.78)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -199.89 L 0 -212.5"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -209.74)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g><g stroke-width="0.8pt"><path style="fill:none" d="M 0 -237.85 L 0 -250.45"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -247.69)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 6.4 0 L 1.79 1.71 L 3.04 0 L 1.79 -1.71 Z"></path></g></g></g></svg>

Figure 2: Memory recall workflow. The query passes through STM, LTM vector search, contextualization, deduplication, reranking, and chronological sorting before returning results.

#### 4.5.1 Long-Term Memory Search

LTM search begins with a vector similarity search using Approximate Nearest Neighbor (ANN) or exact matching against the sentence embeddings. Matched sentences are traced back to their originating episodes, with duplicates removed. The system then applies *contextualization* (Section 4.6).

#### 4.5.2 Episodic Memory Search

Episodic search coordinates STM and LTM. It invokes LTM search for episodes outside the STM window, deduplicates overlapping episodes between STM and LTM, sorts all results chronologically to preserve conversational flow, and returns STM episodes, the STM summary, and LTM episodes for agent-driven context assembly.

### 4.6 Contextualization

A key challenge in conversational memory retrieval is that contextually important episodes may have embeddings quite dissimilar from the query. Unlike document retrieval in traditional RAG, where each chunk is relatively self-contained, conversational turns are highly interdependent. A question about “the restaurant recommendation” requires not just the turn containing the recommendation, but the surrounding turns that establish what was asked, why, and what constraints were given.

MemMachine addresses this with contextualized retrieval:

1. The nucleus episode is located via embedding search.
2. Immediate neighboring episodes are retrieved (one preceding, two following) to form an episode cluster.
3. Episode clusters are reranked using a cross-encoder or other reranking model.
4. The top- $k$ clusters are provided for LLM inference.

This approach ensures that the LLM receives not just the most semantically similar turns, but the conversational context necessary for accurate reasoning. Our experimental results (Section 8) demonstrate the significant impact of contextualization on benchmark performance.

### 4.7 Profile Memory (Semantic Memory)

Profile memory extracts and maintains user-level facts and preferences from conversational data. Unlike episodic memory, which preserves raw interactions, profile memory synthesizes high-level user attributes:

- Demographic information volunteered by the user.
- Stated preferences and interests.
- Behavioral patterns observed across sessions.
- Professional context and domain expertise.

Profile memory is stored in SQL databases (PostgreSQL or SQLite) and supports both retrieval and update operations. When new information contradicts existing profile data, the system can update the profile to reflect the most recent state—supporting the *knowledge update* capability evaluated in benchmarks such as LongMemEval [^7].

### 4.8 Multi-Tenancy and Isolation

MemMachine implements project-based namespace isolation. Each project is identified by an org\_id/project\_id pair and maintains separate memory instances. Sessions are further isolated by user\_id, agent\_id, and session\_id, enabling multi-tenant deployments where multiple users and agents operate with fully isolated memory stores.

## 5 Retrieval Agent

MemMachine’s baseline retrieval mechanism—vector similarity search with optional reranking—performs well on single-hop queries where the answer resides in a single episode cluster. However, production AI agents routinely encounter queries that require *multi-hop reasoning*, *multi-entity fan-out*, or *cross-referential dependency chains*. For such queries, a single embedding cannot capture all the information needed because intermediate entities are unknown at query time. We call this the late binding problem: the correct query for a later retrieval hop cannot be formulated until an earlier hop has been resolved.

To address this, MemMachine v0.3 introduces the Retrieval Agent—an opt-in, LLM-orchestrated retrieval pipeline that routes queries to purpose-built strategies while maintaining bounded cost and latency. The Retrieval Agent augments (not replaces) the baseline search: callers who do not enable agent mode experience zero behavioral change.

### 5.1 The Late Binding Problem

Consider a multi-hop query: *“What is the current employer of the spouse of the CEO of Acme?”* Answering this requires three ordered resolution steps: (1) identify the CEO of Acme $\to$ Person X, (2) identify the spouse of Person X $\to$ Person Y, (3) identify the employer of Person Y $\to$ Company Z. At query time, only the original query string is available. Its embedding clusters around surface terms (“Acme,” “CEO,” “company”) and has no path to Company Z because the intermediate entities are unknown. This is not a limitation of the embedding model—it is a structural property of information dependencies in multi-hop chains that no single-shot vector retrieval can resolve.

Existing mitigation strategies—query expansion (HyDE), BM25 hybrid search, chunk-level reranking—improve single-hop recall but cannot resolve dependency chains because they still operate on a single query formulation. Knowledge graph traversal solves late binding exactly but requires prior graph construction, which is expensive and lossy for arbitrary conversational content.

### 5.2 Architecture

The Retrieval Agent is implemented as a composable tool tree assembled inside MemMachine’s long-term memory module. Figure 3 shows the architecture: a root router dispatches each query to exactly one of three strategy nodes, all of which ultimately delegate to the same declarative memory search.

<svg id="S5.F3.pic1" height="143.76" overflow="visible" version="1.1" viewBox="0 0 249.28 143.76" width="249.28"><g transform="translate(0,143.76) matrix(1 0 0 -1 0 0) translate(40.21,0) translate(0,130.9)"><g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#FFECD9;" stroke="#4D4D4D" fill="#FFECD9" stroke-width="0.7pt"><path d="M 130.29 12.38 L 39 12.38 C 35.94 12.38 33.46 9.9 33.46 6.84 L 33.46 -6.84 C 33.46 -9.9 35.94 -12.38 39 -12.38 L 130.29 -12.38 C 133.35 -12.38 135.83 -9.9 135.83 -6.84 L 135.83 6.84 C 135.83 9.9 133.35 12.38 130.29 12.38 Z M 33.46 -12.38"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.7pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 38.64 -6.03)"><g transform="matrix(1 0 0 -1 0 13.8)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 1.32 0)"><text transform="matrix(1 0 0 -1 0 0)">ToolSelectAgent</text></g></g> <g transform="matrix(1 0 0 1 0 13.8)"><g transform="matrix(1 0 0 -1 0 0)"><foreignObject style="--ltx-fo-width:8.77em;--ltx-fo-height:0.49em;--ltx-fo-depth:0.16em;" width="92" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S5.F3.pic1.1.1.1.1.1.1.1.1" style="font-size:50%;">(LLM query router)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E6E6FF;" stroke="#4D4D4D" fill="#E6E6FF" stroke-width="0.6pt"><path d="M 35.64 -42.43 L -35.64 -42.43 C -37.93 -42.43 -39.79 -44.29 -39.79 -46.58 L -39.79 -71.53 C -39.79 -73.82 -37.93 -75.68 -35.64 -75.68 L 35.64 -75.68 C 37.93 -75.68 39.79 -73.82 39.79 -71.53 L 39.79 -46.58 C 39.79 -44.29 37.93 -42.43 35.64 -42.43 Z M -39.79 -75.68"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 -35.18 -69.34)"><g transform="matrix(1 0 0 -1 0 22.3)"><g transform="matrix(1 0 0 1 0 15.23)"><g transform="matrix(1 0 0 -1 0 0)"><g transform="matrix(1 0 0 -1 0 15.23)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 0 0)"><text transform="matrix(1 0 0 -1 0 0)">ChainOfQuery</text></g></g> <g transform="matrix(1 0 0 1 0 15.23)"><g transform="matrix(1 0 0 -1 20.81 0)"><text transform="matrix(1 0 0 -1 0 0)">Agent</text></g></g></g></g></g> <g transform="matrix(1 0 0 1 0 22.3)"><g transform="matrix(1 0 0 -1 11.32 0)"><foreignObject style="--ltx-fo-width:5.09em;--ltx-fo-height:0.55em;--ltx-fo-depth:0.18em;" width="47.95" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S5.F3.pic1.2.2.2.1.1.1.1.1" style="font-size:50%;">(multi-hop)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E6E6FF;" stroke="#4D4D4D" fill="#E6E6FF" stroke-width="0.6pt"><path d="M 119.86 -42.43 L 49.43 -42.43 C 47.13 -42.43 45.28 -44.29 45.28 -46.58 L 45.28 -71.53 C 45.28 -73.82 47.13 -75.68 49.43 -75.68 L 119.86 -75.68 C 122.16 -75.68 124.02 -73.82 124.02 -71.53 L 124.02 -46.58 C 124.02 -44.29 122.16 -42.43 119.86 -42.43 Z M 45.28 -75.68"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 58.41 -69.34)"><g transform="matrix(1 0 0 -1 0 22.3)"><g transform="matrix(1 0 0 1 0 15.23)"><g transform="matrix(1 0 0 -1 0 0)"><g transform="matrix(1 0 0 -1 0 15.23)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 0 0)"><text transform="matrix(1 0 0 -1 0 0)">SplitQuery</text></g></g> <g transform="matrix(1 0 0 1 0 15.23)"><g transform="matrix(1 0 0 -1 11.87 0)"><text transform="matrix(1 0 0 -1 0 0)">Agent</text></g></g></g></g></g> <g transform="matrix(1 0 0 1 0 22.3)"><g transform="matrix(1 0 0 -1 7.57 0)"><foreignObject style="--ltx-fo-width:3.96em;--ltx-fo-height:0.55em;--ltx-fo-depth:0.18em;" width="37.33" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S5.F3.pic1.3.3.3.1.1.1.1.1" style="font-size:50%;">(fan-out)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E6E6FF;" stroke="#4D4D4D" fill="#E6E6FF" stroke-width="0.6pt"><path d="M 204.51 -43.37 L 134.07 -43.37 C 131.78 -43.37 129.92 -45.23 129.92 -47.52 L 129.92 -70.59 C 129.92 -72.88 131.78 -74.74 134.07 -74.74 L 204.51 -74.74 C 206.8 -74.74 208.66 -72.88 208.66 -70.59 L 208.66 -47.52 C 208.66 -45.23 206.8 -43.37 204.51 -43.37 Z M 129.92 -74.74"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 137.13 -68.4)"><g transform="matrix(1 0 0 -1 0 20.42)"><g transform="matrix(1 0 0 1 0 13.35)"><g transform="matrix(1 0 0 -1 0 0)"><g transform="matrix(1 0 0 -1 0 13.35)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 0 0)"><text transform="matrix(1 0 0 -1 0 0)">MemMachine</text></g></g> <g transform="matrix(1 0 0 1 0 13.35)"><g transform="matrix(1 0 0 -1 17.8 0)"><text transform="matrix(1 0 0 -1 0 0)">Agent</text></g></g></g></g></g> <g transform="matrix(1 0 0 1 0 20.42)"><g transform="matrix(1 0 0 -1 16.46 0)"><foreignObject style="--ltx-fo-width:3.34em;--ltx-fo-height:0.55em;--ltx-fo-depth:0.18em;" width="31.42" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S5.F3.pic1.4.4.4.1.1.1.1.1" style="font-size:50%;">(direct)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#4D4D4D;--ltx-fill-color:#E0FFE0;" stroke="#4D4D4D" fill="#E0FFE0" stroke-width="0.6pt"><path d="M 146.45 -105.73 L 22.84 -105.73 C 20.55 -105.73 18.69 -107.59 18.69 -109.89 L 18.69 -126.34 C 18.69 -128.63 20.55 -130.49 22.84 -130.49 L 146.45 -130.49 C 148.74 -130.49 150.6 -128.63 150.6 -126.34 L 150.6 -109.89 C 150.6 -107.59 148.74 -105.73 146.45 -105.73 Z M 18.69 -130.49"></path></g><g style="--ltx-stroke-color:#000000;--ltx-fill-color:#000000;" stroke-width="0.6pt" fill="#000000" stroke="#000000" transform="matrix(1.0 0.0 0.0 1.0 23.3 -124.14)"><g transform="matrix(1 0 0 -1 0 13.8)"><g transform="matrix(1 0 0 1 0 6.73)"><g transform="matrix(1 0 0 -1 7.28 0)"><text transform="matrix(1 0 0 -1 0 0)">DeclarativeMemory</text></g></g> <g transform="matrix(1 0 0 1 0 13.8)"><g transform="matrix(1 0 0 -1 0 0)"><foreignObject style="--ltx-fo-width:11.77em;--ltx-fo-height:0.49em;--ltx-fo-depth:0.16em;" width="123.52" height="6.92" transform="matrix(1 0 0 -1 0 5.19)" overflow="visible"><span id="S5.F3.pic1.5.5.5.1.1.1.1.1" style="font-size:50%;">(vector search + reranker)</span></foreignObject></g></g></g></g> <g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 84.65 -12.86 L 84.65 -20.73 L 0 -20.73 L 0 -37.43"></path><g transform="matrix(0.0 -1.0 1.0 0.0 0 -34.93)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 84.65 -12.86 L 84.65 -37.43"></path><g transform="matrix(0.0 -1.0 1.0 0.0 84.65 -34.93)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 84.65 -12.86 L 84.65 -20.73 L 169.29 -20.73 L 169.29 -38.37"></path><g transform="matrix(0.0 -1.0 1.0 0.0 169.29 -35.87)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 0 -76.1 L 0 -83.97 L 64.96 -83.97 L 64.96 -100.74"></path><g transform="matrix(0.0 -1.0 1.0 0.0 64.96 -98.23)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 84.65 -76.1 L 84.65 -100.74"></path><g transform="matrix(0.0 -1.0 1.0 0.0 84.65 -98.23)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#595959;--ltx-fill-color:#595959;--ltx-fg-color:#595959;" stroke-width="0.8pt" fill="#595959" stroke="#595959" color="#595959"><path style="fill:none" d="M 169.29 -75.16 L 169.29 -83.03 L 104.33 -83.03 L 104.33 -100.74"></path><g transform="matrix(0.0 -1.0 1.0 0.0 104.33 -98.23)" stroke-dasharray="none" stroke-dashoffset="0.0pt" stroke-linejoin="miter"><path d="M 5.61 0 L 1.79 1.41 L 2.78 0 L 1.79 -1.41 Z"></path></g></g><g style="--ltx-stroke-color:#666666;--ltx-fill-color:#666666;" stroke-width="0.4pt" fill="#666666" stroke="#666666" transform="matrix(1.0 0.0 0.0 1.0 53.38 -23.38)"><foreignObject style="--ltx-fg-color:#666666;--ltx-fo-width:8.84em;--ltx-fo-height:0.68em;--ltx-fo-depth:0.19em;" width="62.53" height="6.15" transform="matrix(1 0 0 -1 0 4.8)" overflow="visible" color="#666666"><span id="S5.F3.pic1.6.6.6.1.1" style="font-size:50%;--ltx-fg-color:#666666;">routes to exactly one</span></foreignObject></g></g></svg>

Figure 3: Retrieval Agent tool tree. The ToolSelectAgent classifies each query and routes it to one of three strategies. All strategies ultimately delegate to the same declarative memory search, ensuring that index and reranker improvements propagate automatically.

Design principles. All three strategy nodes delegate to the same MemMachine leaf, ensuring that improvements to the underlying vector search propagate automatically to all strategies. The tree is constructed once at startup and cached; routing decisions are made per-query at inference time. Agent mode is enabled via a single flag (agent\_mode=true), with zero behavioral change to existing callers. Each node exposes advisory cost properties (accuracy\_score, token\_cost, time\_cost) for future budget-aware routing.

### 5.3 Query Routing

The ToolSelectAgent (root node) uses a single LLM call to classify each incoming query into one of three structural types:

- Multi-hop dependency chain: Two or more sequentially dependent retrieval steps where a later step requires the result of an earlier one. Routed to ChainOfQuery.
- Single-hop multi-entity: Multiple independent subjects answerable via parallel lookups with no inter-dependency. Routed to SplitQuery.
- Single-hop direct: Single subject, single lookup, no decomposition needed. Routed to MemMachine (baseline search with only the routing overhead).

The classification prompt uses embedded calibration examples and a tie-breaker rule: if any explicit dependency chain exists, classify as multi-hop even if multiple entities appear. This conservative bias trades extra LLM calls for higher recall completeness.

We further tuned Retrieval Agent prompts using the APO (Auto Prompt Optimization) algorithm from Agent Lightning [^18], using the Microsoft APO implementation <sup>3</sup>. In our internal ablations, tuning only the final answer prompt improved accuracy by approximately 4% (with baseline prompt quality also improving), while jointly tuning all agent prompts improved accuracy by approximately 6%. We do not perform live tuning at inference time, so these gains add no runtime token or latency overhead.

### 5.4 Strategy Details

ChainOfQuery implements iterative evidence accumulation for dependency chains. It executes up to 3 iterations, each consisting of: (1) retrieval against the current query, (2) a combined sufficiency judgment and query rewrite via a single LLM call, and (3) evidence accumulation. The sufficiency prompt enforces evidence-only judgment (no external knowledge), strict completeness standards, entity grounding (rewrites use only entities present in retrieved evidence), and calibrated confidence scoring with early stopping at $\geq 0.8$ confidence. This design, grounded in the prompt engineering methodology of Luo et al. [^18], formalizes forward-chaining multi-hop reasoning with bounded cost.

SplitQuery addresses fan-out queries by decomposing them into 2–6 independent sub-queries via a single LLM call, executing all sub-queries concurrently via asyncio.gather(), and pooling the results. The decomposition prompt enforces structural constraints: sub-queries must each be answerable by a single fact lookup, derived operations (compare, rank, difference) are prohibited, and a conservative tie-breaker defaults to no-split when ambiguous.

MemMachine is the direct retrieval leaf that calls DeclarativeMemory.search\_scored() without any query transformation. It serves both as the leaf primitive for other agents’ child calls and as the strategy for simple single-hop queries, where agent mode incurs only one routing LLM call overhead.

### 5.5 Multi-Query Reranking

A key innovation in agent mode is multi-query reranking: the final reranker receives a concatenation of *all* queries used during retrieval (original query plus all rewrites or sub-queries), not just the original. This ensures that episodes relevant to any step in the retrieval chain—including intermediate facts that are critical for multi-hop reasoning but not directly referenced in the original query—score well in the final ranking.

### 5.6 Benchmark Results

We evaluate the Retrieval Agent across five benchmarks, comparing three modes: Baseline (LLM with full context, no memory), MemMachine (declarative memory search), and Retrieval Agent (agent-orchestrated search). Table 3 summarizes accuracy and recall across all benchmarks.

Table 3: Retrieval Agent benchmark results across five datasets. Accuracy is LLM-judge score; Recall measures gold supporting fact retrieval. Best result per benchmark in bold. All MemMachine and Agent results use surrounding episodes enabled unless noted.

<table><tbody><tr><th>Benchmark</th><th>Questions</th><td>Answer LLM</td><td colspan="2">MemMachine</td><td colspan="2">Retrieval Agent</td><td>Baseline</td></tr><tr><th></th><th></th><td></td><td>Acc.</td><td>Recall</td><td>Acc.</td><td>Recall</td><td>Acc.</td></tr><tr><th>LoCoMo</th><th>1,540</th><td>gpt-5-mini</td><td>90.5%</td><td>82.2%</td><td>90.2%</td><td>82.5%</td><td>91.7%</td></tr><tr><th>WikiMultiHop</th><th>500</th><td>gpt-4.1-mini</td><td>88.8%</td><td>90.8%</td><td>90.0%</td><td>92.5%</td><td>96.7%</td></tr><tr><th>WikiMultiHop <sup>†</sup></th><th>500</th><td>gpt-5-mini</td><td>87.4%</td><td>91.7%</td><td>92.6%</td><td>83.3%</td><td>96.7%</td></tr><tr><th>MRCR</th><th>300</th><td>gpt-5.2</td><td>79.6%</td><td>99.1%</td><td>81.4%</td><td>99.4%</td><td>32.3%</td></tr><tr><th>EpBench</th><th>546</th><td>gpt-5-mini</td><td>73.4%</td><td>66.1%</td><td>71.8%</td><td>65.3%</td><td>77.5%</td></tr><tr><th>EpBench</th><th>546</th><td>gpt-4o-mini</td><td>71.4%</td><td>67.9%</td><td>73.3%</td><td>69.7%</td><td>50.1%</td></tr><tr><th>HotpotQA</th><th>500</th><td>gpt-5-mini</td><td>91.2%</td><td>91.0%</td><td>93.2%</td><td>95.5%</td><td>93.0%</td></tr></tbody><tfoot><tr><th colspan="8"><sup>†</sup> WikiMultiHop fully randomized cross-question noise injection; all others with content in order.</th></tr></tfoot></table>

HotpotQA provides the clearest demonstration of the Retrieval Agent’s value. On the hard validation set (500 questions), the agent achieves 93.2% overall accuracy and 92.31% gold-supporting-fact recall, compared to 91.2% accuracy and 90.98% recall for baseline MemMachine—a +2.0 and +1.3 percentage point improvement respectively. The per-tool breakdown (Table 4) shows that ChainOfQuery achieves the highest recall (95.31%) on multi-hop bridge questions, validating the iterative evidence accumulation strategy.

Table 4: HotpotQA hard set: per-tool performance breakdown for the Retrieval Agent (n=500, gpt-5-mini).

| Tool | Questions | Accuracy | Recall |
| --- | --- | --- | --- |
| MemMachine | 201 | 93.53% | 89.31% |
| SplitQuery | 118 | 94.07% | 92.83% |
| ChainOfQuery | 181 | 92.27% | 95.31% |
| Overall (Agent) | 500 | 93.20% | 92.31% |

WikiMultiHop demonstrates the benefit of agent orchestration under realistic noise conditions. When all question contexts are pooled into a single shared episodic store with fully randomized ordering—simulating a production setting where relevant and irrelevant memories are interleaved—the Retrieval Agent with gpt-5-mini achieves 92.6% accuracy vs. 87.4% for baseline MemMachine, a +5.2 point improvement.

MRCR (Multi-Round Co-reference Resolution) shows consistent agent improvement: 81.4% vs. 79.6% for MemMachine, with near-perfect recall (99.4%). Notably, the LLM baseline without memory scores only 32.3%, demonstrating that co-reference resolution fundamentally requires memory retrieval.

LoCoMo shows comparable performance between MemMachine (90.5%) and the Retrieval Agent (90.2%). This is expected: LoCoMo is predominantly single-hop conversational questions where baseline vector search is already effective, and the agent’s routing overhead provides minimal benefit.

EpBench results are mixed and benchmark-dependent. With gpt-4o-mini as the answer model, the Retrieval Agent improves over baseline MemMachine (73.3% vs. 71.4%). With gpt-5-mini, baseline MemMachine slightly outperforms (73.4% vs. 71.8%), suggesting model-prompt sensitivity.

### 5.7 Token Cost Analysis

The Retrieval Agent’s improved recall comes at the cost of additional LLM calls for routing and strategy execution. Table 5 shows the per-strategy token cost on HotpotQA.

Table 5: Average token cost per question by Retrieval Agent strategy (HotpotQA hard set).

| Component | Input Tokens | Output Tokens |
| --- | --- | --- |
| ToolSelect (router) | 1,049 | 195 |
| ChainOfQuery | 2,874 | 1,614 |
| SplitQuery | 1,229 | 435 |
| MemMachine | 0 | 0 |

For the 36% of queries routed directly to MemMachine, the total agent overhead is only the routing call ($\sim$ 1,244 tokens). For multi-hop queries routed to ChainOfQuery, total cost reaches $\sim$ 5,732 tokens per question—substantially more, but bounded by the 3-iteration limit. This bounded cost profile is a deliberate improvement over the predecessor unbounded agent loop (OpenAI Agents SDK with max\_turns=30), which was retired in favor of architecturally-defined retrieval strategies.

### 5.8 When to Use Agent Mode

Agent mode is not universally beneficial. Table 6 provides deployment guidance based on query characteristics.

Table 6: Decision guidance for enabling agent mode.

| Use Agent Mode | When… |
| --- | --- |
| Best fit | Queries involve multi-hop reasoning, co-reference resolution, or multi-entity fan-out. Accuracy is prioritized over latency. Use cases include research assistants, compliance review, and complex QA. |
| Not needed | Queries are predominantly single-hop factual lookups. Latency requirements are strict ($<$ 200ms). Token budget is constrained. Use cases include simple chatbot recall, preference lookup, and session context. |

The system is designed for seamless coexistence: agent mode is enabled per-query via a single flag, and the router itself filters simple queries to the zero-overhead direct path. In production, applications can enable agent mode selectively based on query complexity heuristics or always-on with acceptable overhead for the majority of single-hop queries that route directly.

### 5.9 OpenClaw Integration

The Retrieval Agent is also available through OpenClaw <sup>4</sup>, an open-source AI agent framework. The MemMachine OpenClaw integration is implemented as a standard plugin using the OpenClaw Plugin SDK (openclaw/plugin-sdk), not OpenClaw “agent mode.” Concretely, the plugin imports SDK types and exposes the canonical plugin object with register(api: OpenClawPluginApi), where lifecycle hooks and tool registrations connect MemMachine capabilities to the host application. Through this plugin interface, applications can use both declarative memory search and Retrieval Agent orchestration via a unified tool surface. Benchmark results in Table 3 include OpenClaw-based evaluation configurations, demonstrating that the Retrieval Agent’s benefits transfer across agent frameworks—not just MemMachine’s native evaluation harness.

## 6 LLM Integration and Model Impact

### 6.1 How LLMs Are Used in MemMachine

A distinguishing design principle of MemMachine is that LLMs are used sparingly and strategically, rather than for every memory operation. Specifically, LLMs serve three functions:

1. STM Summarization: When the short-term memory window overflows, an LLM generates a compressed summary of the session context.
2. Profile Extraction: An LLM extracts structured user facts and preferences from conversational data for profile memory.
3. Agent-Mode Inference: When operating in agent mode, the eval-LLM can iteratively query MemMachine’s memory as a tool to formulate responses.

Critically, LLMs are *not* used for per-message fact extraction, memory deduplication, or routine memory management—operations that in competing systems account for the majority of LLM token consumption.

### 6.2 Impact of Model Choice on Performance

The choice of LLM significantly affects both benchmark performance and operational cost. Table 7 summarizes the impact of eval-LLM selection on LoCoMo scores.

Table 7: Impact of eval-LLM on MemMachine v0.2 LoCoMo scores.

| Configuration | LLM Score | Mode |
| --- | --- | --- |
| gpt-4.1-mini (agent) | 0.9169 | Agent |
| gpt-4.1-mini (memory) | 0.9123 | Memory |
| gpt-4o-mini (agent) | 0.8812 | Agent |
| gpt-4o-mini (memory) | 0.8747 | Memory |

The transition from gpt-4o-mini to gpt-4.1-mini yields a 3–4 percentage point improvement across both modes, demonstrating that newer LLM generations improve memory-augmented reasoning without any changes to the memory system itself. This also suggests that MemMachine’s architecture is *LLM-agnostic* —performance improvements in the underlying model translate directly to improved memory-augmented agent behavior.

### 6.3 Cost Considerations

Token usage is a primary cost driver for LLM-based applications. MemMachine’s architecture substantially reduces token consumption:

Table 8: Token usage comparison on LoCoMo (gpt-4.1-mini).

| System | Input Tokens | Output Tokens |
| --- | --- | --- |
| MemMachine v0.2 (memory) | 4.20M | 43,169 |
| MemMachine v0.2 (agent) | 8.57M | 93,210 |
| Mem0 main/HEAD (memory) | 19.21M | 14,840 |

MemMachine uses approximately 78% fewer input tokens than Mem0 in memory mode, translating directly to lower inference cost and reduced time-to-first-token latency.

### 6.4 Context Window Considerations

A natural question is whether memory systems provide benefit when conversational content fits entirely within the LLM’s context window. Evidence from the LoCoMo benchmark suggests that even for conversations within context window limits (16K–26K tokens), memory-augmented systems outperform raw full-context baselines [^6]. This is because:

- Full-context approaches suffer from the “lost in the middle” effect [^13], where information in the middle of long contexts is poorly attended.
- Memory systems provide *selective retrieval*, surfacing only the most relevant episodes rather than overwhelming the model with full conversation history.
- As conversations grow beyond context limits, memory systems become essential rather than merely beneficial.

## 7 Experimental Setup

### 7.1 Benchmarks

We evaluate MemMachine on the following benchmarks:

LoCoMo [^6]: Evaluates very long-term conversational memory across four question categories: single-hop (841 questions), multi-hop (282), temporal reasoning (321), and open-domain (96). Total: 1,540 scored questions (the 446 adversarial questions are excluded from scoring per standard practice). The evaluation code is based on Mem0’s published evaluation framework.<sup>5</sup>

LongMemEval <sub>S</sub> [^7]: Benchmarks five core long-term memory abilities—single-session information extraction (user-stated facts, assistant-stated facts, and preference inference), temporal reasoning, knowledge updates, and multi-session reasoning—using 500 curated questions embedded in chat histories of approximately 115k tokens each. We ingest the benchmark’s chat histories session-by-session, then answer each question using MemMachine’s memory search API. Evaluation uses the question-specific judge prompts provided by the LongMemEval framework. We conduct a systematic ablation study across 12 configurations varying six optimization dimensions.

### 7.2 Evaluation Metrics

For LoCoMo, we report three metrics:

- LLM Judge Score (llm\_score): A binary score (0 or 1) assigned by a judge-LLM comparing the system’s answer to ground truth. The overall score is the weighted mean across categories.
- BLEU Score: $n$ -gram overlap with reference answers.
- F1 Score: Token-level precision and recall against reference answers.

The primary metric for comparison is the llm\_score, as it best captures semantic equivalence between generated and reference answers.

For LongMemEval <sub>S</sub>, we report the llm\_score per question category and overall, using the benchmark’s standard LLM-judge evaluation with GPT-4o-mini as judge.

### 7.3 System Environment

Table 9: Benchmark test environment.

| Component | Specification |
| --- | --- |
| Operating System | Ubuntu 24.04 LTS |
| CPU | 8 vCPUs |
| RAM | 16 GiB |
| GPU | Not required (CPU-only runs) |
| Python Version | 3.11 |
| MemMachine Version | v0.3.x |
| Database | PostgreSQL + Neo4j |
| Embedding Model | OpenAI text-embedding-3-small |
| Reranker | AWS Cohere rerank-v3-5:0 |
| Eval-LLM | OpenAI gpt-4o-mini / gpt-4.1-mini / gpt-5 / gpt-5-mini |
| Judge-LLM | OpenAI gpt-4o-mini |

### 7.4 Compared Systems

We compare MemMachine against the following systems using publicly reported results:

- Mem0 [^4]: Tested with Mem0 main/HEAD and re-run with gpt-4.1-mini for fair comparison.
- Zep [^5]: Results sourced from Zep’s published evaluation.
- Memobase: Results sourced from Memobase’s published benchmark.
- LangMem: Results from Mem0’s comparative evaluation.
- OpenAI baseline: ChatGPT’s native memory.

### 7.5 Reproducibility

All benchmark scripts, configuration files, and run instructions are available in the MemMachine repository under evaluation/.<sup>6</sup> For reproducible reporting, we recommend pinning a repository tag or commit hash, recording model versions and API provider settings, and saving raw per-question outputs used for score aggregation. Researchers can reproduce our results with their own hardware and API keys.

## 8 Results and Analysis

### 8.1 LoCoMo Benchmark Results

Table 10 presents the comprehensive LoCoMo results for MemMachine v0.2 across both LLM configurations and both operating modes.

Table 10: MemMachine v0.2 LoCoMo results by category (LLM Judge Score).

| Eval-LLM | Mode | Multi-hop | Temporal | Open-domain | Single-hop | Overall |
| --- | --- | --- | --- | --- | --- | --- |
| gpt-4.1-mini | Agent | 0.8830 | 0.9159 | 0.7188 | 0.9512 | 0.9169 |
| gpt-4.1-mini | Memory | 0.8972 | 0.8910 | 0.7500 | 0.9441 | 0.9123 |
| gpt-4o-mini | Agent | 0.8404 | 0.8069 | 0.7396 | 0.9394 | 0.8812 |
| gpt-4o-mini | Memory | 0.8759 | 0.7352 | 0.7083 | 0.9465 | 0.8747 |

### 8.2 Comparative Analysis

Table 11 compares MemMachine against competing systems on LoCoMo.

Table 11: LoCoMo benchmark comparison across AI agent memory systems (LLM Judge Score). MemMachine results are with gpt-4o-mini for fair comparison with published baselines; gpt-4.1-mini results shown separately in Table 10.

| System | Single-hop | Temporal | Multi-hop | Open-domain | Overall |
| --- | --- | --- | --- | --- | --- |
| MemMachine v0.2 | 0.9465 | 0.7352 | 0.8759 | 0.7083 | 0.8747 |
| Memobase (v0.0.37) | 0.7092 | 0.8505 | 0.4688 | 0.7717 | 0.7578 |
| Zep | 0.7411 | 0.7979 | 0.6604 | 0.6771 | 0.7514 |
| Mem0 | 0.6713 | 0.5551 | 0.5115 | 0.7293 | 0.6688 |
| LangMem | 0.6223 | 0.2343 | 0.4792 | 0.7112 | 0.5810 |
| OpenAI | 0.6379 | 0.2171 | 0.4292 | 0.6229 | 0.5290 |

In our LoCoMo comparison setting, MemMachine achieves the highest overall score by +9.7 points over the next-best system (Memobase). Key observations:

- Single-hop (0.9465): MemMachine’s sentence-level indexing and ground truth preservation enable exceptional factual recall.
- Multi-hop (0.8759): The contextualization mechanism allows linking related information across sessions.
- Temporal (0.7352): Competitive but trailing Memobase (0.8505), suggesting room for improvement in temporal reasoning—likely addressable through enhanced timestamp-aware retrieval.
- Open-domain (0.7083): Strong performance considering that episodic memory is optimized for user-centric rather than world-knowledge queries.

With gpt-4.1-mini, MemMachine’s temporal score improves to 0.9159 in agent mode, suggesting that eval-model capability is a major factor in temporal reasoning outcomes.

### 8.3 Efficiency Analysis

Beyond accuracy, MemMachine demonstrates substantial efficiency advantages:

- Token Reduction: $\sim$ 80% fewer input tokens than Mem0, directly reducing API costs.
- Memory Add Speed: $\sim$ 75% faster than previous versions, enabling real-time ingestion.
- Search Speed: Up to 75% faster search operations, reducing end-to-end response latency.

### 8.4 LongMemEvalS Ablation Study

We evaluate MemMachine on the full LongMemEval <sub>S</sub> benchmark ($n=500$ questions) through a systematic ablation study across six optimization dimensions: sentence chunking, user-query bias correction, context formatting, retrieval depth ($k$), search prompt design, and answer-model selection. Each dimension is evaluated by comparing configuration pairs that differ in exactly one variable. Table 12 summarizes the key configurations; Table 13 isolates the contribution of each optimization.

Table 12: LongMemEval <sub>S</sub> configuration matrix ($n=500$ questions per run). “Chunk” = sentence-level chunking enabled; “User-Q” = user-role query prefix; “JSON-str” = structured message formatting; “Edwin{1,3}” = search prompt variants of increasing refinement.

| ID | Answer LLM | Chunk | User-Q | JSON-str | Prompt | top\_ $k$ | LLM Score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C5 | GPT-5 | — | — | ✓ | Edwin1 | 20 | 0.855 |
| C6 | GPT-5 | — | ✓ | ✓ | Edwin1 | 20 | 0.870 |
| C7 | GPT-5 | — | ✓ | ✓ | Edwin1 | 30 | 0.912 |
| C8 | GPT-5 | — | ✓ | ✓ | Edwin1 | 50 | 0.890 |
| C9 | GPT-5 | ✓ | ✓ | ✓ | Edwin1 | 20 | 0.878 |
| C11 | GPT-5 | ✓ | ✓ | ✓ | Edwin3 | 20 | 0.896 |
| C12 | GPT-5-mini | ✓ | ✓ | ✓ | Edwin3 | 20 | 0.922 |
| C13 | GPT-5-mini | ✓ | ✓ | ✓ | Edwin3 | 30 | 0.916 |
| C14 | GPT-5-mini | ✓ | ✓ | ✓ | Edwin3 | 50 | 0.928 |
| C15 | GPT-5-mini | ✓ | ✓ | ✓ | Edwin3 | 100 | 0.930 |
| C16 | GPT-5 | ✓ | ✓ | ✓ | Edwin3 | 30 | 0.902 |
| C17 | GPT-5 | ✓ | ✓ | ✓ | Edwin3 | 50 | 0.914 |

Table 13: LongMemEval <sub>S</sub> ablation: contribution of each optimization to overall LLM score, measured by comparing configuration pairs that differ in one variable.

<table><tbody><tr><th>Optimization</th><td>Comparison</td><td><math><semantics><mi>Δ</mi> <annotation>\Delta</annotation></semantics></math> Score</td></tr><tr><th colspan="3"><em>Retrieval-stage optimizations</em></th></tr><tr><th>Retrieval depth (<math><semantics><mi>k</mi> <annotation>k</annotation></semantics></math>: 20 <math><semantics><mo>→</mo> <annotation>\to</annotation></semantics></math> 30)</th><td>C6 vs. C7</td><td>+4.2%</td></tr><tr><th>Context formatting (JSON-str)</th><td>C4 vs. C5</td><td>+2.0%</td></tr><tr><th>Search prompt (Edwin1 <math><semantics><mo>→</mo> <annotation>\to</annotation></semantics></math> 3)</th><td>C9 vs. C11</td><td>+1.8%</td></tr><tr><th>COT <math><semantics><mo>→</mo> <annotation>\to</annotation></semantics></math> simple prompt (GPT-5)</th><td>C1 vs. C4</td><td>+1.6%</td></tr><tr><th>User-query bias correction</th><td>C5 vs. C6</td><td>+1.4%</td></tr><tr><th colspan="3"><em>Ingestion-stage optimization</em></th></tr><tr><th>Sentence chunking</th><td>C6 vs. C9</td><td>+0.8%</td></tr><tr><th colspan="3"><em>Model selection</em></th></tr><tr><th>GPT-5 <math><semantics><mo>→</mo> <annotation>\to</annotation></semantics></math> GPT-5-mini</th><td>C11 vs. C12</td><td>+2.6%</td></tr></tbody></table>

#### 8.4.1 Retrieval Depth (kk)

The most impactful single parameter is the number of retrieved episodes. Increasing $k$ from 20 to 30 yields the largest improvement: +4.2 percentage points (C6: 0.870 $\to$ C7: 0.912). However, further increases show diminishing or negative returns: $k=50$ drops to 0.890, *worse* than $k=30$.

This non-monotonic behavior reflects a tension between recall and noise. At $k=20$, the retrieval window misses some relevant episodes, particularly for multi-hop questions requiring evidence from multiple sessions. At $k=30$, sufficient evidence is captured without overwhelming the answer LLM with distractors. At $k=50$, additional episodes introduce irrelevant context that degrades reading comprehension, consistent with the “lost in the middle” phenomenon [^13].

Notably, this $k$ -sensitivity is model-dependent. With GPT-5-mini (C12–C15), performance improves monotonically from $k=20$ (0.922) through $k=50$ (0.928) to $k=100$ (0.930), though with diminishing marginal gains. This suggests GPT-5-mini is more robust to distractor context than GPT-5, possibly due to differences in attention mechanisms or instruction-following behavior at high context lengths.

#### 8.4.2 User-Query Bias Correction

We observe that MemMachine’s search results can exhibit a bias toward retrieving assistant messages over user messages. Assistant messages are typically longer with more sentences and therefore more embedding keys, while user messages are shorter but often contain first-hand factual statements with higher informational value for recall tasks. Prepending the prefix "user:" to the search query shifts retrieval toward user messages, yielding +1.4% (C5: 0.855 $\to$ C6: 0.870).

#### 8.4.3 Context Formatting

The format in which retrieved messages are presented to the answer LLM significantly affects comprehension. A naive approach concatenating all messages with carriage returns produces a wall of text. Using \\n as line terminators *within* a message while using actual carriage returns to *separate* messages improves the LLM’s ability to parse message boundaries, yielding +2.0%.

#### 8.4.4 Sentence Chunking

MemMachine’s sentence-level chunking creates one embedding key per sentence rather than per message, producing finer-grained index entries. Enabling chunking yields +0.8% (C6: 0.870 $\to$ C9: 0.878), a modest but consistent gain. The relatively small effect suggests that sentence-level granularity primarily helps on questions where the relevant information is a single sentence embedded within a longer message.

#### 8.4.5 Search Prompt Design

We evaluate three search prompt variants (Edwin1, Edwin2, Edwin3) with increasing refinement. Edwin3 yields +1.8% over Edwin1 (C9: 0.878 $\to$ C11: 0.896), demonstrating that the framing of the search query—not just the retrieval algorithm—materially affects recall quality.

#### 8.4.6 Answer LLM Selection

A surprising finding is that GPT-5-mini outperforms GPT-5 as the answer LLM by +2.6% (C11: 0.896 $\to$ C12: 0.922). The advantage persists across retrieval depths: at $k=30$, GPT-5-mini achieves 0.916 vs. GPT-5’s 0.902; at $k=50$, 0.928 vs. 0.914. We attribute this to the interaction between prompt design and model architecture. The Edwin3 prompt is a direct, concise instruction without chain-of-thought scaffolding, which aligns with GPT-5-mini’s streamlined instruction-following. Conversely, GPT-5’s built-in reasoning may interfere when given explicit reasoning instructions. Since GPT-5-mini is also substantially cheaper per token, the best configuration is the most cost-efficient.

#### 8.4.7 Per-Category Analysis

Table 14 presents per-category scores for selected configurations.

Table 14: LongMemEval <sub>S</sub> per-category LLM scores for selected configurations ($n=500$). SSU = single-session-user, SSP = single-session-preference, SSA = single-session-assistant, TR = temporal reasoning, KU = knowledge update, MS = multi-session.

| Config | LLM | SSU | SSP | SSA | TR | KU | MS | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C5 (baseline) | GPT-5 | 0.986 | 0.700 | 1.000 | 0.798 | 0.925 | 0.797 | 0.855 |
| C6 (user-q) | GPT-5 | 0.957 | 0.667 | 0.982 | 0.850 | 0.885 | 0.835 | 0.870 |
| C7 ($k$ =30) | GPT-5 | 0.986 | 0.800 | 1.000 | 0.917 | 0.923 | 0.850 | 0.912 |
| C12 (mini,$k$ =20) | GPT-5-mini | 0.986 | 0.933 | 1.000 | 0.902 | 0.962 | 0.850 | 0.922 |
| C14 (mini,$k$ =50) | GPT-5-mini | 1.000 | 0.933 | 1.000 | 0.932 | 0.949 | 0.842 | 0.928 |
| C15 (mini,$k$ =100) | GPT-5-mini | 1.000 | 0.933 | 0.982 | 0.917 | 0.949 | 0.872 | 0.930 |

Several patterns emerge. Single-session extraction (SSU, SSA) is nearly saturated: most configurations achieve 0.98–1.00, indicating that sentence-level indexing is well-suited for recalling specific facts from individual sessions. Single-session preference (SSP) shows the most dramatic improvement, rising from 0.700 (C5) to 0.933 (C12–C15). Preference questions require inferring user preferences from indirect cues, which benefits from both better retrieval and better answer models. Temporal reasoning (TR) improves steadily with retrieval depth and prompt optimization, from 0.798 (C5) to 0.932 (C14), as retrieving more context helps establish temporal relationships. Multi-session reasoning (MS) remains the most challenging category, peaking at 0.872 (C15, $k$ =100), since synthesizing information across sessions requires the broadest retrieval window.

#### 8.4.8 Token Cost–Accuracy Tradeoff

Retrieval depth directly affects token consumption. Table 15 shows the cost profile for selected configurations.

Table 15: LongMemEval <sub>S</sub> token consumption per 500-question run. Input tokens scale with $k$; output tokens remain approximately constant.

| Config (LLM) | $k$ | Input (M) | Score |
| --- | --- | --- | --- |
| C6 (GPT-5) | 20 | 2.94 | 0.870 |
| C7 (GPT-5) | 30 | 4.03 | 0.912 |
| C8 (GPT-5) | 50 | 6.47 | 0.890 |
| C12 (GPT-5-mini) | 20 | 2.58 | 0.922 |
| C14 (GPT-5-mini) | 50 | 5.97 | 0.928 |
| C15 (GPT-5-mini) | 100 | 9.79 | 0.930 |

The Pareto-optimal configuration is C12 (GPT-5-mini, $k$ =20): it achieves 0.922 with only 2.58M input tokens, outperforming C7 (GPT-5, $k$ =30, 0.912) which requires 4.03M tokens. Reaching the peak score of 0.930 (C15) requires $3.8\times$ the input tokens of C12 for only +0.8% accuracy.

## 9 Discussion

### 9.1 Retrieval Stage Dominates Accuracy

Our LongMemEval ablation reveals that retrieval-stage optimizations contribute substantially more to final accuracy than ingestion-stage changes. The cumulative effect of retrieval-side improvements (retrieval depth: +4.2%, formatting: +2.0%, search prompt: +1.8%, COT removal: +1.6%, user-query bias: +1.4%) far exceeds the ingestion-side contribution of sentence chunking (+0.8%). This suggests that for memory systems, *how* data is recalled matters more than *how* it is stored, provided the storage preserves ground truth.

This has architectural implications: systems that invest heavily in LLM-based ingestion (extracting facts, building knowledge graphs) may be over-optimizing the wrong stage. MemMachine’s approach of storing raw data with lightweight indexing and investing in retrieval quality appears to be more effective per unit of engineering effort.

### 9.2 Model–Prompt Co-optimization

The GPT-5-mini result on LongMemEval highlights that model selection and prompt design must be co-optimized. A chain-of-thought prompt designed for GPT-4.x is suboptimal for GPT-5, and a simple direct prompt can outperform a complex one when paired with the right model. The advantage persists across retrieval depths (GPT-5-mini beats GPT-5 by +1.4% at $k$ =30 and $k$ =50). This argues against the common practice of reusing prompts across model upgrades, and suggests that memory system deployments should re-evaluate prompts whenever the underlying answer model changes.

### 9.3 The Role of Personalization

Personalization is perhaps the most compelling reason for AI agent memory. Without memory, every interaction starts from zero—the agent has no awareness of the user’s history, preferences, or context. Memory transforms a generic LLM into a personalized assistant that adapts to individual users over time.

MemMachine’s dual memory architecture directly supports personalization: episodic memory provides the factual grounding for “what happened,” while profile memory captures the distilled “who the user is.” This combination enables agents to:

- Maintain continuity across sessions without requiring users to repeat context.
- Adapt responses to user preferences, communication style, and domain expertise.
- Build trust through demonstrated recall of past interactions.
- Provide proactive suggestions based on accumulated user knowledge.

As AI agents move from novelty to daily utility, personalization through memory will become a differentiating capability. Users will expect their agents to “know” them—and memory systems like MemMachine provide the infrastructure to deliver this expectation.

### 9.4 Summary vs. Full Context vs. Compressed Observations

A recurring design question is whether to provide the LLM with a summary of past interactions, the full conversational context, or a compressed intermediate form. Our findings, together with recent work on observational memory [^15], suggest that each approach occupies a distinct point in the design space:

- Full context overwhelms the model, triggers the “lost in the middle” effect [^13], and becomes infeasible as history grows beyond context limits.
- Summary-only approaches (compaction) lose critical detail, particularly for factual and temporal queries where the exact wording or timing matters. As Mastra’s research notes, compaction produces “documentation-style summaries” that “strip out the specific decisions and tool interactions agents need.”
- Compressed observations (Mastra) offer a middle ground: event-based logs that preserve structure while achieving 3–40 $\times$ compression. This enables prompt caching and stable context windows but sacrifices the ability to retrieve original episodes on demand.
- MemMachine’s approach—STM summary *plus* selectively retrieved raw episodes—provides a different tradeoff: the summary gives high-level context, while retrieved episodes supply *uncompressed* factual grounding. This is particularly important for use cases requiring auditability, compliance, or multi-hop reasoning over exact conversational records.

The choice between these approaches depends on the deployment context. For tool-heavy agents generating large outputs (coding agents, SRE agents), compression-first approaches may be optimal. For agents serving domains where factual precision matters (healthcare, legal, financial services), ground-truth-preserving retrieval is essential. A promising future direction is hybrid architectures that combine compressed observations for high-level context with on-demand retrieval of raw episodes when precision is needed.

### 9.5 Single-Agent vs. Multi-Agent Memory

Memory benefits increase in multi-agent environments:

- Shared memory enables agents to coordinate without redundant information gathering.
- Specialized agents can deposit domain-specific knowledge that other agents retrieve, enabling emergent division of labor.
- Session continuity allows agent handoffs without context loss.
- Reduced token usage across the system, as agents share rather than regenerate context.

MemMachine’s multi-tenancy architecture (project/session isolation) naturally supports multi-agent deployments where agents share a project-level memory while maintaining session-level isolation for individual conversations.

### 9.7 Limitations and Threats to Validity

Our results should be interpreted with several limitations in mind. First, benchmark outcomes are sensitive to eval-model choice, prompt templates, and provider-side model updates; scores reported here are tied to the specific configurations listed in Section 7. Second, cross-system comparisons mix re-run results and published numbers, which may differ in preprocessing, prompt settings, or infrastructure. Third, while LoCoMo, LongMemEval <sub>S</sub>, HotpotQA, WikiMultiHop, and EpBench cover important retrieval behaviors, they do not fully represent all production workloads (for example, multilingual, multimodal, or strict real-time constraints). Fourth, token-efficiency comparisons are workload-dependent and should be treated as directional outside the reported setup. Fifth, the LongMemEval ablation treats each optimization dimension independently; interaction effects between dimensions (e.g., whether chunking benefits change at higher $k$) remain unexplored, and the ablation configurations C1–C4 used partial question subsets before being extended to the full 500-question evaluation. We therefore view these results as strong empirical evidence within the evaluated settings rather than universal performance guarantees.

### 9.8 Architectural Design Tensions

The VentureBeat analysis of emerging memory architectures [^15] identifies several key questions that enterprises should consider when selecting a memory approach. We frame these as design tensions that inform MemMachine’s positioning:

Retrieval vs. stable context. Retrieval-based systems (MemMachine, Mem0, Zep) search for relevant memories each turn, which enables access to arbitrarily large memory stores but invalidates prompt caches and adds latency. Stable-context systems (Mastra’s observational memory) keep a compressed log always in context, enabling prompt caching but capping the total memory to what fits in the context window. MemMachine’s approach provides the scalability of retrieval while its STM component ensures that recent context is always immediately available without a retrieval step.

Prompt cacheability. Modern LLM providers (OpenAI, Anthropic) offer significant discounts for cached prompt prefixes. Systems that maintain a stable prefix can exploit this for 50–90% cost reduction on cached tokens. MemMachine’s STM summary provides a semi-stable prefix, though retrieved episodes vary per query. This represents an area for future optimization—for example, caching frequently retrieved episode clusters.

Infrastructure complexity. MemMachine requires database infrastructure (PostgreSQL, Neo4j) but provides full control over data persistence and query patterns. Text-only approaches (Mastra) eliminate the need for specialized databases but may become constrained as memory volume grows. For enterprises with existing database infrastructure, MemMachine’s approach integrates naturally; for teams seeking minimal infrastructure, simpler architectures may be preferable initially.

Memory as a top-level primitive. There is growing consensus that memory is one of the essential primitives for production AI agents, alongside tool use, workflow orchestration, observability, and guardrails. MemMachine’s design as a standalone, framework-agnostic memory layer—accessible via REST API, Python SDK, and MCP—reflects this view. Agents should be able to adopt memory without being locked into a specific orchestration framework.

Table 16 summarizes the architectural tradeoffs across representative memory systems.

Table 16: Architectural design space comparison across agent memory systems.

| Property | MemMachine | Mem0 | Zep | Mastra OM | MemOS | Full Context |
| --- | --- | --- | --- | --- | --- | --- |
| Memory approach | Retrieval | Retrieval | Retrieval | In-context | Hybrid | In-context |
| Ground truth preserved | ✓ | Partial | Partial | $\times$ | Partial | ✓ |
| Prompt cacheable | Partial | $\times$ | $\times$ | ✓ | $\times$ | ✓ |
| Scales beyond context window | ✓ | ✓ | ✓ | $\times$ | ✓ | $\times$ |
| LLM calls per message | Low | High | Moderate | Moderate | High | None |
| Specialized DB required | Yes | Yes | Yes | No | Yes | No |
| Parametric/KV-cache memory | $\times$ | $\times$ | $\times$ | $\times$ | ✓ | $\times$ |
| Works with closed-source LLMs | ✓ | ✓ | ✓ | ✓ | Partial | ✓ |
| Open source | ✓ | Partial | Partial | ✓ | ✓ | N/A |

### 9.9 When Memory Helps (and When It Doesn’t)

Memory provides clear benefits for:

- Multi-session interactions (customer support, healthcare, education).
- Personalization-dependent applications (content recommendations, personal assistants).
- Complex workflows requiring state persistence (project management, CRM).
- Compliance and audit scenarios requiring interaction history.

Memory may be unnecessary or counterproductive for:

- Single-turn, stateless queries (search, translation, simple QA).
- High-volume, low-personalization tasks (batch processing, data extraction).

## 10 Future Work

Several directions merit investigation:

- Procedural memory: Extending MemMachine to store and retrieve learned action patterns, tool-use strategies, and workflow recipes.
- Enhanced temporal reasoning: Developing dedicated temporal indexing and query expansion techniques to improve performance on temporal benchmarks.
- LongMemEval <sub>M</sub> evaluation: Extending evaluation to LongMemEval <sub>M</sub> (500 sessions, $\sim$ 1.5M tokens per question), which tests memory at production scale.
- Adaptive retrieval depth: Implementing query-complexity-aware $k$ selection, informed by our finding that optimal $k$ depends on both the query type and the downstream answer model.
- Memory consolidation and forgetting: Implementing cognitive-inspired mechanisms for prioritizing frequently accessed memories and gracefully retiring stale information.
- Multi-modal memory: Supporting images, audio, and structured data alongside conversational text.
- Additional database backends: Expanding support to ChromaDB, Milvus, and other vector stores.
- Reinforcement learning integration: Using benchmark feedback to optimize retrieval strategies through learned policies.
- Retrieval Agent extensions: Expanding the agent tool tree with specialized agents for temporal reasoning, aggregation queries, and comparative analysis. Implementing budget enforcement (token cost ceilings, latency limits) with automatic fallback to cheaper strategies. Enabling per-agent LLM tier selection for cost optimization.
- Adaptive retrieval budgets: Dynamically adjusting per-sub-query retrieval limits based on query complexity estimates and accumulated evidence, reducing redundant episode retrieval in fan-out and chain-of-query strategies.
- Function-calling code mode: Investigating function-calling architectures where agents emit structured executable code (for example, Python or TypeScript) rather than invoking large predefined tool lists. Code executes in a secure interpreter that handles data processing, dynamic tool discovery, and multi-step chaining with fewer repeated LLM roundtrips. Prior reports indicate large token savings for massive toolsets (for example, 98.7% in Anthropic’s MCP code execution workflow and up to 99.9% in Cloudflare’s Code Mode) [^19] [^20]. We will evaluate both client-side and server-side variants, including dynamic directory-based schema loading and low-overhead search/execute proxy patterns.

## 11 Conclusion

We have presented MemMachine, an open-source memory system for AI agents that prioritizes ground truth preservation, cost efficiency, and personalization. Through a two-tier architecture of short-term and long-term episodic memory augmented by profile memory, MemMachine provides agents with the ability to store, recall, and reason over past experiences without the high cost and error accumulation inherent in LLM-dependent extraction approaches.

Our evaluation spans multiple benchmarks. On LoCoMo, MemMachine achieves state-of-the-art performance (0.9169 with gpt-4.1-mini) with approximately 80% fewer tokens than Mem0. On LongMemEval <sub>S</sub>, a systematic ablation across six optimization dimensions achieves 93.0% overall accuracy and reveals that retrieval-stage optimizations—particularly retrieval depth tuning (+4.2%) and context formatting (+2.0%)—dominate over ingestion-stage changes, and that smaller models (GPT-5-mini) outperform larger models (GPT-5) when co-optimized with appropriate prompts. The Retrieval Agent extends these capabilities to multi-hop queries, achieving 93.2% on HotpotQA hard and 92.6% on WikiMultiHop with randomized noise—demonstrating that MemMachine’s ground-truth-preserving architecture is composable: intelligent retrieval strategies can be layered on top without modifying the underlying storage model.

As AI agents transition from experimental technology to production infrastructure, the quality of their memory systems will determine the quality of their personalization, accuracy, and trustworthiness. MemMachine provides a foundation for this next generation of memory-augmented agents.

[^1]: Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Ion Stoica, and Joseph E. Gonzalez. MemGPT: Towards LLMs as Operating Systems. *arXiv preprint arXiv:2310.08560*, 2024.

[^2]: Joon Sung Park, Joseph C. O’Brien, Carrie J. Cai, Meredith Ringel Morris, Percy Liang, and Michael S. Bernstein. Generative Agents: Interactive Simulacra of Human Behavior. *arXiv preprint arXiv:2304.03442*, 2023.

[^3]: Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In *NeurIPS*, 2020.

[^4]: Prateek Chhikara, Dev Khant, Saket Aryan, Taranjeet Singh, and Deshraj Yadav. Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory. *arXiv preprint arXiv:2504.19413*, 2025.

[^5]: Preston Rasmussen, Pavlo Paliychuk, Travis Beauvais, Jack Ryan, and Daniel Chalef. Zep: A Temporal Knowledge Graph Architecture for Agent Memory. *arXiv preprint arXiv:2501.13956*, 2025.

[^6]: Adyasha Maharana, Dong-Ho Lee, Sergey Tulyakov, Mohit Bansal, Francesco Barbieri, and Yuwei Fang. Evaluating Very Long-Term Conversational Memory of LLM Agents. *arXiv preprint arXiv:2402.17753*, 2024.

[^7]: Di Wu, Hongwei Wang, Wenhao Yu, Yuwei Zhang, Kai-Wei Chang, and Dong Yu. LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory. *arXiv preprint arXiv:2410.10813*, 2024. Accepted at ICLR 2025.

[^8]: Alexis Huet, Zied Ben Houidi, and Dario Rossi. Episodic Memories Generation and Evaluation Benchmark for Large Language Models. In *International Conference on Learning Representations (ICLR)*, 2025.

[^9]: Yuyang Hu, Shichun Liu, Yue Yue, *et al.* Memory in the Age of AI Agents: A Survey. *arXiv preprint arXiv:2512.13564*, 2025.

[^10]: Endel Tulving. Episodic and Semantic Memory. In E. Tulving and W. Donaldson, editors, *Organization of Memory*, pages 381–403. Academic Press, 1972.

[^11]: Richard C. Atkinson and Richard M. Shiffrin. Human Memory: A Proposed System and Its Control Processes. In K. W. Spence and J. T. Spence, editors, *The Psychology of Learning and Motivation*, volume 2, pages 89–195. Academic Press, 1968.

[^12]: Tibor Kiss and Jan Strunk. Unsupervised Multilingual Sentence Boundary Detection. *Computational Linguistics*, 32(4):485–525, 2006.

[^13]: Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in the Middle: How Language Models Use Long Contexts. *Transactions of the Association for Computational Linguistics*, 12:157–173, 2024.

[^14]: Yu Wang, Chi Han, Tongtong Wu, Xiaoxin He, Wangchunshu Zhou, Nafis Sadeq, Xiusi Chen, Zexue He, Wei Wang, Gholamreza Haffari, *et al.* Towards Lifespan Cognitive Systems. *arXiv preprint arXiv:2409.13265*, 2024.

[^15]: Tyler Barnes and Sam Bhagwat. Observational Memory: A Human-Inspired Memory System for AI Agents. Mastra Technical Report, 2026. [https://mastra.ai/research](https://mastra.ai/research).

[^16]: Zhiyu Li, Chenyang Xi, Chunyu Li, Ding Chen, Boyu Chen, Shichao Song, Simin Niu, Hanyu Wang, et al. MemOS: A Memory OS for AI System. *arXiv preprint arXiv:2507.03724*, 2025.

[^17]: Zhiyu Li, Shichao Song, Hanyu Wang, Simin Niu, Ding Chen, Jiawei Yang, Chenyang Xi, et al. MemOS: An Operating System for Memory-Augmented Generation (MAG) in Large Language Models. *arXiv preprint arXiv:2505.22101*, 2025.

[^18]: Xiao Luo, Yuxuan Zhang, Zheng He, Zifeng Wang, Sixun Zhao, Dongming Li, Long K. Qiu, and Yang Yang. Agent Lightning: Train ANY AI Agents with Reinforcement Learning. *arXiv preprint arXiv:2508.03680*, 2025.

[^19]: Anthropic. Code execution with MCP. Engineering blog, 2025. [https://www.anthropic.com/engineering/code-execution-with-mcp](https://www.anthropic.com/engineering/code-execution-with-mcp).

[^20]: Cloudflare. Introducing Code Mode for MCP servers. Cloudflare blog, 2025. [https://blog.cloudflare.com/code-mode-mcp/](https://blog.cloudflare.com/code-mode-mcp/).

[^21]: Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W. Cohen, Ruslan Salakhutdinov, and Christopher D. Manning. HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. In *Proceedings of EMNLP*, 2018.