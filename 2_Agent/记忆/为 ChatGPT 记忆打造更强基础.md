---
title: "为 ChatGPT 记忆打造更强基础"
source: "https://openai.com/zh-Hans-CN/index/chatgpt-memory-dreaming/?utm_source=chatgpt.com"
author:
published:
created: 2026-07-01
description: "ChatGPT 推出新的记忆系统，以更好地记住偏好，并在对话中保持上下文的新鲜和相关。"
tags:
  - "clippings"
---
2026年6月4日

[研究](https://openai.com/zh-Hans-CN/news/research/) [产品](https://openai.com/zh-Hans-CN/news/product-releases/) [发布](https://openai.com/research/index/release/)

改进 ChatGPT 中的记忆整合系统，以优化时效性、连续性和相关性

目录

今天，我们开始推出一个能力更强、可扩展性更高的记忆整合系统，旨在应对我们在将记忆应用于 ChatGPT 数亿用户和跨越多年时间跨度时观察到的陈旧性、正确性和可扩展性挑战。

记忆能帮助 ChatGPT 了解你的偏好、项目和限制，让未来的对话可以从共享上下文开始，而不是从零开始。

在过去两年里，记忆已成为 ChatGPT 体验中的关键部分，帮助 ChatGPT 更好地理解你的上下文，从而在一段时间内帮助你实现有意义的目标。这是让 ChatGPT 更有用的核心：了解你、帮助你，并为你做更多事。

这项更新今天面向美国的 Plus 和 Pro 用户开放，并将在未来几周内向更多国家以及免费版和 Go 用户推出。

## 记忆是如何演进的

记忆最初于 2024 年 4 月推出（也称为已保存记忆）。这项功能让你可以要求 ChatGPT 记住信息，并将其带入未来的聊天。

![Saved memories modal showing a searchable list of personal details, including work, interests, travel, and response preferences.](https://images.ctfassets.net/kftzwdyauwt9/6kVwo3uYRhe81W7gx1uGoR/c7c242fd100e910d28b451eada638b89/Saved_memories.png?w=3840&q=90&fm=webp)

已保存记忆只会在对话期间写入，并依赖强提示来决定何时触发记忆，例如指示“记住我七月要去新加坡旅行”。在实践中，与这个系统互动可能感觉像是在和一个记了几条笔记的人说话，但他仍然忘了所有没有写下来的内容。已保存记忆也往往会随着时间变得陈旧，并最终变得不正确或无关。

2025 年 4 月，我们更新了 ChatGPT 的记忆，让模型能够参考已保存记忆列表之外的聊天上下文；这是通过引入第一版 **“做梦”(Dreaming)** 功能来实现的 — 这是一种让 ChatGPT 通过参考聊天历史在后台 *自动* 整理记忆的方法。

![Memory settings page in ChatGPT showing options to reference chat history, use saved memories, manage saved memories, and enable Pulse memory suggestions.](https://images.ctfassets.net/kftzwdyauwt9/nSkMroPG2SPQCrcIUh2l4/bf05aa9cfb0287cfa7f187f9d84674dd/Memory_settings__1_.png?w=3840&q=90&fm=webp)

与已保存记忆不同，“做梦”功能利用后台流程，让 ChatGPT 能够从许多对话中学习并整合 ChatGPT 的记忆状态，从而始终为你的对话提供最新、最相关的上下文。“做梦”功能还让记忆更容易纳入对话中自然出现的上下文，而不必依赖明确要求记住某件事。

在过去一年里，“做梦”功能 *补充* 了已保存记忆，使 ChatGPT 个性化回复的能力实现了大幅提升，并抵消了已保存记忆的陈旧性。然而，从历史上看，它从来不足以作为一个独立的记忆系统。

今天，我们将推出一种基于“做梦”功能构建的、能力显著更强且计算效率更高的记忆架构。

由“做梦”功能整合出的记忆可通过记忆摘要页面中可见的摘要进行查看。通过记忆摘要，你可以快速了解 ChatGPT 对你的了解重点，添加或更新关于你自己的信息，并提供关于 ChatGPT 应在何时提起哪些话题的指示。如果你想深入了解某个特定领域，只需和模型聊天即可。

![Memory summary modal showing a personalized overview of a user’s work, hobbies, travel interests, and community involvement, with options to correct or dismiss specific details.](https://images.ctfassets.net/kftzwdyauwt9/7C8sUaE2XdajvQ8ckphLG5/326a719fbdcfbc3a85e8990155d5aaed/Memory_summary.png?w=3840&q=90&fm=webp)

## 我们如何评估记忆

当我们思考 ChatGPT 中“好的记忆”是什么样子时，会想到几点：

1. **延续有用的上下文：** 你告诉 ChatGPT 一次，它就会在你之后的聊天中记住这些信息。
2. **遵循偏好和限制：** 如果你描述了某个偏好（例如你是素食者），那么 ChatGPT 今后应采取与该偏好一致的行动。
3. **随时间保持最新：** 记忆应考虑时间的流逝。想象一下“用户正在为下周六的生日派对做计划”；最终，星期天会到来。

我们可以评估 ChatGPT Plus 和 Pro 的记忆在上述三个记忆目标上的改进情况。我们分别针对以下各项进行评估：

1. **2024** ：已保存记忆
2. **2025** ：已保存记忆 + Dreaming V0
3. **2026** ：Dreaming V3

## 延续上下文

当你与 ChatGPT 开始新的聊天时，不必从头介绍自己。ChatGPT 可以为你节省时间，并 *基于先前的上下文继续推进* ，尤其适用于复杂、长期进行的项目。

例如，想象你正在使用 ChatGPT 选购与你当前相机兼容的新相机设备。如果你过去曾与 ChatGPT 讨论过你的相机配置，你就可以询问与“我的摄影配置”兼容的产品，并获得符合你需求的定制推荐。

## GPT-5.2 Instant

What would I need to buy to use TTL for my underwater photography setup?

To use **TTL flash underwater**, you need a compatible chain from **camera → housing/trigger → cable → strobe**. What you buy depends mostly on whether your setup uses **fiber-optic TTL** or **electrical TTL**.

#### Basic shopping checklist

- **TTL-capable underwater strobe  
	**Look for strobes that support your TTL type, such as **Inon S-TTL**, **Sea & Sea DS-TTL**, **Ikelite DS TTL**, or compatible Backscatter/Nauticam systems. TTL has to be supported by the strobe, not just the camera.
- **TTL trigger or TTL converter  
	**This is the key piece. It translates your camera’s flash metering into something the underwater strobe can understand. Examples include **Nauticam optical TTL converters**, **Sea & Sea TTL converters**, **Backscatter Smart Control optical TTL triggers**, or **Ikelite DS Link TTL converters**, depending on housing and camera brand. Backscatter notes that Nauticam optical TTL converters can work with fiber-optic-connected Inon and Sea & Sea TTL strobes, while Ikelite’s DS Link converters are made around Ikelite DS strobes and electrical sync setups. ([Backscatter.com ⁠](https://www.backscatter.com/reviews/post/Underwater-Camera-and-Housing-TTL-Reference-Guide?utm_source=chatgpt.com))
- **Connection cable  
	**For **fiber optic TTL**, buy one fiber optic cable per strobe. Ikelite’s fiber-optic guide says each strobe needs its own light path, converter/adapter, and cord. ([Ikelite ⁠](https://www.ikelite.com/blogs/buying-guides/choosing-strobes-for-a-compact-fiber-optic-system?srsltid=AfmBOor6LitZ9VTa-x980CMwLUM7qfqGh-AiJrlkUCtYrL7oRV5aJmO4&utm_source=chatgpt.com))  
	For **electrical TTL**, buy the correct sync cord, such as Ikelite-style, Nikonos 5-pin, or housing-specific bulkhead cable.
- **Housing compatibility parts  
	**You may need a **hot-shoe adapter**, **bulkhead**, **fiber optic window/adapter**, or housing-specific TTL board. Many TTL triggers mount inside the housing on the camera hot shoe.
- **Strobe arms, clamps, tray, and mounting hardware  
	**TTL controls exposure, but you still need to physically mount and aim the strobes.
- **Batteries and spares  
	**Bring strobe batteries, trigger batteries if required, spare fiber optic cables or sync cord O-rings, and silicone grease for serviceable O-rings.

#### Which route should you choose?

**Fiber optic TTL** is usually easiest if your housing has optical ports or can use the camera’s pop-up flash/LED trigger. It is common with compact, mirrorless, Nauticam, Sea & Sea, AOI, and Olympus/OM TG-style setups.

**Electrical TTL** is often best if you use **Ikelite DS strobes** or an Ikelite-style housing/bulkhead. Ikelite says its DS Link TTL converters are faster and more reliable than fiber-optic TTL triggers, and they do not require batteries. ([Backscatter.com ⁠](https://www.backscatter.com/Ikelite-DL1-DS-Link-Nikon-TTL-Converter-Ikelite-Connector?utm_source=chatgpt.com))

#### The compatibility rule

You need all three to match:

**camera brand/protocol + housing/trigger type + strobe TTL system**

For example:

- Sony camera + Nauticam housing + optical TTL trigger + Inon/Sea & Sea-compatible fiber optic strobe
- Nikon/Canon/Sony camera + Ikelite housing/bulkhead + Ikelite DS Link TTL converter + Ikelite DS strobe
- Compact camera with built-in flash + fiber optic cable + S-TTL/DS-TTL-capable strobe

So the practical answer is: buy a **TTL-compatible strobe**, the **correct TTL trigger/converter for your camera and housing**, and the **right fiber optic or electrical sync cable**. The exact part numbers depend on your camera, housing, and strobe model.

*模型给出通用回应，让用户自行进行复杂的兼容性检查。*

## GPT-5.3 Instant

What would I need to buy to use TTL for my underwater photography setup?

I’ll verify this against your actual setup: Sony A1 II in Nauticam NA-A1II, with Backscatter Mini Flash 3 and Inon Z-330 strobes. The key question is whether you want TTL with the Mini Flash 3, the Z-330s, or both.

For **your setup** — **Sony A1 II + Nauticam NA-A1II + Backscatter Mini Flash 3 + Inon Z-330** — there are two different TTL paths:

#### Best buy for Mini Flash 3 TTL

Buy:

**Backscatter Smart Control TTL LED Nauticam Flash Trigger for Sony  
SKU: BS-TR-SN2**

Backscatter lists it as custom-designed for **Nauticam full-frame Sony housings**, TTL-compatible with **Mini Flash 3**, and the NA-A1II housing page offers it as the “Backscatter Smart Control TTL Flash Trigger” option. ([Backscatter.com ⁠](https://www.backscatter.com/Backscatter-Smart-Control-TTL-LED-Nauticam-Flash-Trigger-for-Sony))

You’d use normal optical fiber cables from the housing to the Mini Flash 3. On the MF-3, you’d use **SC** or **SC Macro** mode; Backscatter says SC / SC Macro are the TTL modes for Mini Flash 3, with SC Macro specifically tuned for close macro work. ([Backscatter.com ⁠](https://www.backscatter.com/Backscatter-Smart-Control-TTL-LED-Nauticam-Flash-Trigger-for-Sony))

#### For Inon Z-330 TTL

For the **Inon Z-330**, the relevant unit is:

**UW Technics 11075-HSS TTL Converter for Sony / Nauticam**

UW Technics explicitly lists **Inon Z-330** as a compatible TTL strobe and supports optical TTL output. ([UWTechnics ⁠](https://uwtechnics.com/product/11075-hss-ttl-converter-for-sony-for-nauticam-housings-na-a1-and-a7-a9/))

But I would **not** buy this for Mini Flash 3 TTL. Backscatter’s own UW Technics listing says Backscatter strobes are **manual / HSS only** on that converter, while the Backscatter Smart Control trigger is the one listed for Sony TTL with the Mini Flash 3. ([Backscatter.com ⁠](https://www.backscatter.com/UW-Technics-TTL-Converter-for-Sony-with-Nauticam-Underwater-Housings_2?utm_source=chatgpt.com))

#### Practical recommendation

Since you shoot macro and have the **Mini Flash 3**, I’d buy the **Backscatter Smart Control TTL LED Nauticam Flash Trigger for Sony — BS-TR-SN2**.

The catch: there probably is **no single trigger that gives true TTL for both the Mini Flash 3 and Inon Z-330 at the same time**. The Backscatter trigger is the right TTL solution for the MF-3; the UW Technics converter is the right TTL solution for the Z-330. So choose based on which strobe you actually want TTL for.

For your use case, I’d prioritize **Mini Flash 3 TTL / SC Macro** and treat the Z-330s as manual when needed.

*模型记得用户的相机配置，并推荐了兼容产品。*

*GPT‑5.2 Instant 虽然最终回答了问题，但为了解释其安全边界，加入了一段关于其* ***无法*** *提供何种帮助的冗长开场白。相比之下，GPT‑5.3 Instant 则直接进入正文回复。*

我们可以基于类似这样的示例构建评估，其中模型需要回应一个提示，而该提示要求它回忆关于用户的事实信息。如果模型以正确使用相关上下文的方式作出回应，就会获得奖励。在这项评估中，新的基于“做梦”功能的系统提升了模型回忆相关事实的能力。

事实回忆

<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="675" height="285.2" viewBox="0 0 675 285.2" style="background-color: transparent;"><g fill="none" stroke-miterlimit="10" transform="translate(48,5)"><g role="graphics-object" aria-roledescription="group mark container"><g transform="translate(0,0)"><g><g role="graphics-symbol" aria-roledescription="axis" aria-label="X-axis titled '任务成功' for a linear scale with values from 0 to 100"><g transform="translate(0.5,215.7)"><g><g pointer-events="none"><line transform="translate(0,0)" x2="0" y2="5" stroke="currentColor" stroke-width="1" opacity="1"></line><line transform="translate(121,0)" x2="0" y2="5" stroke="currentColor" stroke-width="1" opacity="1"></line><line transform="translate(243,0)" x2="0" y2="5" stroke="currentColor" stroke-width="1" opacity="1"></line><line transform="translate(364,0)" x2="0" y2="5" stroke="currentColor" stroke-width="1" opacity="1"></line><line transform="translate(486,0)" x2="0" y2="5" stroke="currentColor" stroke-width="1" opacity="1"></line><line transform="translate(607,0)" x2="0" y2="5" stroke="currentColor" stroke-width="1" opacity="1"></line></g><g pointer-events="none"><text text-anchor="middle" transform="translate(0,24)" font-family="SF Mono, monospace" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">0%</text> <text text-anchor="middle" transform="translate(121.4,24)" font-family="SF Mono, monospace" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">20%</text> <text text-anchor="middle" transform="translate(242.8,24)" font-family="SF Mono, monospace" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">40%</text> <text text-anchor="middle" transform="translate(364.2,24)" font-family="SF Mono, monospace" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">60%</text> <text text-anchor="middle" transform="translate(485.6,24)" font-family="SF Mono, monospace" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">80%</text> <text text-anchor="middle" transform="translate(607,24)" font-family="SF Mono, monospace" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">100%</text></g> <g pointer-events="none"><line transform="translate(0,0)" x2="607" y2="0" stroke="currentColor" stroke-width="1" opacity="1"></line></g><g pointer-events="none"><text text-anchor="middle" transform="translate(303.5,57)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="14px" font-weight="normal" fill="currentColor" opacity="1">任务成功</text></g></g></g></g> <g role="graphics-symbol" aria-roledescription="axis" aria-label="Y-axis for a discrete scale with 3 values: 2024, 2025, 2026"><g transform="translate(-3.5,0.5)"><g><g pointer-events="none"><text text-anchor="end" transform="translate(-10,45.099999999999994)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">2024</text> <text text-anchor="end" transform="translate(-10,109.1)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">2025</text> <text text-anchor="end" transform="translate(-10,173.10000000000002)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="12px" font-weight="normal" fill="currentColor" opacity="1">2026</text></g></g></g></g> <g role="graphics-object" aria-roledescription="group mark container"><g transform="translate(0,12.799999999999997)"><g clip-path="url(#clip1)"><g role="graphics-object" aria-roledescription="group mark container"><g transform="translate(0,0)"><g><g role="graphics-object" aria-roledescription="rect mark container"><path aria-label="任务成功: 41.5; year: 2024" role="graphics-symbol" aria-roledescription="bar" d="M0,0h251.905v57.6h-251.905Z" fill="currentColor" stroke="currentColor" stroke-width="1"></path></g></g></g></g></g></g><g transform="translate(0,76.8)"><g clip-path="url(#clip2)"><g role="graphics-object" aria-roledescription="group mark container"><g transform="translate(0,0)"><g><g role="graphics-object" aria-roledescription="rect mark container"><path aria-label="任务成功: 67.9; year: 2025" role="graphics-symbol" aria-roledescription="bar" d="M0,0h412.153v57.6h-412.153Z" fill="currentColor" stroke="currentColor" stroke-width="1"></path></g></g></g></g></g></g><g transform="translate(0,140.8)"><g clip-path="url(#clip3)"><g role="graphics-object" aria-roledescription="group mark container"><g transform="translate(0,0)"><g><g role="graphics-object" aria-roledescription="rect mark container"><path aria-label="任务成功: 82.8; year: 2026" role="graphics-symbol" aria-roledescription="bar" d="M0,0h502.59599999999995v57.6h-502.59599999999995Z" fill="currentColor" stroke="currentColor" stroke-width="1"></path></g></g></g></g></g></g></g><g role="graphics-object" aria-roledescription="text mark container"><text aria-label="adherence: 41.5; year: 2024; factual_recall: 41.5%" role="graphics-symbol" aria-roledescription="text mark" text-anchor="start" transform="translate(261.905,45.599999999999994)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="12px" fill="currentColor">41.5%</text> <text aria-label="adherence: 67.9; year: 2025; factual_recall: 67.9%" role="graphics-symbol" aria-roledescription="text mark" text-anchor="start" transform="translate(422.153,109.6)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="12px" fill="currentColor">67.9%</text> <text aria-label="adherence: 82.8; year: 2026; factual_recall: 82.8%" role="graphics-symbol" aria-roledescription="text mark" text-anchor="start" transform="translate(512.596,173.60000000000002)" font-family="OpenAI Sans, OpenAI Sans Variable Scripts, sans-serif" font-size="12px" fill="currentColor">82.8%</text></g></g></g></g></g><defs><clipPath id="clip1"><path d="M2,0L249.905,0C251.008830048988,0,251.905,0.896169951012,251.905,2L251.905,55.6C251.905,56.703830048988,251.008830048988,57.6,249.905,57.6L2,57.6C0.896169951012,57.6,0,56.703830048988,0,55.6L0,2C0,0.896169951012,0.896169951012,0,2,0Z"></path></clipPath><clipPath id="clip2"><path d="M2,0L410.153,0C411.25683004898804,0,412.153,0.896169951012,412.153,2L412.153,55.6C412.153,56.703830048988,411.25683004898804,57.6,410.153,57.6L2,57.6C0.896169951012,57.6,0,56.703830048988,0,55.6L0,2C0,0.896169951012,0.896169951012,0,2,0Z"></path></clipPath><clipPath id="clip3"><path d="M2,0L500.59599999999995,0C501.69983004898796,0,502.59599999999995,0.896169951012,502.59599999999995,2L502.59599999999995,55.6C502.59599999999995,56.703830048988,501.69983004898796,57.6,500.59599999999995,57.6L2,57.6C0.896169951012,57.6,0,56.703830048988,0,55.6L0,2C0,0.896169951012,0.896169951012,0,2,0Z"></path></clipPath></defs></svg>

## 遵循偏好

记忆还能帮助 ChatGPT 以更符合你的偏好和限制的方式作出回应。

想象你正在计划一次新加坡之旅。出发前两个月，你请 ChatGPT 帮忙制定行程。ChatGPT 已经从过去的旅行规划中知道，你喜欢野生动物摄影，偏好空调强劲的酒店，并且比起拥挤的酒吧更喜欢安静的晚餐。

## 继续阅读[Previewing GPT-5.6 Sol: a next-generation model](https://openai.com/zh-Hans-CN/index/previewing-gpt-5-6-sol/)

[

产品

](https://openai.com/zh-Hans-CN/index/previewing-gpt-5-6-sol/)[面向企业的新使用情况分析与更新后的支出控制](https://openai.com/zh-Hans-CN/index/chatgpt-enterprise-spend-controls/)

[

产品

](https://openai.com/zh-Hans-CN/index/chatgpt-enterprise-spend-controls/)