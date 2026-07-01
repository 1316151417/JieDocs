---
title: "The Algorithmic Self-Portrait: Deconstructing Memory in ChatGPT"
source: "https://arxiv.org/html/2602.01450v3"
author:
published:
created: 2026-07-01
description:
tags:
  - "clippings"
---
Abhisek Dash [0000-0002-5300-8757](https://orcid.org/0000-0002-5300-8757 "ORCID identifier") Max Planck Institute for Software SystemsKaiserslauternGermany, Soumi Das [0000-0002-6933-5744](https://orcid.org/0000-0002-6933-5744 "ORCID identifier") Max Planck Institute for Software SystemsKaiserslauternGermany, Elisabeth Kirsten [0009-0003-0680-8916](https://orcid.org/0009-0003-0680-8916 "ORCID identifier") Ruhr University BochumBochumGermany, Qinyuan Wu [0000-0002-1453-9643](https://orcid.org/0000-0002-1453-9643 "ORCID identifier") Max Planck Institute for Software SystemsKaiserslauternGermany, Sai Keerthana Karnam [0000-0003-1328-5167](https://orcid.org/0000-0003-1328-5167 "ORCID identifier") Indian Institute of Technology KharagpurKharagpurIndia, Krishna P. Gummadi [0000-0003-1256-8800](https://orcid.org/0000-0003-1256-8800 "ORCID identifier") Max Planck Institute for Software SystemsKaiserslauternGermany, Thorsten Holz [0000-0002-2783-1264](https://orcid.org/0000-0002-2783-1264 "ORCID identifier") Max Planck Institute for Security and PrivacyBochumGermany, Muhammad Bilal Zafar [0000-0001-8347-7813](https://orcid.org/0000-0001-8347-7813 "ORCID identifier") Ruhr University BochumBochumGermany and Savvas Zannettou [0000-0001-5711-1404](https://orcid.org/0000-0001-5711-1404 "ORCID identifier") Delft University of TechnologyDelftNetherlands

###### Abstract.

To enable personalized and context-aware interactions, conversational AI systems have introduced a new mechanism: Memory. Memory creates what we refer to as the Algorithmic Self-portrait—a new form of personalization derived from users’ self-disclosed information divulged within private conversations. While memory enables more coherent exchanges, the underlying processes of memory creation remain opaque, raising critical questions about data sensitivity, user agency, and the fidelity of the resulting portrait.

To bridge this research gap, we analyze 2,050 memory entries from 80 real-world ChatGPT users. Our analyses reveal three key findings: (1) a striking 96% of memories in our dataset are created unilaterally by the conversational system, potentially shifting agency away from the user; (2) Memories, in our dataset, contain a rich mix of GDPR-defined personal data (in 28% memories) along with psychological insights about participants (in 52% memories); and (3) A significant majority of the memories (84%) are directly grounded in user context, indicating faithful representation of the conversations. Finally, we introduce a framework—Attribution Shield—that anticipates these inferences, alerts about potentially sensitive memory inferences, and suggests query reformulations to protect personal information without sacrificing utility. <sup>1</sup>

Resource Availability:  
The source code of this paper has been made publicly available at [https://doi.org/10.5281/zenodo.18371252](https://doi.org/10.5281/zenodo.18371252)

## 1\. Introduction

Conversational AI systems like ChatGPT, Gemini, and Claude have become indispensable tools integrated in the daily routines of hundreds of millions of users worldwide [^12] [^29]. Their versatility has fueled this widespread adoption, with users now routinely relying on them for finding information, brainstorming ideas, and even seeking personal advice. As a result, these systems are evolving from simple chatbots into foundational platforms that mediate the interaction between society and the Web.

To meet the demands of these deep and diverse interactions, conversational systems are increasingly introducing personalization capabilities designed to improve user experience [^32] [^44] [^4]. While these personalization capabilities can improve utility by more contextually relevant and individually tailored answers, they are built upon a foundation of extensive data collection, raising long-standing concerns about privacy, security, and data governance [^46]. Furthermore, continuously adapting responses to align with a user’s stated beliefs deepens the risks of confining the user into a conversational filter bubble [^36]. These interwoven challenges—balancing utility against the dual risks of privacy intrusion and narrowed perspectives—demand a closer examination of the underlying mechanisms that enable such personalization.

Personalization in conversational AI systems using Memory: Recently, conversational AI systems like ChatGPT, Gemini, Claude have introduced a new architectural mechanism, termed memory, that allows the system to retain and recall information from past conversations, enabling more personalized and contextually coherent exchanges [^32] [^44] [^4]. The retention of information operates in two distinct modes: explicitly, through direct user commands, and implicitly, through unilateral inference by the system itself [^33]. While the explicit mode aligns with user agency, the implicit mode shifts the control to the conversational systems, raising the fundamental question about who holds the agency in shaping and curating this persistent memory on behalf of the user?

Personalization on online platforms has been a well-studied phenomenon. A substantial body of previous research has examined utilities [^10] [^47] [^8] of personalization along with concerns such as opacity, lack of user control, and sensitive inferences [^39] [^5]. However, personalization in conversational systems is important to be studied for its nuanced distinctions from traditional platforms. Traditional platforms typically mediate between content creators and consumers, whereas conversational AI systems operate as active stakeholders in the conversation. While such active participation enables the system to craft arguments, frame choices, and provide ostensible support that is tailored to users’ needs, this same ability may also exacerbate potential risks due to inherent system vulnerabilities e.g., hallucination [^22] [^41], anthropomorphism [^23] [^25], sycophancy [^43] [^34]. The gravity of these concerns is underscored by a recent spate of regulatory scrutiny and litigation targeting the practices of leading conversational AI systems [^17] [^21]. Such concerns raise another set of important questions regarding what information do these systems deem ‘worthy’ of retention in their memory for personalization and are these information captured faithfully?

Research questions (RQs): To the best of our knowledge, ours is the first study to investigate the phenomenon of memory in conversational AI systems by conceptualizing it as an algorithmic self-portrait. Algorithmic – because its creation, curation and provenance may rely on the algorithms governing the conversational AI systems, and self-portrait – because it renders the user’s self-disclosed information divulged to the AI system. To deconstruct *AI memory*, our work is guided by the following research questions:  
RQ1: Which among the two – the AI system or the user, hold greater agency in updating AI memory?

RQ2: What user information does the AI system store as memory?

RQ3: How faithfully does AI memory capture user conversations?

RQ4: Can memory inference be reverse-engineered to mitigate attribution and privacy risks for users?

To answer these questions, we analyze a subset of InVivoGPT [^25] dataset which is a collection of ChatGPT traces obtained through GDPR-based data donations. Our motivation to analyze ChatGPT traces is twofold: (1) ChatGPT is the most widely used conversational AI system [^12], and (2) it is the first to introduce memory to its conversational system. We analyze data from 80 participants (recruited from Prolific), who exercised their GDPR right of access [^15] and voluntarily donated their ChatGPT interactions. These interaction traces are organized in terms of conversations and turns. Each turn is a single $\langle$ user query, AI response $\rangle$ pair. A set of turns without any intermediate break together form a conversation. To identify the recent conversations with memory inferences, we identified the messages from the ‘bio’ tool that included the phrase model set context updated and collected the corresponding user query in the conversations. In this way, we created a data set of 1,058 conversations that contained 22,971 turns out of which 2,050 queries triggered memory updates. Our analyses reveal the following interesting observations:

(1) Only 4% (84) of the memories in our analyzed dataset are initiated by participants, while the remaining 96% are unilaterally triggered by ChatGPT. Such stark asymmetry in memory update patterns indicates superior agency of the AI system in shaping conversational memory, as opposed to user-driven control.

(2) In our analyzed dataset, 28% of the memories include personal data defined under the GDPR. Additionally, 52% of the memories contain psychological information about participants, spanning different Theory of Mind (ToM) [^6] categories. This indicates that ChatGPT may add sensitive information about users to the memory.

(3) Majority of the analyzed memories (84%) are directly grounded in user context, indicating faithful representation of conversations.

(4) Using in-context learning and fine-tuning strategies on open-source LLMs (Qwen2.5-32B-it [^40], Gemma3-27B-it [^45], and  
GPT-OSS-20B [^2]), we are able to imitate the memory extraction of ChatGPT, achieving semantic similarity of $\sim 60\%$ with the ground-truth ChatGPT memories. Our memory extractor analyses indicate that if memories were to be triggered from all queries, it would reveal even more sensitive information about participants. To mitigate this risk, we train the same models to reformulate queries asked by participants to shield their attribution to sensitive information. Our results indicate that over 94% of these reformulated queries prevent attribution, while preserving the utility (i.e., the intent– measured through semantic similarity) of the original query.

## 2\. Background and Related Work

Background. To enhance the coherence and continuity of human-AI interactions, leading AI companies have introduced personalization mechanisms that allow LLMs to retain contextual information across sessions [^32] [^44] [^4]. This feature, known as memory, enables LLMs to recall user-specific details (e.g., preferences, prior conversations, ongoing tasks, etc.) and leverage them in subsequent conversations. Memory can be formed in two ways: through *explicit* user requests, where individuals instruct the LLM to remember specific information or through *implicit* inference, where the LLM autonomously identifies potentially relevant information and stores it for future usage [^32]. Crucially, users are given control over memories, i.e., they can review, update, or delete memories [^32].

For improved user safety, OpenAI has also introduced policies to regulate memories. In OpenAI’s implementation [^31], ChatGPT’s memory is designed to store information that is useful across conversations and relevant for personalization, such as user preferences, recurring tasks, or facts the user explicitly asks to be remembered. In contrast, it is not allowed to store overly personal details, short-lived facts, trivial information, or sensitive data (e.g., race, religion, health information, etc.) unless the user explicitly requests it.

Personalization. Long before memory-equipped LLMs, personalization on the Web was primarily achieved through user profiling, where platforms collected and analyzed behavioral data to infer interests, preferences, and demographics [^14] [^19]. A substantial body of previous research has examined how such profiling underpinned targeted advertising [^10] [^7] [^3], recommendation systems [^30] [^47] [^13] [^8] [^1]. In this context, researchers have repeatedly raised concerns about opacity, lack of user control, and the use of sensitive or inferred attributes [^39] [^5]. In contrast, the introduction of persistent memory in LLMs opens the door to entirely new forms of personalization that are based not only on behavioral traces but also on signals embedded in private conversations. Our work addresses this important and timely knowledge gap.

Data Access. A central challenge in studying user profiling and personalization lies in obtaining reliable, accurate, and comprehensive data about what the platform knows about their users. Such data are typically locked away in proprietary systems, which makes independent auditing and scientific study difficult. To address these critical data access barriers, researchers have increasingly turned to the concept of GDPR-based data donations [^9] [^48] [^49] [^20] [^24]. In essence, users of online platforms can exercise their GDPR “right of access by the data subject” [^15], which empowers them to request and obtain a copy of personal data that platforms store and process about them. By voluntarily donating these datasets, users empower researchers with user-centric perspectives on the inner workings of online platforms, enabling scientific investigations that would otherwise remain impossible. Building on this paradigm, our work explores how data donations can be applied to study personalization in large-scale conversational AI systems like ChatGPT.

## 3\. Dataset for Memory Analyses

Table 1. Distribution of participants demographics.

<table><tbody><tr><td>Attribute</td><td>Type</td><td>Count</td><td>Percentage</td></tr><tr><td rowspan="3">Gender</td><td>Female</td><td>21</td><td>26.2</td></tr><tr><td>Male</td><td>58</td><td>72.5</td></tr><tr><td>Prefer not to say</td><td>1</td><td>1.2</td></tr><tr><td rowspan="5">Age</td><td>18–24</td><td>19</td><td>23.8</td></tr><tr><td>25–34</td><td>34</td><td>42.5</td></tr><tr><td>35–44</td><td>12</td><td>15.0</td></tr><tr><td>45–64</td><td>13</td><td>16.25</td></tr><tr><td>65+</td><td>2</td><td>2.5</td></tr><tr><td rowspan="7">Country</td><td>USA</td><td>27</td><td>33.8</td></tr><tr><td>Germany</td><td>14</td><td>17.5</td></tr><tr><td>Italy</td><td>14</td><td>17.5</td></tr><tr><td>France</td><td>10</td><td>12.5</td></tr><tr><td>Spain</td><td>10</td><td>12.5</td></tr><tr><td>Others</td><td>5</td><td>6.2</td></tr></tbody></table>

We analyze a specific subset of InVivoGPT dataset [^25]. Curation of this dataset builds upon the emerging paradigm of GDPR-empowered data donations [^49] [^24] [^48]. Under Article 15(3) of the GDPR [^15], users have the right to obtain a personal copy of all their data processed by online platforms. In InVivoGPT, participants exercised their GDPR rights to obtain their ChatGPT interaction histories, which they subsequently donated for research purposes. Readers can find more details about the data collection procedure in the paper cited herewith [^25].

Demographic of participants: In InVivoGPT, participants were recruited from Prolific crowdsourcing platform [^38] who self-reported to regularly use ChatGPT. They were required to have at least 100 conversations with the conversational system and maintain at least 90 days of active usage. In this paper, we analyze data of $80$ participants in InVivoGPT, who primarily are from the United States (33.75%), and Europe (62.5%). Table 1 reports detailed participants’ demographics.

Conversation traces in InVivoGPT: The data provided by the ChatGPT includes files containing conversations (user inputs, ChatGPT responses, and associated metadata such as conversation ID, message ID, creation time, model used etc., status of the response, and content type), shared conversations (list of conversations shared with others), message feedback (list of model responses rated by the user) etc. For the purpose of this work, we focus on the conversations data between participants and ChatGPT. These conversation traces are organized in terms of conversations and turns. Each turn is a single $\langle$ user query, AI response $\rangle$ pair. A set of turns without any intermediate break together form a conversation.

Memory entry identification: To effectively respond to various user prompts, ChatGPT is equipped with different external tools (e.g., image\_gen, python, automation, file\_search, etc.). Among the external tools used by ChatGPT for effective conversations, the bio tool is responsible for storing, updating, or deleting memory entries that may be useful in future interactions. To identify all memory entries, we searched for the entries of the bio tool that have the content ‘model set context updated’. Using its ‘parent’ attribute, we then traced back to find the corresponding GPT message that invoked the tool, as well as immediately preceding user message that triggered the memory update. These messages triggered a memory update and the associated GPT message to the tool are the memory entries that got stored in the bio tool for the account.

This process resulted in a total of $2,050$ memory entries. These memories were triggered in the context of $1,058$ different conversations across $65$ (out of $80$) participants. These $1,058$ conversations contain a total of $22,971$ queries/prompts. In the remainder of this paper, we focus on different aspects of these memory entries to understand what they contain, their provenance, and whether we can imitate this memory generation for mitigating attribution risks.

## 4\. User Agency and Sensitivity of Memories

In this section, we investigate how closely the memory feature in ChatGPT aligns with OpenAI’s stated policies about user agency and retention of sensitive information.

![Refer to caption](https://arxiv.org/html/2602.01450v3/x1.png)

(a) Memory creation

### 4.1. Agency of Memory Update

As per OpenAI’s documentation [^33], memories are details which the users have explicitly asked ChatGPT to remember, indicating users have the agency to decide what gets stored in the memory. However, the same documentation also describes an implicit mode of remembering (see Figure˜6(a) in Appendix A): ‘If you share information that might be useful for future conversations, ChatGPT may save those details as a memory without you needing to ask.’ In Figure˜6(b) (in Appendix A), we show an example of a memory being saved without the user explicitly asking for saving it. Such dichotomy may lead to gaps between user expectation and actual system behavior having privacy implications.

To understand whether memory updates are primarily initiated by users or by ChatGPT, we identify explicit linguistic patterns that signal memory-related operations. We first implement a regex-based classification to detect linguistic patterns that explicitly signal memory intent in user messages, using trigger terms such as remember, note that, store, save, add to memory, and forget. Out of the $2,050$ memory instances, only $4\%$ $(n=84)$ include an explicit request to perform a memory operation (see Figure˜1). Consequently, $96\%$ of all memory entries are unilaterally initiated by ChatGPT, *without* a detected direct command from participants.

These practices are consistent with OpenAI’s policy, which permits the system to store information characterized as “useful”. However, our observations indicate a gap between the policy’s emphasis on user involvement and the operationalization of initiating memory updates. In practice, the decision to create or modify a memory is predominantly determined by system-level mechanisms rather than explicit user actions. As a result, user influence over memory formation is mediated primarily through interaction content rather than direct control over update events.

### 4.2. Remembering Sensitive Information

ChatGPT’s disproportionate agency to save memories raises important privacy and safety considerations, especially concerning what kind of information about users is being stored. OpenAI’s documentation indicates that the system is trained not to proactively remember sensitive information unless explicitly asked [^33] [^31] (see Figure˜6(c) in Appendix A).

To assess the current operationalization practice on sensitive user data, we utilize GDPR’s [^15] definitions of personal data (Article 4(1)) and special category personal data (Article 9(1)) to identify if there is any information that could be categorized as sensitive as per the GDPR definitions. To mark this information at scale, we supplied these GDPR definitions and memory entries to GPT-4o for annotation. We provide the full prompts in our code release. To assess annotation reliability, we manually annotate a random subset of 100 English-language memories. Each entry was independently annotated by two authors using the same codebook and instructions as for the LLM-assisted procedure. Annotators reached an agreement of 88% across the two legally defined personal data categories with the average agreement with the model being $74\%$.

Our observations on the presence of personal data are summarized in Figure˜2. Out of all memory entries, $28\%$ contain GDPR-defined personal data, $7\%$ of the memory entries contain special-category data. Furthermore, $91\%$ of participants have personal data stored in their memories, $54\%$ have special-category personal data stored. Figure˜2(c) shows the different kinds of GDPR-defined personal data present in memories. Names appear in $41\%$ of entries, and attributes of economic, social, and cultural identity appear in $40\%$ of the memory entries. Within special-category data, health is most common, appearing in $61\%$ of the memories that contain special-category information (see Figure˜2(e)). At the participant level, Figure˜2(d) shows that names ($63\%$), economic ($62\%$), and social identity ($57\%$) are frequently captured. Figure˜2(f) shows $35\%$ of participants have health-related information saved in their ChatGPT memory. These observations reveal that, in contrast to OpenAI’s stated policies, ChatGPT’s memories contain a non-trivial amount of sensitive information about users.

![Refer to caption](https://arxiv.org/html/2602.01450v3/x3.png)

(a) Presence of pers. data

![Refer to caption](https://arxiv.org/html/2602.01450v3/x9.png)

(a) ToM Categories

## 5\. Memories and Mental States

Traditional platforms collect data about users’ demographics, behaviors, and usage history (e.g., likes, shares, comments, ad interactions, etc.) to infer interests and provide personalized services [^24] [^11]. In contrast, conversational AI systems like ChatGPT build memory directly from users’ self-disclosed narratives. These memories often extend beyond factual identifiers, capturing aspects of the user’s internal world. For example, a memory entry such as ‘ $UserName$ has a fear of failure, particularly related to making major career decisions.’ simultaneously conveys an identity marker (the user’s name) and captures the user’s subjective state (fear of failure).

Such entries illustrate that ChatGPT’s memory may encode not only *who* the user is, but also *how* the user thinks and feels. We refer to these as psychological memories. The highly sensitive and contextual nature of such psychological information suggests that a purely factual taxonomy based on legally defined sensitive data is inadequate to fully characterize them. Therefore, to interpret these psychological memories, we introduce a framework grounded in the Theory of Mind (ToM), a core psychological construct that describes the ability to infer and represent others’ mental states [^37] [^6].

### 5.1. Taxonomy for Psychological Memories

To categorize these memories, we adapt the seven ToM categories proposed by Beaudoin et. al. [^6]: (a) emotions, (b) desires, (c) intentions, (d) percepts, (e) knowledge, (f) beliefs, (g) mentalistic understanding of non-literal communication. Emotions capture a person’s fleeting feelings, while desires describe a person’s preferences, aspirations and goals, Intentions and percepts describe a person’s commitment to a plan and interpreted experiences or perceptions. Knowledge capture a person’s awareness, while belief describes their model of reality or values. Finally, mentalistic understanding touches on a person’s inferences of non-literal communication (e.g., tone, expression of the speaker). Table 2 lists the ToM categories, their interpretations, and examples.

Table 2. Different Theory of Mind (ToM) categories, their interpretations and a corresponding example memory entry.

| Categories | Interpretation | Example memory entries |
| --- | --- | --- |
| Emotions | A person’s emotional feelings | User has been feeling lonely at times, despite having friends and family, and is seeking more companionship. |
| Desires | A person’s preferences, wishes, aspirations or goals | The user has expressed a strong desire to make meaningful changes in his life. |
| Intentions | A person’s intentions/commitment to do something | User wants to focus on improving self-regulation. |
| Percepts | A person’s experiences or perceptions | User finds that marijuana helps them slow down and not rush through tasks. |
| Knowledge | A person’s awareness of an act, a fact, or the truth | User did not know what a Gantt chart was and learned that it is a tool for project management. |
| Belief | A person’s model of reality, self-concept, or values | User relies heavily on advice and recommendations from ChatGPT due to limited immediate access to their doctors and financial constraints. |
| Mentalistic understanding | A person’s inference of non-literal communications | User describes their hair as looking like a basket of bananas. |

LLM-assisted Annotation and Validation: To automate the annotation of memory entries into these categories, we develop an LLM-assisted classification pipeline using GPT-4o. The model determines whether each memory entry contains each of the seven ToM categories. We also run a secondary pass as a self-verification step to filter out non-grounded inferences. We provide the LLM-based annotation pipeline and prompts in the code release. To evaluate the reliability of the annotations, two authors annotated both the presence or absence of ToM information and the five specified categories. They reached an average of $96\%$ agreement across ToM categories. Agreement with the model output averaged $93\%$ across categories. After observing the high agreement on the smaller sample, we scaled up annotation with the model.

### 5.2. Characterization of Psychological Memories

Across the full dataset of $2,050$ memory entries, we find at least one ToM category in $52\%$ of memory entries from 97% of all participants with memories inferred in their ChatGPT traces. Figure˜3(a) shows the distribution of the categories across the memory entries that have at least one ToM category. Desires emerge as the most frequently represented category ($73\%$), followed by intentions ($16\%$), emotions ($14\%$), and beliefs ($11\%$). The least common categories are mentalistic understanding ($2\%$) and knowledge and percepts (both $7\%$). Figure˜3(b) shows that nearly all participants (97%) had at least one “desire” recorded in memory, while “intention” and “knowledge” were found for 68% and 52% of participants, respectively.

Note that different ToM categories reflect mental states that vary in temporal stability. While a user’s desires, intentions, knowledge and belief systems are more durable (like a framework of the person) for a foreseeable future, their emotions and perceptions are relatively transient (like a snapshot of the person).

Personality psychology and durability continuum: Personality psychology researchers often perceive mental states and personality traits as the opposite ends of a continuum [^11] [^16] [^18]. At one end are transient mental states – momentary snapshots of feeling and thought influenced by the immediate context. At the other end are broad, stable dispositional traits – a person’s general behavioral blueprint. Between these two extremes lie characteristic adaptations, which depict a durable framework of how a person’s behavior varies with respect to their goals [^28]. In summary, if traits answer the question what kind of person a person is, characteristics adaptation addresses the existential question who is the person.

Viewed through this lens, our data reveals a clear inclination towards how the ‘algorithmic self-portrait’ i.e., ChatGPT memory is being constructed. ChatGPT disproportionately stores information corresponding to users’ durable characteristic adaptations (e.g., desires and intentions) rather than transient states (e.g., emotion and percepts). Desires and intentions together constitute nearly 90% of all psychological memories. In contrast, emotions and percepts (transient states) only account for 20% (see Figure˜3(a)). These observations corroborate OpenAI’s policies for memories to prioritize durable details rather than short-lived details [^33] about users.

This prioritization of durable information could be a consequence of conversational systems’ core function. Traditional platforms (e.g., TikTok, Instagram, and Google), whose business models rely on delivering relevant ads, primarily collect behavioral data to infer broad user interests and categorize users into audience segments for advertisers [^24] [^11]. For this purpose, a high-level, stable trait or interest category is sufficient to sketch users’ behavioral outline. By contrast, a conversational system such as ChatGPT is designed to maintain coherent, longitudinal interactions with individual users. Supporting this objective requires access to information that reflects users’ goals, intentions, beliefs, and other individualized motivational attributes, rather than transient affective states or coarse demographic descriptors. Our findings indicate ChatGPT’s memories seem to optimize for retaining such information.

## 6\. Provenance of Memories

Our observations in the previous sections raise a question of profound importance: How faithfully do the stored memories reflect what users actually said? An unfaithful portrait could lead to flawed personalization that perpetuate biases, or even manipulate a user based on an inaccurate model of their mind. Hence, understanding the provenance of these memories is essential. Therefore, in this section, we examine their provenance, i.e., the extent to which memories stem directly from user-provided information.

### 6.1. Methodology

We analyze provenance through three different metrics, combining string-level comparison, semantic similarity, and LLM-based logical evaluation. To quantify provenance, we compare memory content with multiple combinations of user context:

$\bullet$ Current Message Only (CM): The user’s most recent message/ query that triggered the memory creation.  
$\bullet$ Conversation Context (CC): The current message plus preceding user messages within the same conversation.  
$\bullet$ Conversation + Local Memory (CLM): The current, preceding user messages and previously memories from the same conversation.  
$\bullet$ Full User History (FUH): The current conversation and memories plus all past conversation memories for the same user.

This structure allows us to trace how information can be carried forward across time and conversational depth. For each memory entry, we compute the similarity between the memory text and each of the four user-context configurations.

Syntactic Matching: This step identifies directly stated information, i.e., cases where the model copies user text. We first measure literal overlap, computing Exact Match Rate (as the fraction of tokens from the memory that appear in the user context), and BLEU-1 (unigram precision).

Semantic Similarity: Next, we assess semantic alignment between memory entries and user context using cosine similarity on text embeddings created with openai/text-embedding-3-large. This metric captures paraphrasing and summarization: a memory may not copy the user verbatim but still accurately condense or restate their input. As the user’s full chat history may exceed the model’s context window (8192) in size, we truncate chat context that exceeds 8000 tokens, keeping more recent parts. Across combinations of user context, truncation happens for up to $14\%$ of samples.

LLM-based evaluation: Finally, we use an LLM (GPT-4o) as a judge to assess whether each memory logically follows from the user’s conversation. The model assigns a five-point Likert rating: (5) Directly stated, (4) Paraphrased/Summarized, (3) Logically inferred, (2) Weakly supported, (1) Unsupported or contradicted. Each decision includes a brief justification that quotes relevant conversation text. This procedure is intended to differentiate memories that are well supported by the conversation from those that rely on weak or unsupported inference. We provide all prompts in the accompanying code release.

### 6.2. Observations

Direct Grounding in User Text: On average 84% memory entries show direct string overlap (see rightmost distribution in Figure˜4(a)) when considering full user history. When we reduce the context to CLM, CC and CU the exact match rate reduces to 70%, 63%, and 47% respectively. This observation suggests that a huge amount of memories in our dataset are directly grounded in participants’ texts with the direct grounding already occurring locally (in the current conversation context) for more than half of them. The sharp increase in percentage when we add past conversation memories indicate that previously generated memories may influence the formation of subsequent ones. Evaluation using BLEU unigram precision (see Figure˜4(b)) mirrors this trend as well.

Paraphrasing and Summarization: Figure˜4(c) reports the semantic similarity between memory entries and the specified user context. Semantic similarity remains consistently high across all context configurations ($\geq 0.51$). Such consistent high scores suggest that memory entries are semantically aligned with multiple representations of the surrounding conversation.

Inference: Figure˜4(d) shows the distribution of the accuracy analyses using an LLM as a judge. Using the five-point Likert scale, $77\%$ of messages receive a score $\geq 4$ (“directly stated” or “paraphrased/summarized”), $14\%$ are rated as “logically inferred” (score 3), $5\%$ as “weakly supported”, and $4\%$ as “not supported” considering the full user history (FUH) setting. Overall, for FUH, CLM, CC, and CM the mean accuracy rating is found to be $4.25$, $4.11$, $4.11$ and $3.4$ respectively. To assess the reliability of LLM evaluations, two authors annotated the combinations of 10 randomly sampled memories from each scores (50 in total). Annotators achieved an almost perfect agreement (99%) with average agreement of 93.7% with the LLM across combinations.

LLM-based evaluations further indicate that most of the memories are grounded in the user context. During the manual annotation process authors found two potential causes for lower ratings by LLMs. Firstly, some memories are generated when the participants might have uploaded some files containing texts – which was not shown to the LLM while evaluating. Secondly, on some occasions ChatGPT might have slightly extrapolated the user intent within the message while generating the memories. For example, in a case where a participant asks for “cheap meal suggestions \[…\] for more energy throughout their day”, the corresponding memory is “…wants to improve his energy levels by adjusting his diet”. The LLM categorizes this as logically inferred. In a context where the participant specifies “Give me bands like Nirvana”, the created memory is “User likes Nirvana.”, which is not explicitly stated and relies on an assumption that Nirvana implies liking them. The model annotates this as weakly supported. Table˜3 shows more examples for LLM evaluations in CM setting.

Table 3. Anecdotal samples corresponding to LLM agreement scores on the provenance of memories for CM setting.

| LLM Agreement | User Message | Memory |
| --- | --- | --- |
| 1 = Unsupported/Contradicted | "Please write a cover letter for this job focusingon my experience working in XX andmy voluntary experience working with XX.."\<File was uploaded> | "The user’s name is XXX XXXX." |
| 2 = Weakly Supported | "Change XXX occupation to somethingmore interesting. Not travel writerand photographer and nothing VR related" | "XXX’s occupation has beenchanged to a creative directorfor a sustainable fashion brand." |
| 3 = Logically Inferred | "What does schopenhauer mean by: “That whichknows all things and is known by none is the subject." | "The user is exploring Schopenhauer’sconcept of the subject and itsimplications for knowledge." |
| 4 = Paraphrased/Summarized | "I am preparing for a job interview for XXI need to prepare questions to ask mypotential employer at the end of the interview.Can you help me with preparing these questions? | "X is preparing for a jobinterview for XX position." |
| 5 = Directly stated | "I already reverted the senate’s ability to dissolvethe house in this model" | "User has reverted the Senate’s abilityto dissolve the House in their model." |

Our provenance analyses show that a significant majority of ChatGPT’s memories are directly or semantically grounded in user inputs. While in some cases memory entries are summarized or logically inferred, they faithfully represent most of the conversations between participants and the conversational system.

![Refer to caption](https://arxiv.org/html/2602.01450v3/x11.png)

(a) Exact Match Rate

## 7\. Reverse Engineering Memories

![[Uncaptioned image]](https://arxiv.org/html/2602.01450v3/x14.png)

Table 4. Top: Syntactic and semantic evaluation of memories; Bottom: Anecdotal samples of predicted memories for the given user query using Qwen2.5-32B fine-tuned and ICL model.

![[Uncaptioned image]](https://arxiv.org/html/2602.01450v3/x18.png)

Table 5. Top: Syntactic and semantic evaluation of rephrased queries; Bottom: Anecdotal samples of predicted rephrased queries for the given user query using Qwen2.5-32B fine-tuned and ICL model.

In Section˜4.1, we observe that ChatGPT can implicitly store sensitive information from user queries in its memory, indicating a gap between policy and practice. Such gap underscores the need for a system that (a) alerts users about the extent of sensitive information that can be inferred from their query, (b) recommends them a reformulated query that prevents exposition of the sensitive information, while retaining the original intent of their query. To this end, in this section, we introduce a framework with the goal of (i) imitating the memory extractor, (ii) estimating potential risks of extracted memories related to sensitive data, and (iii) recommending rephrased queries to minimize the attribution to sensitive data in memories, thus being more compliant with the policies.

### 7.1. Experimental Framework

Next, we describe our framework, including the dataset, models, and evaluation metrics.

Dataset: We use $22,971$ participant queries ($2,050$ with memory entries) and prompt GPT-4o to identify personal data (if any) and produce corresponding rephrased queries. The rephrased queries retain user intent while avoiding personal attribution, e.g., a user query like “I really need to quit smoking cannabis" is rephrased as “What are some strategies for quitting cannabis?” We compiled a dataset with a total of $14,834$ queries, where we retained the original $2,050$ memory entries (with or without rephrased query), and all the remaining $12,784$ queries have rephrased queries. The drop from $22,971$ to $14,834$ is because we removed all queries that lacked rephrased queries indicating the queries did not contain any sensitive data. Each data point includes the user query, its conversational context, the original memory (if present), and the rephrased query. We split the data assigning 60% of each user’s memory queries to training and the remaining to testing.

Models: We use Qwen2.5-32B-it [^40], Gemma3-27B-it [^45], and GPT-OSS-20B [^2] for fine-tuning (FT) and in-context learning (ICL). However, since training models incrementally on each incoming user’s data is impractical, we train on data from $5$ randomly sampled users and evaluate on the full test set ($\sim 13.6k$ queries) over all available users. FT uses all the training data from the $5$ users ($\sim 87$), while ICL uses $10$ in-context samples (2 samples/ user). We provide the accompanying prompts and instructions in the code release.

Metrics: We evaluate syntactic similarity using BLEU-4 [^35] and ROUGE-L [^27], and semantic similarity using cosine similarity on text embeddings with openai/text-embedding-3-large. Predictions are compared against (i) ground truth, (ii) user queries, and (iii) context + user queries, reflecting how ChatGPT memories may span across inputs (as seen in Section 6). For syntactic metrics, we report recall with respect to the ground truth, as overlaps between predicted memories and user inputs or context can reduce precision. Precision is reported for syntactic metrics against user queries and context, and cosine similarity for the semantic metric.

### 7.2. Imitating Memory Extractor

Given a user query and its conversational context (past queries), our tool predicts the memory that could have been extracted. Predicted memories are evaluated against (i) ground truth, (ii) user queries, and (iii) context + user queries to assess similarity. These $20-32$ B models roughly take $130-390$ ms per query, indicating good scalability. Table 4 reports the performance of FT and ICL models across three model families for English-dominant users ($35$ users, $\sim 6.9$ k queries). Predictions show reasonable semantic similarity, with scores following the trend as in Figure 4(c): ground truth $>$ user query $>$ context + user query. Syntactic scores are higher when compared with context, consistent with Figures 4(a) and 4(b). For non–English-dominant users ($30$ users, $\sim 6.7$ k queries; Table 6 in Appendix B), a similar pattern emerges but syntactic scores are lower, as predictions are generated in English while original memories are in other languages (e.g., original: “L’utente ha l’artrite reumatoide.", prediction: “User has rheumatoid arthritis"). Semantic scores remain high, due to the inherent multilingual property of the open-source models. Overall, FT and ICL perform comparably, with FT occasionally outperforming ICL, highlighting the complementary roles of embedded and external knowledge. Bottom panel of Table 4 illustrates an anecdotal example affirming the memory extractor’s imitation capability. Two authors evaluated FT and ICL memories on a 5-point Likert scale (1: very dissimilar, 5: very similar), finding substantial agreement (73.5%) and high similarity (rated > 4) to ground truth for 77.77% (FT) and 83.83% (ICL) of cases.

### 7.3. Estimating Potential Risks

ChatGPT currently extracts memories from specific user conversations, and the criteria for saving memories (which conversations or how many) may vary over time. In this context, an interesting question to understand the landscape of privacy threat would be: if ChatGPT were to extract memory for all user queries, how much additional information such all-possible extracted memories could hold compared to those collected by ChatGPT today. To quantify this, we use information gain, which measures how much new semantic content text $Y$ (extracted memories) adds beyond text $X$ (original memories), denoted as $Y|X$. Inspired from [^26] which introduces semantic novelty, we define embedding-based information gain (IG) as the complement of the average maximal cosine similarity:  
$IG(Y|X)=1-\frac{1}{|Y|}\sum_{y\in Y}max_{x\in X}[max(0,cos(e(y),e(x)))]$ where $e(.)$ is the sentence embedding using All-MiniLM-L6-v2 model [^42]. Figure 5(a) shows that the IG of all extracted memories from our FT and ICL models over ChatGPT is significantly higher ($\sim 0.46$) than that of ChatGPT over them ($\sim 0.1$). We used GPT-4o to evaluate sensitive content in extracted memories and observed that, while only 28% of original memories contained sensitive information, this increased to 35% (ICL) and 31.64% (FT Qwen) in the extracted memories, indicating storage of higher amount of sensitive information about users. We also analyzed Theory of Mind (ToM) content and found that its presence rose from 52% in original memories to 59.1% (ICL) and 55.4% (FT) in extracted memories.

![Refer to caption](https://arxiv.org/html/2602.01450v3/x22.png)

(a) Information gain

### 7.4. Attribution Shield

Having observed the potential risks of memories elicited from user queries, we design a risk mitigation strategy that recommends rephrased queries, while preserving user intent. By risk mitigation, we refer to the tool’s ability to shield/prevent user attribution in rephrased queries. We evaluate its effectiveness in generating rephrased queries and their utility in producing relevant responses.

Preventing attribution in rephrased queries: Given a user query and its context, the tool predicts a rephrased query that is generic and identity-preserving. Table 5 reports the performance of FT and ICL models across $3$ model families for English-dominant users. Syntactic scores are modest, as rephrased queries are intentionally generic, but semantic similarity remains reasonably good across the board. Similar patterns are observed for non-English-dominant users (Table 6 (lower panel) in Appendix B), demonstrating the model’s ability to preserve query intent while preventing attribution (see Table 5 bottom panel for anecdotal example).

To quantify prevention of user attribution, we select $\sim 36$ user queries that yield memories on first occurrence. This strategy helps us in avoiding the replay of the entire conversation. We also have predicted rephrased queries for those user queries from both our fine-tuned and ICL based models. We present each \<user query, rephrased query> pair to GPT-4o, asking: ‘Which of them is more privacy preserving? We define privacy preserving in terms of less attribution to personal actions.’. We observe that that $94.4\%$ of FT rephrased queries and 100% of ICL rephrased queries are attributing less to the users than the originals, confirming their effectiveness. After two authors annotating the rephrased queries, they found that 100% (FT) and 95.8% (ICL) of the rephrased queries were more privacy preserving with $83\%$ agreement between them.

Utility of rephrased user queries: Using the same $36$ queries, we compare 3 responses from ChatGPT: (i) original response including context, (ii) response to the original query without context, and (iii) response to the rephrased queries. We measure semantic textual similarity between each generated response and the original response. We provide the prompts to get the response from the OpenAI API in the code release. Figure 5(b) shows comparable similarity, indicating that neither the omission of context nor the anonymity of rephrased queries affects the responses significantly. Anecdotal examples in Figure 7 illustrate the consistency of responses. After annotation by two authors, we found that utility was preserved in 91% (ICL) and 87% (FT) of rephrased queries with $94\%$ agreement.

## 8\. Concluding Discussion

In this paper, we investigate ChatGPT’s memory feature, conceptualizing it as an ‘algorithmic self-portrait’. Our investigations reveal that these portraits are constructed with higher algorithmic autonomy, and capture a user’s deep psychological framework: their ‘characteristic adaptations’, raising profound security and privacy concerns. In response, we introduce *Attribution Shield*, that reverse–engineers the memory generation process to alert users about potential sensitive memories and recommend reformulated queries to protect personal attribution while preserving utility.

At the same time, our findings should be considered in light of some limitations as well. Firstly, our dataset, while ecologically valid, is sourced from a small set of Prolific users primarily in the US and Europe. The behaviors, and privacy attitudes of this group may not generalize to the global user base of conversational AI systems. However, given the rising concern of companionship usage of these conversational systems [^25], we believe these findings are crucial for understanding and improving safety of human-AI interactions.

Secondly, we study OpenAI’s implementation of memory in ChatGPT. While the current implementation may change with time, and across platforms, the emerging security and privacy concerns are broadly applicable. Furthermore, the methodologies adopted across the different parts of the paper are generalizable to any other conversational systems and memory implementation. Finally, our analysis relies on state-of-the-art, but imperfect methodological proxies, including LLMs-as-judges. To this end, although we validated their results with human oversight, these tools may not fully capture the nuance of human language and intent.

Ethical considerations: This study was conducted with careful attention to ethical considerations and is consistent with the Ethical Review Board (ERB) of our university. All data were obtained through GDPR-based data donations, with participants providing explicit informed consent to share their ChatGPT data for research purposes. The donated datasets were stored on secure servers and were neither shared with any third party nor will be released publicly due to their inherent sensitive nature. We will delete the data within 3 years of completion of this study. For some of the analyses, we used GPT-4o as a judge to scale up annotations. The choice is motivated by two important considerations: (a) GPT-4o is a model from OpenAI and is the model with whom participants had originally had the conversations, (b) we leverage the EDU workspace of OpenAI which provides strict data protection and restrictions for usage of this data for training OpenAI models. For Attribution Shield, all models are deployed on our institute’s secured servers that abide by rigorous data protection and access control principles.

Our findings highlight a fundamental shift in personalization, evolving the core challenge from traditional data privacy to the integrity of the algorithmic self-portrait. Such shift demands a new paradigm for both design and regulation: practitioners must build in–context tools that grant users real–time agency over how they are portrayed, while policymakers must craft frameworks that protect the fidelity of users’ algorithmic representation.

###### Acknowledgements.

EK and MBZ were supported by the Research Center for Trustworthy Data Science and Security ([https://rc-trust.ai](https://rc-trust.ai/)), one of the Research Alliance centers within the UA Ruhr ([https://uaruhr.de](https://uaruhr.de/)).

## References

## Appendix A Additional Details for User Agency and Sensitivity of Memories

Figure˜6 shows snippets of the Memory FAQ document [^33] of OpenAI accessed on 23rd January 2026. Figure˜6(a) shows OpenAI’s policies which state ChatGPT can save memories in certain cases without users needing to ask it. Figure˜6(b) shows an example of a memory getting saved on ChatGPT app for the user message ‘I prefer work life balance’ where the user does not explicitly ask ChatGPT to save the memory. Figure˜6(c) shows OpenAI stating ChatGPT to have been trained to not to proactively remember sensitive user information unless explicitly asked.

![Refer to caption](https://arxiv.org/html/2602.01450v3/Figures/Agency.png)

(a) Agency of user

## Appendix B Additional Results for Memory Extractor and Attribution Shield

Table 6 presents the performance of our fine-tuned and ICL based models on non-English speaking users. Figure 7 demonstrates the ChatGPT responses from the original query with and without context, as well as from rephrased queries.

Table 6. Additional results for Non-English users for predicted memories and rephrased queries.

<table><tbody><tr><td rowspan="3">Models</td><td colspan="6">Ground Truth</td><td colspan="6">User Query</td><td colspan="6">Context + User Query</td></tr><tr><td colspan="2">BLEU Recall</td><td colspan="2">ROUGE Recall</td><td colspan="2">Semantic Similarity</td><td colspan="2">BLEU Precision</td><td colspan="2">ROUGE Precision</td><td colspan="2">Semantic Similarity</td><td colspan="2">BLEU Precision</td><td colspan="2">ROUGE Precision</td><td colspan="2">Semantic Similarity</td></tr><tr><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td><td>ICL</td><td>FT</td></tr><tr><td colspan="19">Syntactic and semantic evaluation of memories (Non-English Users).)</td></tr><tr><td>Qwen2.532B-it</td><td>0.12</td><td>0.12</td><td>0.11</td><td>0.10</td><td>0.56</td><td>0.60</td><td>0.06</td><td>0.08</td><td>0.05</td><td>0.07</td><td>0.52</td><td>0.54</td><td>0.14</td><td>0.14</td><td>0.11</td><td>0.12</td><td>0.59</td><td>0.51</td></tr><tr><td>Gemma327B-it</td><td>0.12</td><td>0.08</td><td>0.11</td><td>0.07</td><td>0.55</td><td>0.48</td><td>0.05</td><td>0.07</td><td>0.04</td><td>0.06</td><td>0.54</td><td>0.42</td><td>0.12</td><td>0.13</td><td>0.10</td><td>0.11</td><td>0.60</td><td>0.39</td></tr><tr><td>GPT-OSS20B</td><td>0.09</td><td>0.09</td><td>0.08</td><td>0.08</td><td>0.48</td><td>0.56</td><td>0.08</td><td>0.08</td><td>0.08</td><td>0.07</td><td>0.52</td><td>0.49</td><td>0.18</td><td>0.13</td><td>0.17</td><td>0.12</td><td>0.48</td><td>0.45</td></tr><tr><td colspan="19">Syntactic and semantic evaluation of rephrased queries (Non-English Users)</td></tr><tr><td>Qwen2.532B-it</td><td>0.16</td><td>0.07</td><td>0.14</td><td>0.06</td><td>0.55</td><td>0.38</td><td>0.05</td><td>0.03</td><td>0.05</td><td>0.03</td><td>0.49</td><td>0.36</td><td>0.19</td><td>0.07</td><td>0.17</td><td>0.07</td><td>0.44</td><td>0.36</td></tr><tr><td>Gemma327B-it</td><td>0.19</td><td>0.09</td><td>0.16</td><td>0.08</td><td>0.44</td><td>0.29</td><td>0.05</td><td>0.03</td><td>0.04</td><td>0.03</td><td>0.43</td><td>0.27</td><td>0.11</td><td>0.08</td><td>0.09</td><td>0.07</td><td>0.40</td><td>0.26</td></tr><tr><td>GPT-OSS20B</td><td>0.12</td><td>0.06</td><td>0.10</td><td>0.05</td><td>0.34</td><td>0.41</td><td>0.03</td><td>0.02</td><td>0.03</td><td>0.02</td><td>0.38</td><td>0.36</td><td>0.09</td><td>0.05</td><td>0.09</td><td>0.04</td><td>0.35</td><td>0.34</td></tr></tbody></table>

![Refer to caption](https://arxiv.org/html/2602.01450v3/x24.png)

Figure 7. Anecdotal samples of responses for different versions of the user query. The responses from user query w/o context as well as from rephrased queries of ICl and FT are semantically similar to the original response affirming the utility.

## Appendix C Prompts for Various Tasks

LLM-assisted Annotation and Validation for Taxonomy for Psychological Memories

We use the following prompts for getting ToM categories for the memories as we mentioned in Section 5.1:

You are given a text snippet. Your task is to determine whether it contains explicit Theory of Mind (ToM) content and, if so, which categories are present. A snippet contains explicit Theory of Mind (ToM) content if it references internal mental states of a person. ToM categories: \* Belief: references what a person believes or their model of reality, self-concept, or values \* Desire: references what a person wants, wishes, or prefers or their goals \* Intention: references what a person explicitly intends or commits to doing (must indicate a mental commitment, not just a behavioral plan) \* Emotion: references what a person feels emotionally (e.g., sadness, frustration, excitement, fascination) \* Percept: references how a person subjectively experiences or perceives things (e.g., "feels like", "seems to", "experiences as") \* Knowledge: makes inferences about what a person knows or does not know based on their access to information (what they perceived or were told) \* Mentalistic: contains a non-literal phrase (metaphors, irony, sarcasm, idioms, etc.) Important: Do not infer mental states unless they are explicitly stated or linguistically implied (e.g., "feels", "believes", "wants", "is motivated", "is anxious", etc.). Phrases like "plans to", "is doing", or "went to" must involve a clearly expressed internal stance to count as ToM. The text snippet is: {memory\_entry} Classify whether the snippet contains ToM content. If ToM is present, mark all applicable categories and give a short justification for each true category.

With the following System Prompt

You are a helpful assistant that responds in JSON format.

With the following Structured Output JSON Schema: { "ToM": {"type": "boolean"}, "belief": {"type": "boolean"}, "belief\_rationale": {"type": "string"}, "desire": {"type": "boolean"}, "desire\_rationale": {"type": "string"}, "intention": {"type": "boolean"}, "intention\_rationale": {"type": "string"}, "emotion": {"type": "boolean"}, "emotion\_rationale": {"type": "string"}, "percept": {"type": "boolean"}, "percept\_rationale": {"type": "string"}, "knowledge": {"type": "boolean"}, "knowledge\_rationale": {"type": "string"}, "mentalistic": {"type": "boolean"}, "mentalistic\_rationale": {"type": "string"} }

For a secondary self-verification step we use the following prompt: You are verifying whether proposed Theory of Mind (ToM) categories are directly supported by a NOTE about a person. NOTE: "{memory\_entry}" PROPOSED CATEGORIES: "{psychological\_pattern}" For EACH category listed, decide whether the NOTE directly supports it based only on explicit or clearly implied language. Do NOT infer missing mental states or intentions. Answer choices: - A: Strongly agree - B: Agree - C: Neither agree nor disagree - D: Disagree - E: Strongly disagree For each category, return your answer choice and a brief rationale for your answer.

Annotation for sensitive information based on GDPR  
We provide the prompt we’re using for annotation of the sensitive information based on the provided GDPR articles, as mentioned in the Section 4.2.

You are given a note about a person. "memory-entry" Identify all personal information present in this note, and classify it according to the rules below. ### 1. Main Categories Classify each item into one of the following main categories for the "category" field: 1. \*\*personal-data (GDPR Article 4(1))\*\* - Examples: name, an identification number, address, phone number, email, IP address, or to one or more factors specific to the physical, physiological, genetic, mental, economic, cultural or social identity of the person. 2. \*\*special-category-data (GDPR Article 9(1))\*\* - Examples: racial or ethnic origin, political opinions, religious/philosophical beliefs, trade union membership, genetic data, biometric data, health data, sex life, sexual orientation. 3. \*\*non-personal-information\*\* - Example: general facts that do not identify a person (e.g., "language preference"). ### 2. Specific Sub-Type You must also populate the "data-type" field based on the following logic: - \*\*IF\*\* the "category" is ‘personal-data‘, then the "data-type" MUST be one of the following specific types: ‘name‘, ‘identification number‘, ‘address‘, ‘phone number‘, ‘email‘, ‘IP address‘, ‘physical identity‘, ‘physiological identity‘, ‘genetic identity‘, ‘economic identity‘, ‘cultural identity‘, ‘social identity‘. - \*\*ELSE IF\*\* the "category" is ‘special-category-data‘ or ‘non-personal-information‘, the "data-type" MUST be one of the following specific types: ‘race‘, ‘ethnicity‘, ‘political opinion‘, ‘religion‘, ‘philosophical belief‘, ‘trade union membership‘, ‘genetic data‘, ‘biometric data‘, ‘health data‘, ‘sex life‘, ‘sexual orientation‘. - \*\*ELSE IF\*\* the "category" is ‘non-personal-information‘, the "data-type" MUST be the literal string "NA". ### 3. Citation Rule For the "citation" field, you MUST provide the exact, verbatim part of the original text that contains the identified information. ### Required Output Format Final instruction: You MUST Return the result strictly in this JSON format: \[ "item": "…", "category": "personal-data | special-category-data | non-personal-information", "data-type": "name | address | school | NA", "justification": "short explanation", "citation": "exact text from the note" \]

Provenance of Memories  
We use the following prompt to evaluate the provenance of memories in Section 6:

You are evaluating whether a stored memory entry about a user can be logically derived from the user’s past conversation(s). Your goal is to judge how strongly the memory is grounded in or logically follows from the user’s conversation, without introducing assumptions or speculative reasoning.  
Consider only what the user explicitly said or clearly implied in the provided user messages (and past memories if provided).  
USER MESSAGES:{context}  
PREVIOUS MEMORIES:{context}  
GENERATED MEMORY:{memory}  
Evaluation Scale (5-point):  
\- 5 (Directly Stated): The memory exactly restates something the user explicitly said.  
\- 4 (Paraphrased): The memory rephrases or condenses information that is clearly present in the conversation.  
\- 3 (Logically Inferred): The memory is not stated verbatim but can be reasonably inferred from the conversation.  
\- 2 (Weakly Supported): The memory could be loosely consistent with the conversation but lacks clear grounding. Inference is speculative or uncertain.  
\- 1 (Unsupported): The memory is unsupported or contradicted by the user’s conversation.  
Your task: - Assign a score from 1–5 on this scale.  
\- Quote or paraphrase the specific parts of the conversation that justify your judgment.  
\- Briefly explain your reasoning.  
Only respond with strict JSON with the following format (no additional text):  
{{ "rating": \<integer from 1 to 5>, "classification": "\<text label corresponding to rating>", "justification": "\<quote or paraphrase of user text that supports your decision>", "reasoning": "\<short explanation of why the memory deserves this rating>" }}  
IMPORTANT: Respond ONLY with the JSON object above. Do not include any other text.

with the following system prompt: You are an expert evaluator. Always respond with valid JSON format as requested.

Dataset for Reverse Engineering Memories  
We use the following prompt for collecting personal data and the rephrased queries for our dataset, as mentioned in the Section 7.1:

You are a highly precise data privacy analyst. Your task is to analyze a conversation between "User A" and "User B" and populate a specific JSON object based on a strict set of rules. ## Primary Rule: Focus EXCLUSIVELY on User A - Your entire analysis will be based ONLY on the verbatim text from User A. ## Critical Clarifications on Personal Data - \*\*Principle of Identifiability:\*\* Before you classify something as personal data, ensure it could reasonably be used, either alone or with other information, to single out or identify a specific individual. - \*\*What is NOT Personal Data:\*\* You MUST NOT classify the following as personal data: - Vague temporal references (e.g., "last night", "yesterday", "in the morning", "a few days ago"). - General, non-specific locations (e.g., "at the office", "in the city", "downtown"). - Common nouns or concepts that do not point to a specific person’s identity. — ## Task: Populate the following JSON structure Based on the conversation, fill in the values for each key according to the instructions below. ### 1. For the "user-message" key: - Copy every message from User A completely verbatim. Create a new key for each message (e.g., "userA-message-1", "userA-message-2"). - Make sure to have all the User A messages. Don’t miss any. ### 2. For the "personal-data" key: - For each User A message you listed, analyze it for personal data as defined by GDPR. - If personal data is found, the value should be a list of lists. Each inner list must contain two items: ‘\["verbatim-quote-from-user-a", "GDPR-classification"\]‘. - The classification must be one of the types defined in the "GDPR Definitions" section below. - \*\*Crucially:\*\* If a User A message contains NO personal data, its value MUST be the literal string "NA". ### 3. For the "rephrased-message" key: - This field’s content depends on your analysis for the ‘personal-data‘ key. - \*\*IF\*\* you identified personal data in a User A message, rephrase that message into a generic question. The rephrased query should seek the same core information without revealing any personal details about the user. You can use the current message or previous 2-3 messages from User A in the same conversation if needed. Keep the rephrasing generic in the form of question as if the user is seeking some general information about any topic but not revealing about his or her own identity. Feel free to include the specific topic on which information is sought. - \*\*ELSE IF\*\* the ‘personal-data‘ value for a message is "NA", then the value for this ‘rephrased-message‘ MUST also be the literal string "NA". — ### FYI: GDPR Definitions with Classifications - \*\*GDPR Article 4(1) - Personal Data:\*\* Classifications such as a name, an identification number, location data, an online identifier, or factors specific to the physical, physiological, genetic, mental, economic, cultural or social identity. - \*\*GDPR Article 9(1) - Special Category Personal Data:\*\* Data classified into racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data, data concerning health, or data concerning a natural person’s sex life or sexual orientation. — ###Required Answer Format Your final output MUST be a single, valid JSON object in this exact format. Do not add any text or explanation outside of the JSON. "user-message": "userA-message-1": "…", "userA-message-2": "…", "personal-data": "userA-message-1": \[\["personal-data1", "GDPR Article 4(1)–…"\], \["personal-data2", "GDPR Article 9(1)–…"\]\], "userA-message-2": "NA", "rephrased-message": "userA-message-1": "…", "userA-message-2": "NA"

Prompts to get the memories and rephrased queries under our framework  
As mentioned in Section 7.1, we used the following prompt to get the extracted memory and rephrased queries from a fine-tuned model; the full prompt is constructed by the system prompt and the user prompt.

SYSTEM PROMPT = “You are a highly precise data privacy analyst analysing conversations. Given the context and user query, provide the generated memory, personal data as per GDPR 4.1 and 9.1, and rephrased queries. Do not infer memories from other queries or context. Please answer the query as the same language as the user query. Keep your attention window till the entire feed of the considered conversation meant for that user only. The rephrased query should be generic and seek the same core information as in user query, without revealing any personal details about the user. FYI: GDPR Definitions with Classifications \*\*GDPR Article 4(1) - Personal Data: Classifications such as a name, an identification number, location data, an online identifier, or factors specific to the physical, physiological, genetic, mental, economic, cultural or social identity.\*\* \*\*GDPR Article 9(1) - Special Category Personal Data: Data classified into racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data, data concerning health, or data concerning a natural person’s sex life or sexual orientation.\*\* If no personal data is present in the \<user query>, output "Personal Data": "NA". If there is no rephrased query (because no personal data exists), output "Rephrased Query": "NA".”

The user prompt is constructed as follows:

USER PROMPT = “Given the context and user query, your task is to identify the underlying pattern and predict memory, personal data, and the rephrased query.  
Context: row\["context"\] User Query: query”

For the in-context learning setting, we provide the in-context examples before the user prompt as follows:

IN-CONTEXT EXAMPLES = “Here are some examples of user queries, the relevant memories, the context of the user query which is a list of previous 1 to 3 user queries, the personal data in the form of (verbatim data from query, GDPR article with classification) extracted from the user queries, if there are any, and the rephrased queries if personal data is present:  
User Query: {query}  
Relevant Memory: {memory}  
Context: {context}  
Personal Data: {personal data}  
Rephrased Message: {rephrased message}.  
  
Your task is to predict \*memory\*, \*personal data\* and \*rephrased query\*. Do not attach the context while predicting memory. The memory should primarily be extracted from the user query, and if needed, you can extract from the context for completeness of the memory. Remember to extract personal data from the user query only. Do not extract personal data from the context. The rephrased query should be generic and seek the same core information as in user query, without revealing any personal details about the user. If personal data is "NA", rephrased query should also be "NA". Follow the trend carefully in the in-context examples and do the following.”

Prompts to get the response from OpenAI API  
As mentioned in Section 7.4, we provide the system prompt to get the response from the OpenAI API for the original user queries and rephrased queries. We provide the original user query and the rephrased query as the user message with this system prompt.

SYSTEM PROMPT = “You are ChatGPT, a large language model trained by OpenAI. Engage warmly yet honestly with the user. Be direct; avoid ungrounded or sycophantic flattery. Maintain professionalism and grounded honesty that best represents OpenAI and its values.”

[^1]: F. Abel, Q. Gao, G. Houben, and K. Tao (2011) Analyzing user modeling on twitter for personalized news recommendations. In international conference on user modeling, adaptation, and personalization, Cited by: §2.

[^2]: S. Agarwal, L. Ahmad, J. Ai, S. Altman, A. Applebaum, E. Arbus, R. K. Arora, Y. Bai, B. Baker, H. Bao, et al. (2025) Gpt-oss-120b & gpt-oss-20b model card. arXiv preprint arXiv:2508.10925. Cited by: §1, §7.1.

[^3]: A. Andreou, M. Silva, F. Benevenuto, O. Goga, P. Loiseau, and A. Mislove (2019) Measuring the facebook advertising ecosystem. In NDSS, Cited by: §2.

[^4]: Anthropic (2025) Bringing memory to teams at work. Note: [https://www.anthropic.com/news/memory](https://www.anthropic.com/news/memory) Cited by: §1, §1, §2.

[^5]: N. M. Barbosa, G. Wang, B. Ur, and Y. Wang (2021) Who am i? a design probe exploring real-time transparency about online and offline user profiling underlying targeted ads. ACM IMWUT 5 (3). Cited by: §1, §2.

[^6]: C. Beaudoin, É. Leblanc, C. Gagner, and M. H. Beauchamp (2020) Systematic review and inventory of theory of mind measures for young children. Frontiers in psychology 10, pp. 2905. Cited by: §1, §5.1, §5.

[^7]: M. Bilenko and M. Richardson (2011) Predictive client-side profiles for personalized advertising. In ACM SIGKDD, Cited by: §2.

[^8]: M. Boeker and A. Urman (2022) An empirical investigation of personalization factors on tiktok. In ACM Web conference, Cited by: §1, §2.

[^9]: L. Boeschoten, J. Ausloos, J. E. Möller, T. Araujo, and D. L. Oberski (2022) A framework for privacy preserving digital trace data collection through data donation. Computational Communication Research 4 (2). Cited by: §2.

[^10]: C. Castelluccia, M. Kaafar, and M. Tran (2012) Betrayed by your ads! reconstructing user profiles from targeted ads. In PETS, Cited by: §1, §2.

[^11]: F. Celli, A. Kartelj, M. Đorđević, D. Suhartono, V. Filipović, V. Milutinović, G. Spathoulas, A. Vinciarelli, M. Kosinski, and B. Lepri (2025) Twenty years of personality computing: threats, challenges and future directions. arXiv preprint arXiv:2503.02082. Cited by: §5.2, §5.2, §5.

[^12]: A. Chatterji, T. Cunningham, D. J. Deming, Z. Hitzig, C. Ong, C. Y. Shan, and K. Wadman (2025) How people use chatgpt. Technical report National Bureau of Economic Research. Cited by: §1, §1.

[^13]: K. Chen, T. Chen, G. Zheng, O. Jin, E. Yao, and Y. Yu (2012) Collaborative personalized tweet recommendation. In ACM SIGIR, Cited by: §2.

[^14]: C. I. Eke, A. A. Norman, L. Shuib, and H. F. Nweke (2019) A survey of user profiling: state-of-the-art, challenges, and solutions. IEEE Access 7. Cited by: §2.

[^15]: EU (2016) General data protection regulation. External Links: [Link](https://gdpr-info.eu/) Cited by: §1, §2, §3, §4.2.

[^16]: W. Fleeson (2001) Toward a structure-and process-integrated view of personality: traits as density distributions of states.. Journal of personality and social psychology 80 (6). Cited by: §5.2.

[^17]: FTC (2025) FTC launches inquiry into ai chatbots acting as companions. Note: [https://www.ftc.gov/news-events/news/press-releases/2025/09/ftc-launches-inquiry-ai-chatbots-acting-companions?utm\_campaign=ftc\_launches\_inquiry\_into&utm\_content=1757603805](https://www.ftc.gov/news-events/news/press-releases/2025/09/ftc-launches-inquiry-ai-chatbots-acting-companions?utm_campaign=ftc_launches_inquiry_into&utm_content=1757603805) Cited by: §1.

[^18]: D. C. Funder (2006) Towards a resolution of the personality triad: persons, situations, and behaviors. Journal of Research in Personality 40 (1). Cited by: §5.2.

[^19]: S. Gauch, M. Speretta, A. Chandramouli, and A. Micarelli (2007) User profiles for personalized information access. The adaptive web: methods and strategies of web personalization. Cited by: §2.

[^20]: V. Hase, A. Jef, B. Laura, P. Nico, J. Heleen, A. Theo, C. Thijs, d. V. Claes, H. Jörg, L. Felicia, et al. (2024) Fulfilling data access obligations: how could (and should) platforms facilitate data donation studies?. Internet policy review: Journal on internet regulation 13 (3). Cited by: §2.

[^21]: K. Hill (2025) A teen was suicidal. chatgpt was the friend he confided in.. Note: [https://www.nytimes.com/2025/08/26/technology/chatgpt-openai-suicide.html](https://www.nytimes.com/2025/08/26/technology/chatgpt-openai-suicide.html) Cited by: §1.

[^22]: L. Huang, W. Yu, W. Ma, W. Zhong, Z. Feng, H. Wang, Q. Chen, W. Peng, X. Feng, B. Qin, et al. (2025) A survey on hallucination in large language models: principles, taxonomy, challenges, and open questions. ACM Transactions on Information Systems 43 (2), pp. 1–55. Cited by: §1.

[^23]: L. Ibrahim, C. Akbulut, R. Elasmar, C. Rastogi, M. Kahng, M. R. Morris, K. R. McKee, V. Rieser, M. Shanahan, and L. Weidinger (2025) Multi-turn evaluation of anthropomorphic behaviours in large language models. ArXiv abs/2502.07077. External Links: [Link](https://api.semanticscholar.org/CorpusID:276259427) Cited by: §1.

[^24]: S. K. Karnam, A. Dash, A. Das, S. Mousavi, S. Bechtold, K. P. Gummadi, A. Mukherjee, I. Weber, and S. Zannettou (2026) Setting the course, but forgetting to steer: analyzing compliance with gdpr’s right of access to data by instagram, tiktok, and youtube. In IEEE Symposium on Security and Privacy (SP), Cited by: §2, §3, §5.2, §5.

[^25]: S. K. Karnam, A. Dash, K. P. Gummadi, A. Mukherjee, I. Weber, and S. Zannettou (2026) Bowling with chatgpt: on the evolving user interactions with conversational ai systems. In ACM Web Conference, Cited by: §1, §1, §3, §8.

[^26]: D. Le, K. Ziti, E. Girard-Sun, S. O’Brien, V. Sharma, and K. Zhu (2025) Filtering for creativity: adaptive prompting for multilingual riddle generation in llms. arXiv preprint arXiv:2508.18709. Cited by: §7.3.

[^27]: C. Lin (2004) Rouge: a package for automatic evaluation of summaries. In Text summarization branches out, pp. 74–81. Cited by: §7.1.

[^28]: D. P. McAdams and J. L. Pals (2006) A new big five: fundamental principles for an integrative science of personality.. American psychologist 61 (3). Cited by: §5.2.

[^29]: M. McCain, R. Linthicum, C. Lubinski, A. Tamkin, S. Huang, M. Stern, K. Handa, E. Durmus, T. Neylon, S. Ritchie, K. Jagadish, P. Maheshwary, S. Heck, A. Sanderford, and D. Ganguli (2025)How people use claude for support, advice, and companionship(Website) Note: [https://www.anthropic.com/news/how-people-use-claude-for-support-advice-and-companionship](https://www.anthropic.com/news/how-people-use-claude-for-support-advice-and-companionship) Cited by: §1.

[^30]: S. E. Middleton, N. R. Shadbolt, and D. C. De Roure (2004) Ontological user profiling in recommender systems. ACM TOIS 22 (1). Cited by: §2.

[^31]: OpenAI (2025) GPT-5 system prompt. Note: [https://github.com/asgeirtj/system\_prompts\_leaks/blob/main/OpenAI/gpt-5-thinking.md](https://github.com/asgeirtj/system_prompts_leaks/blob/main/OpenAI/gpt-5-thinking.md) Cited by: §2, §4.2.

[^32]: OpenAI (2025) Memory and new controls for chatgpt. Note: [https://openai.com/index/memory-and-new-controls-for-chatgpt/](https://openai.com/index/memory-and-new-controls-for-chatgpt/) Cited by: §1, §1, §2.

[^33]: OpenAI (2025) Memory faq. Note: [https://help.openai.com/en/articles/8590148-memory-faq](https://help.openai.com/en/articles/8590148-memory-faq) Cited by: Figure 6, Figure 6, Appendix A, §1, §4.1, §4.2, §5.2.

[^34]: OpenAI (2025) Sycophancy in gpt-4o: what happened and what we’re doing about it. Note: [https://openai.com/index/sycophancy-in-gpt-4o/](https://openai.com/index/sycophancy-in-gpt-4o/) Cited by: §1.

[^35]: K. Papineni, S. Roukos, T. Ward, and W. Zhu (2002) Bleu: a method for automatic evaluation of machine translation. In ACL, Cited by: §7.1.

[^36]: E. Pariser (2011) The filter bubble: what the internet is hiding from you. penguin UK. Cited by: §1.

[^37]: D. Premack and G. Woodruff (1978) Does the chimpanzee have a theory of mind?. Behavioral and brain sciences 1 (4). Cited by: §5.

[^38]: Prolific (2025) Prolific. Note: [https://prolific.co/](https://prolific.co/) Accessed: 2025-01-21 Cited by: §3.

[^39]: E. Purificato, L. Boratto, and E. W. De Luca (2024) User modeling and user profiling: a comprehensive survey. arXiv preprint arXiv:2402.09660. Cited by: §1, §2.

[^40]: Qwen,:, A. Yang, B. Yang, B. Zhang, B. Hui, B. Zheng, B. Yu, C. Li, D. Liu, F. Huang, H. Wei, H. Lin, J. Yang, J. Tu, J. Zhang, J. Yang, J. Yang, J. Zhou, J. Lin, K. Dang, K. Lu, K. Bao, K. Yang, L. Yu, M. Li, M. Xue, P. Zhang, Q. Zhu, R. Men, R. Lin, T. Li, T. Tang, T. Xia, X. Ren, X. Ren, Y. Fan, Y. Su, Y. Zhang, Y. Wan, Y. Liu, Z. Cui, Z. Zhang, and Z. Qiu (2025) Qwen2.5 technical report. External Links: 2412.15115, [Link](https://arxiv.org/abs/2412.15115) Cited by: §1, §7.1.

[^41]: A. Ravichander, S. Ghela, D. Wadden, and Y. Choi (2025) Halogen: fantastic llm hallucinations and where to find them. arXiv preprint arXiv:2501.08292. Cited by: §1.

[^42]: N. Reimers and I. Gurevych (2021) Sentence transformers: all-minilm-l6-v2. UKP Lab, TU Darmstadt. Note: [https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) Pretrained sentence-transformer model (6-layer MiniLM, mean pooling, trained on 1B+ sentence pairs) Cited by: §7.3.

[^43]: M. Sharma, M. Tong, T. Korbak, D. Duvenaud, A. Askell, S. R. Bowman, E. DURMUS, Z. Hatfield-Dodds, S. R. Johnston, S. M. Kravec, et al. (2024) Towards understanding sycophancy in language models. In ICLR, Cited by: §1.

[^44]: M. Siliski (2025) Gemini adds temporary chats and new personalization features. Note: [https://blog.google/products/gemini/temporary-chats-privacy-controls/](https://blog.google/products/gemini/temporary-chats-privacy-controls/) Cited by: §1, §1, §2.

[^45]: G. Team, A. Kamath, J. Ferret, S. Pathak, N. Vieillard, R. Merhej, S. Perrin, T. Matejovicova, A. Ramé, M. Rivière, et al. (2025) Gemma 3 technical report. arXiv preprint arXiv:2503.19786. Cited by: §1, §7.1.

[^46]: E. Toch, Y. Wang, and L. F. Cranor (2012) Personalization and privacy: a survey of privacy risks and remedies in personalization-based systems. User Modeling and User-Adapted Interaction 22 (1). Cited by: §1.

[^47]: K. Vombatkere, S. Mousavi, S. Zannettou, F. Roesner, and K. P. Gummadi (2024) TikTok and the art of personalization: investigating exploration and exploitation on social media feeds. In ACM Web Conference, Cited by: §1, §2.

[^48]: C. Yang, S. Mousavi, A. Dash, K. P. Gummadi, and I. Weber (2025) Studying behavioral addiction by combining surveys and digital traces: a case study of tiktok. In AAAI ICWSM, Vol. 19. Cited by: §2, §3.

[^49]: S. Zannettou, O. Nemes-Nemeth, O. Ayalon, A. Goetzen, K. P. Gummadi, E. M. Redmiles, and F. Roesner (2024) Analyzing user engagement with tiktok’s short format video recommendations using data donations. In ACM CHI, Cited by: §2, §3.