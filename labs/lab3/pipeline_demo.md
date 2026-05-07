# Lab 3 动手 — Mini Pipeline Demo

把下面这段 prompt 复制到 Claude Code 里跑：

---

请用 Agent tool 起 3 个命名 agent 跑一个 mini pipeline，每个 agent 用 `SendMessage` 把结果传给下一棒：

**Agent 1: researcher**
- subagent_type: general-purpose
- name: researcher
- run_in_background: true
- prompt: 读 `~/Desktop/agent-lessons/labs/lab1/LESSON.md`，提取 3 个关于 MCP 协议的关键概念。然后 SendMessage 给 'summarizer'，message 里包含这 3 个概念。

**Agent 2: summarizer**
- subagent_type: general-purpose
- name: summarizer
- run_in_background: true
- prompt: 等 'researcher' 发来 3 个概念。把它们压缩成 **1 个英文句子**（不超过 20 词）。然后 SendMessage 给 'critic'，message 是这句话。

**Agent 3: critic**
- subagent_type: general-purpose
- name: critic
- run_in_background: true
- prompt: 等 'summarizer' 发来 1 句话。从 3 个维度评价：(1) 是否准确反映 MCP 核心 (2) 是否清晰 (3) 是否够 20 词。最后输出"PASS / FAIL: 理由"。

启动后用 `SendMessage` 给 'researcher' 发：`"Start"`。

最后把 critic 的最终判断报给我。

---

## 预期观察

1. 3 个 agent 在 background 状态启动
2. 每个 agent 等前一棒，收到消息才开干
3. 最后 critic 输出 PASS/FAIL 给主 agent
4. 主 agent 报告给你

## 看什么细节

- agent 之间的 `SendMessage` 调用次数 = 3 次（含启动信号）
- critic 收到的应该是压缩后的句子，不是原 3 个概念（否则 summarizer 没干活）
- 总耗时约 30-60 秒（3 个 agent 串行 + 通信开销）

## 进阶玩法（教程外）

把 critic 的输出反馈到 summarizer，做迭代：

```
researcher → summarizer ↔ critic (loop until PASS)
```

这就从 pipeline 升级到 **supervisor with feedback loop**。
