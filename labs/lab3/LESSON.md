# Lab 3 — Pipeline 拓扑实战

> **学完你会**：用 Claude Code 内置的 Agent tool 起 5 个**命名 agent**，让它们用 `SendMessage` 真实流转，看 multi-agent pipeline 怎么落地。

---

## 1. 拓扑入门 — 4 大经典模式

```
① Pipeline (流水线)
   A → B → C → D
   适用：顺序依赖（feature dev: research → design → code → test）

② Fan-out (扇出)
   Lead → A, B, C → Lead
   适用：独立并行（research 多角度同时调研）

③ Supervisor (主从)
   Lead ↔ workers (双向反复)
   适用：复杂 refactor，主管持续指挥

④ Hive-Mind / Swarm
   Queen → Workers (with consensus)
   适用：大规模并发，要 voting
```

本课重点 **Pipeline**（最简单，覆盖 60% 真实场景）。

---

## 2. Claude Code 原生 Agent tool（这是核心武器）

Claude Code 自带 `Agent` 工具，能 spawn 命名子 agent。每个 agent 是独立 child process：

```javascript
// Claude Code 主线程里：
Agent({
  description: "Research the codebase",
  prompt: "Find all auth-related files. SendMessage findings to 'architect'.",
  subagent_type: "general-purpose",
  name: "researcher",                    // ← 关键：命名后可被 SendMessage 寻址
  run_in_background: true                // ← 后台跑，主线程继续
})
```

**`name` 参数让 agent 互相寻址成为可能**——没有名字就只能等 promise.all，没法做复杂协调。

---

## 3. 真实例子 — 5-Agent Feature Dev Pipeline

### 场景设定

你要实现一个新 feature："给 CanMarket 加 PDF 导出"。

5 个 agent 串成 pipeline：

```
researcher → architect → coder → tester → reviewer
   ↓             ↓          ↓        ↓         ↓
 找代码      画方案    写实现    写测试    评审
```

### 完整 spawn 代码

```javascript
// 一次性 spawn 5 个 agent，每个都知道下一棒是谁
Agent({
  description: "Research existing export code",
  prompt: `Search the codebase for existing export functionality
           (CSV, JSON, etc). Find patterns we can reuse.
           When done, SendMessage to 'architect' with findings.`,
  subagent_type: "general-purpose",
  name: "researcher",
  run_in_background: true
})

Agent({
  description: "Design PDF export architecture",
  prompt: `Wait for 'researcher' to send findings.
           Design how PDF export should integrate.
           SendMessage to 'coder' with: 1) files to modify,
           2) new files to create, 3) library choice (weasyprint/wkhtmltopdf).`,
  subagent_type: "general-purpose",
  name: "architect",
  run_in_background: true
})

Agent({
  description: "Implement PDF export",
  prompt: `Wait for 'architect' to send design.
           Implement the code. Run linter.
           SendMessage to 'tester' with: list of files changed,
           how to invoke the new feature.`,
  subagent_type: "general-purpose",
  name: "coder",
  run_in_background: true
})

Agent({
  description: "Write tests for PDF export",
  prompt: `Wait for 'coder' to send change list.
           Write unit + integration tests. Run them.
           SendMessage to 'reviewer' with: test results, coverage report.`,
  subagent_type: "general-purpose",
  name: "tester",
  run_in_background: true
})

Agent({
  description: "Code review",
  prompt: `Wait for 'tester' to send test results.
           Review all changed code for: security, perf, style.
           Output a final verdict: ship / hold / changes requested.`,
  subagent_type: "code-reviewer",
  name: "reviewer",
  run_in_background: true
})

// 启动 pipeline
SendMessage({
  to: "researcher",
  summary: "Start PDF export pipeline",
  message: "Begin research phase. Goal: implement PDF export for CanMarket."
})
```

### 流转图

```
[Lead 你]
   │ SendMessage
   ↓
[researcher] ──findings──→ [architect] ──design──→ [coder]
                                                      │
                                                      │ change-list
                                                      ↓
                            [reviewer] ←──results── [tester]
                                │
                                ↓ verdict
                              [Lead 你]
```

---

## 4. SendMessage 协议细节

`SendMessage` 是 Claude Code 内置工具（不是 MCP，是 native）：

```javascript
SendMessage({
  to: "architect",                     // 目标 agent name
  summary: "Research findings ready",  // 短摘要（30 字内）
  message: "...detailed findings..."   // 实际内容
})
```

被消息的 agent 收到时长这样（在它的 conversation 里出现）：

