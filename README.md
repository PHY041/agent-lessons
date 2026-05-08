# A2A 协议研究 + 实操教程

> **Agent-to-Agent 全景研究** — MCP / Google A2A / ANP / ACP 协议对比 + 5 lab 实操 + 8 篇必读论文。  
> 每节都有真代码、真数据、真使用场景，写给想"知道能做什么、精确到代码层面"的开发者。

---

## 📚 仓库结构

```
a2a-research/
├── README.md                 ← 你在这里
├── tutorial.pdf              ← 完整 PDF 版本
├── labs/
│   ├── lab1/                 看穿 MCP 协议
│   │   ├── LESSON.md
│   │   └── toy_mcp_server.py    50 行 Python MCP server
│   ├── lab2/                 A2A 协议对比
│   │   ├── LESSON.md
│   │   └── a2a_agent.py         FastAPI 实现 Google A2A
│   ├── lab3/                 Pipeline 拓扑实战
│   │   ├── LESSON.md
│   │   └── pipeline_demo.md     Claude Code 5-agent 流水线
│   ├── lab4/                 Swarm + HNSW 记忆
│   │   ├── LESSON.md
│   │   └── swarm_test.sh        Ruflo hive-mind 实测脚本
│   └── lab5/                 评估
│       ├── LESSON.md
│       ├── eval_agent.py        30 行 4 维评估脚本
│       └── eval_set.jsonl       样例 held-out 集
└── bonus/
    ├── A2A_DEEP_DIVE.md      4 大协议生态深研（MCP/A2A/ACP/ANP）
    └── BENCHMARKS.md         Multi-agent benchmark 最新数据
```

---

## 🎯 学完你会

| Lab | 学完会的事 |
|---|---|
| **Lab 1** | 自己写 50 行 Python MCP server；看穿 Claude Code 跟工具之间在塞什么 JSON |
| **Lab 2** | 知道 MCP / A2A / ACP / ANP 4 大协议各管什么；什么时候用哪个 |
| **Lab 3** | 用 Claude Code Agent tool 起 5 个命名 agent 跑 pipeline；用 SendMessage 真实流转 |
| **Lab 4** | 用 Ruflo 起 hive-mind swarm；理解 HNSW vector memory 怎么共享经验 |
| **Lab 5** | 写 30 行评估脚本，4 维度（accuracy/cost/latency/robustness）测自己的 swarm |

---

## 🚀 快速开始

### 1. Clone

```bash
git clone https://github.com/PHY041/agent-lessons.git ~/Desktop/agent-lessons
cd ~/Desktop/agent-lessons
```

### 2. 跑 Lab 1（5 分钟验证你的环境 OK）

```bash
cd labs/lab1
printf '%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"echo","arguments":{"text":"hello a2a"}}}' \
  | python3 toy_mcp_server.py
```

应该看到 3 条 JSON-RPC 响应。**这就是完整的 MCP 协议**。

### 3. 按顺序读 Lab 1 → Lab 5

每节 ~25-40 分钟。

---

## 📖 推荐阅读顺序

```
Lab 1 (MCP 基础)
   ↓
Lab 2 (A2A 协议生态) ←──────┐
   ↓                         │
Lab 3 (Pipeline 实战)        │  bonus/A2A_DEEP_DIVE.md
   ↓                         │  （想看协议生态全貌时读）
Lab 4 (Swarm + 记忆)         │
   ↓                         │
Lab 5 (评估) ←───────────────┤
                             │  bonus/BENCHMARKS.md
                             │  （想看公开 leaderboard 数据时读）
```

---

## ⚠️ 必读警告

学完任何 lab 之前，先读 Cognition 的反对派文章：  
**[Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)**

不是所有问题都该 multi-agent。单 agent 经常更优。

---

## 🛠 环境要求

| 工具 | 版本 | 用途 |
|---|---|---|
| Python | 3.10+ | Lab 1, Lab 2, Lab 5 |
| Node / npm | 18+ | Lab 4 (Ruflo) |
| Claude Code | 最新 | Lab 3 |
| FastAPI + uvicorn | 任意 | Lab 2（`pip install fastapi uvicorn`）|

---

## 📊 真实使用场景（每个 lab 都列了）

学完不是收藏夹吃灰。每节 lab 都给了 4 个具体场景告诉你"能用在哪"：

- 给 Claude Code 接私有数据源
- 跨进程 / 跨机器 agent 协作
- 5-agent feature dev pipeline
- Hive-mind 调研任务
- 给自己的 swarm 做 4 维评估

---

## 🎓 学完之后

1. **选一个真实项目**用 5-lab 学到的东西重做一遍
2. **建 30-50 题私有 held-out 集**评估你的 multi-agent 系统
3. **读 bonus 章节**了解协议生态全貌
4. **关注 Cognition + Anthropic 工程博客**——这两家最敢说 multi-agent 实话

---

## 📜 License

MIT — 完整 license 文本见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- 教程基于 [`claude-peers-mcp`](https://github.com/anthropics/claude-code-mcp-examples) 真实代码做解剖
- 协议数据来自 [MCP](https://modelcontextprotocol.io/) / [A2A](https://github.com/a2aproject/A2A) 官方 spec
- Benchmark 数据来自 HAL Princeton / SWE-bench / AgentBench 公开 leaderboard
- Ruflo 信息来自 [ruvnet/ruflo](https://github.com/ruvnet/ruflo)（前 Claude Flow）

写这份教程是为了把"agent 之间到底怎么协作"这件事讲清楚——不是营销 hype，是代码层面真懂。

---

🤖 教程结构 + 代码示例由 Claude（Anthropic）协助生成，并经过 OpenAI Codex 独立 review 校验关键 fact。协议生态演进很快——本教程是 2026-05 的 snapshot；阅读时请以官方 spec 为准（每节末尾都有官方链接）。
