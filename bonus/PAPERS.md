# Bonus: Multi-Agent / A2A 必读 8 篇 — 开发者视角

> 不是学术摘要，是"这篇论文教我什么能直接用到代码里的事"。  
> 全部 8 篇 arxiv ID 已校验真实，无虚构。

---

## 1. MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework
**arxiv.org/abs/2308.00352** (2023-08)

**问题**：多 agent 协作时，agents 互相 hallucinate、对齐失败、对话漂移，复杂软件任务做不下来。

**核心方法**：把人类 SOP（标准作业程序）编码进 agents——PM/Architect/Engineer/QA 各有 role prompt，**通过结构化中间产物（PRD、API 设计、流程图）通信而非自由对话**。每个 role 只读自己关心的 artifact section（"publish-subscribe"机制）。

**Takeaway**：别让 agents 自由聊天交换信息——定义 schema 化的 artifact（Pydantic / JSON Schema），让上游 agent 写 artifact，下游 agent 订阅。这把 agent 通信从 NLP 问题降级成数据管道问题，可观测可调试。

---

## 2. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation
**arxiv.org/abs/2308.08155** (2023-08)

**问题**：每搭一个 multi-agent 应用都从零写消息循环、工具调用、人类介入逻辑——重复造轮子。

**核心方法**：把所有交互抽象成 **conversable agents 互发消息**。Agent = (LLM + tools + human-in-the-loop) 的组合，靠 `register_reply` 钩子定义"收到消息怎么回"。GroupChat 是 agent 也是 message router。

**Takeaway**：把 agent 设计成**纯消息处理函数** `(message, sender) → reply`，不要纠结于"工作流引擎"。一个 agent 就是一个状态机+inbox。这个抽象让 swap LLM、加 tool、插 human approval 都是改一行配置——是今天 LangGraph/CrewAI 的祖宗模式。

---

## 3. CAMEL: Communicative Agents for "Mind" Exploration of LLM Society
**arxiv.org/abs/2303.17760** (2023-03)

**问题**：让两个 agent 协作完成任务时，对话很快退化（角色翻转、无限客套、提前宣布完成）。

**核心方法**：**Inception Prompting**——一个 task-specifier agent 先把模糊需求精炼成 specific task，然后 user-agent + assistant-agent 严格扮演角色循环对话。系统消息硬约束角色不可翻转，用结构化 `Instruction:/Input:` 格式强制推进。

**Takeaway**：agent 间对话必须有**强 protocol**（固定字段 + 转换状态机），自由 chat 必崩。代码里给每条消息加 `role`+`stage` 字段、加防御性 prompt（"don't role-flip, don't say task done unless X"），并设硬性 turn cap——agent 间通信永远预设"对方会越界"。

---

## 4. ChatDev: Communicative Agents for Software Development
**arxiv.org/abs/2307.07924** (2023-07)

**问题**：让 LLM 端到端写完整软件（不止 1 个文件），代码 hallucination 失控。

**核心方法**：瀑布式 pipeline（Design → Code → Test → Doc），每阶段双人对话（CTO+程序员、程序员+审查员）。引入 **communicative dehallucination**：审查 agent 主动提"含糊不清的细节"反问，强迫 coder 补全才能进下一步。

**Takeaway**：长任务用 **chain-of-pairs** 而非单一 super-agent。每个交付物前插一个"adversarial reviewer" agent 追问细节——这比加 reflection prompt 有效得多，因为追问 agent 没有"快点完工"的偏置。代码上：把 review pass 设成 pipeline 的 hard gate。

---

## 5. Voyager: An Open-Ended Embodied Agent with Large Language Models
**arxiv.org/abs/2305.16291** (2023-05)

**问题**：Agent 在开放环境（Minecraft）持续学习时，每个 session 重头开始，技能不沉淀。

**核心方法**：三件套——**automatic curriculum**（GPT 自己提下一个目标）+ **skill library**（把跑通的代码存成可调用 function，向量检索复用）+ **iterative prompting**（用环境反馈+错误信息自我修代码）。