```
<channel source="agent" from="researcher" summary="Research findings ready" ts="...">
...detailed findings...
</channel>
```

**关键点**：被消息的 agent **会立刻打断当前任务响应**——这是 PUA 机制（你的 system reminder 也用这个机制）。

---

## 5. 跟 claude-peers 的对比

| 维度 | Claude Code Agent + SendMessage | claude-peers MCP |
|---|---|---|
| 寻址方式 | 名字（同一 session 内） | peer ID（跨 session） |
| 进程边界 | 同一 Claude 主进程的 children | 不同 Claude Code 实例 |
| 用途 | 单个任务的多步骤协作 | 不同人 / 不同项目的 Claude 互相找 |
| 实现 | Anthropic 内置 | 第三方 MCP（你装了）|
| 持久化 | 任务结束即销毁 | broker SQLite，跨 restart |

**你应该这么选**：
- 单任务复杂协作 → Agent + SendMessage
- 跨终端、跨项目互通 → claude-peers
- 跨机器（Server + Portable）→ claude-peers + Tailscale

---

## 6. 真实使用场景（**已经 shipped 的**）

### 场景 ① Anthropic 自己的 Research 系统
- Anthropic 公开了 multi-agent research 架构
- Opus 4 作为 lead，Sonnet 4 作为 subagents（fan-out 模式）
- **+90.2% accuracy** vs 单 agent，但 token 消耗 **15x**
- 阅读：https://www.anthropic.com/engineering/multi-agent-research-system

### 场景 ② Claude Code 自己的 sub-agents
- 你看到的 Explore / planner / code-reviewer / security-reviewer 都是这个机制
- Anthropic 把它们做成 markdown 配置文件，用户一键调用

### 场景 ③ gstack 的 /office-hours → /plan-eng-review → /ship
- 这个流水线本质就是 pipeline 拓扑
- 每个 skill 是 stage，stage 间通过 markdown 文件传 artifact
- 你已经在每天跑

### 场景 ④ CanMarket 4-Agent
- intel → strategist → designer → data-sci
- 你的产品已经在用 pipeline 拓扑

---

## 7. Pipeline 反模式 — Cognition 的反对派论点

⚠️ **必读**：Cognition Labs（做 Devin 的）写过一篇 "Don't Build Multi-Agents"：
https://cognition.ai/blog/dont-build-multi-agents

核心观点：
1. **多 agent 上下文丢失严重**——subagent 不知道 lead 看过什么
2. **指令漂移**——每多一层传话，意图就模糊一点
3. **Devin 2.0 故意单 agent**——多个 Devin 实例并行而不是协作

**所以什么时候用 pipeline？**
- 任务**强可拆**（research / design / code / test 是独立专业）
- 每段输出**人类也能看懂**（接力时不靠隐式上下文）
- **错了能 retry**（比如 reviewer 拒了打回 coder）

什么时候**不**用：
- 持续探索性任务（不知道下一步是啥）
- 状态高度耦合（共享内存模型）
- 模糊创意工作（设计 / 写作）

---

## 8. 动手实验

`pipeline_demo.md` 在本目录，里面是一段你可以**直接喂给 Claude Code** 的 prompt：

```
请用 Agent tool 起 3 个 agent 跑一个 mini pipeline：

1. researcher (general-purpose)
   - 读 ~/Desktop/agent-lessons/README.md
   - 提取 3 个关键概念
   - SendMessage 给 'summarizer'

2. summarizer (general-purpose)  
   - 等 researcher
   - 把 3 个概念压缩成 1 句话
   - SendMessage 给 'critic'

3. critic (general-purpose)
   - 等 summarizer
   - 评价那句话："清楚 / 模糊 / 错"

最后把 critic 的判断报告给我。
```

---

## 9. 关键 Takeaway

```
┌─────────────────────────────────────────────────────────────┐
│ ① Agent + name + SendMessage = 同 session multi-agent       │
│   不需要 MCP / 不需要 broker                                │
├─────────────────────────────────────────────────────────────┤
│ ② Pipeline 拓扑解 60% 真实场景                              │
│   research → design → code → test → review 是黄金模式       │
├─────────────────────────────────────────────────────────────┤
│ ③ 用 multi-agent 前先读 Cognition 反对派                    │
│   不是所有问题都该 multi-agent — 单 agent 经常更优          │
└─────────────────────────────────────────────────────────────┘
```

下一节 → **Lab 4: Swarm + HNSW 记忆** 看 Ruflo 怎么做大规模并发 + 持久化记忆。