**Takeaway**：给你的 agent 加一个 **skill cache**——任何成功执行过的工具组合（一段 Python、一个 SQL 查询、一个 shell 命令）存成命名 function 写回 vector DB。下次类似任务先 retrieve 再生成。这就是把 agent 从"每次重新推理"变成"积累一个个人 utility 库"。

---

## 6. Generative Agents: Interactive Simulacra of Human Behavior
**arxiv.org/abs/2304.03442** (2023-04)

**问题**：Long-running agent 没法维持一致的人格、关系、长期计划——上下文窗口装不下一周的记忆。

**核心方法**：三层 memory 架构——**memory stream**（原始事件流）+ **reflection**（定期对最近记忆做 abstraction，写成更高阶观察）+ **planning**（基于 reflection 推导 daily/hourly plan）。检索分数 = recency × importance × relevance 三者加权。

**Takeaway**：long-running agent 必须有**分层 memory**，不是简单的 vector store。代码层面：原始 log + LLM 周期性 summarize 成"insights" + insights 再 summarize 成"identity/goals"。检索时把 recency decay 和 LLM 打的 importance score 加进相似度排序——不然永远召回最相似但最无关的旧事件。

---

## 7. AgentVerse: Facilitating Multi-Agent Collaboration and Exploring Emergent Behaviors
**arxiv.org/abs/2308.10848** (2023-08)

**问题**：固定 role 的 multi-agent 系统不灵活；任务不同需要的专家组合也不同。

**核心方法**：4 阶段循环——**Expert Recruitment**（按任务动态 spawn 角色）→ **Collaborative Decision**（垂直/水平讨论）→ **Action Execution** → **Evaluation**（不达标退回重组）。Agent 阵容随任务自适应。

**Takeaway**：不要硬编码 agent roster——**先让一个 "recruiter" agent 读任务，决定召哪些 specialists**。代码里把 agent 定义抽成 registry（role_name → prompt + tools），recruiter 输出 role 列表，runtime 实例化。这把"什么 agent 做什么"从配置文件升级到 LLM 决策，处理新任务零代码改动。

---

## 8. Mixture-of-Agents Enhances Large Language Model Capabilities
**arxiv.org/abs/2406.04692** (2024-06)

**问题**：单个 LLM 有 ceiling，但简单 ensemble（多次采样投票）提升有限。

**核心方法**：**分层聚合**——Layer 1 多个异构 LLM 并行回答 → Layer 2 LLM 把这些 response 当 reference 重新生成（不是投票，是 *综合改写*）→ 多层堆叠。开源 MoA 在 AlpacaEval 上超过 GPT-4o。

**Takeaway**：质量瓶颈到了别堆 prompt——**做 N-of-M 采样 + aggregator agent**。代码模式：并行调用 3-5 个不同 model（Gemini Flash + Claude Haiku + GPT-5），把所有 output 喂给一个"synthesizer" prompt 重新写。比 single-shot 大模型便宜且更稳，特别适合 critical 任务的最后一公里。

---

## 速查表

| # | 论文 | 一句话精髓 |
|---|---|---|
| 1 | MetaGPT | Schema 化 artifact 通信 > 自由对话 |
| 2 | AutoGen | Agent = (msg, sender) → reply 的纯函数 |
| 3 | CAMEL | 强 protocol 约束 + 硬性 turn cap |
| 4 | ChatDev | 每个交付物前插 adversarial reviewer |
| 5 | Voyager | Skill cache：成功的代码存进 vector DB |
| 6 | Generative Agents | 三层 memory：raw → reflection → identity |
| 7 | AgentVerse | Recruiter agent 动态 spawn role |
| 8 | MoA | N-of-M 异构采样 + aggregator |

---

## 推荐阅读顺序

```
新手：2 (AutoGen) → 1 (MetaGPT) → 4 (ChatDev) — 理解 multi-agent 基本范式
进阶：6 (Generative) → 5 (Voyager) — 理解记忆 + 学习
高阶：3 (CAMEL) → 7 (AgentVerse) → 8 (MoA) — 理解 protocol + 动态化 + 集成
```
