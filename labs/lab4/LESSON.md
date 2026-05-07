# Lab 4 — Swarm + HNSW 向量记忆

> **学完你会**：用 Ruflo 起一个真正的 swarm（>5 agent 并发），让它们共享 HNSW vector memory，看持久化记忆怎么改写 multi-agent 的可能性。

---

## 1. 为什么单纯 pipeline 不够？

回顾 Lab 3 的 pipeline:
```
researcher → architect → coder → tester → reviewer
```

它解 60% 场景。但有 40% 是它解不了的：

| 场景 | Pipeline 卡在哪 |
|---|---|
| 不知道任务多长（探索式） | 没法预先排 stage |
| 同时要 5 个角度（多视角生成） | 顺序串行慢 |
| Agent 互相要参考过去任务的输出 | 没有共享记忆 |
| 任务可能失败，需要 voting | 没有共识机制 |

**Swarm 拓扑** 解这些问题。

---

## 2. Swarm 的 3 个核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   ① Topology (拓扑)                                          │
│      mesh / hive-mind / hierarchical / adaptive              │
│      决定 agent 之间怎么通信                                 │
│                                                              │
│   ② Shared Memory (共享记忆)                                 │
│      HNSW vector store / SQLite / Redis                      │
│      让 agent 跨任务记住经验                                 │
│                                                              │
│   ③ Coordination Strategy (共识)                             │
│      consensus / voting / Byzantine / Raft                   │
│      错了怎么纠正、冲突怎么解                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Ruflo 实战 — 升级到 --full

> **前置**（Lab 4 第一次跑要做）：先建一个 sandbox 目录并 init Ruflo。如果你跟 Lab 1 走完了创建 `~/Desktop/ruflo-spike` 那就跳过这一步；否则：
>
> ```bash
> mkdir -p ~/Desktop/ruflo-spike && cd ~/Desktop/ruflo-spike
> npx -y ruflo@latest init --minimal --no-global  # 先 init 出基础结构
> ```

升级到 `--full` 看真本事（137 skills + HNSW + neural）：

```bash
cd ~/Desktop/ruflo-spike
npx -y ruflo@latest init --full --no-global --force
```

> ⚠️ `--no-global` 防止 Ruflo 改你的 `~/.claude/CLAUDE.md`（issue #1744）。生产 setup 不带这个 flag 就会污染全局配置。

**对比表**：

| 项 | minimal | full |
|---|---|---|
| Skills | 8 | **137+** |
| HNSW vector memory | ❌ | ✅ |
| Self-Learning Bridge | ❌ | ✅ |
| Memory Graph (PageRank) | ❌ | ✅ |
| Neural pattern training | ❌ | ✅ |
| Sessions persistence | 基础 | 全量 |

---

## 4. HNSW Vector Memory — agent 之间怎么共享经验

### HNSW 是什么

**Hierarchical Navigable Small World** 是当前最快的向量近邻搜索算法。Ruflo 内嵌的 AgentDB 用 HNSW 做记忆检索。

为什么不直接用 Postgres + pgvector？因为：

| | Postgres + pgvector | HNSW (in-process) |
|---|---|---|
| 网络往返 | 有 | 无 |
| 延迟 | ~5-50ms | <0.05ms |
| 部署 | 需要 DB | 嵌入式 |
| 适合 | 大数据量 | 单机 swarm |

**Ruflo 声称 150x-12,500x 加速**——主要因为消除网络 IO。

### 真实使用模式

```bash
# 一个 agent 写记忆
ruflo memory store \
  --namespace "canmarket-research" \
  --key "competitor-style-genome-2026" \
  --value "..." \
  --tags "brand,research,2026"

# 另一个 agent 检索
ruflo memory search \
  --namespace "canmarket-research" \
  --query "what styles do competitors use" \
  --top-k 5
```

### 关键：memory namespace

不同任务隔离，避免污染：

```
canmarket-research/
canmarket-content/
twitter-pipeline/
sc4062-image-agent/
```

---

## 5. Hive-Mind 拓扑 — Queen-Worker 模式

```
                ┌──────────┐
                │  Queen   │  (规划 + 路由)
                └────┬─────┘
              ┌─────┴─────┐
              ↓     ↓     ↓
          ┌─────┐ ┌─────┐ ┌─────┐
          │ W1  │ │ W2  │ │ W3  │  (并行执行)
          └─────┘ └─────┘ └─────┘
              ↑     ↑     ↑
              └─────┴─────┘
                    ↓
                 共享 HNSW memory
```

**Queen 干什么**：
- 拆任务（goal decomposition）
- 路由到合适的 worker（基于 worker 历史成功率，Q-Learning）
- 共识 / 投票决策

**Worker 干什么**：
- 执行单一明确任务
- 写结果进共享 memory
- 报告给 Queen

### 启动一个 hive-mind

```bash
cd ~/Desktop/ruflo-spike

# 1. 装齐
npx -y ruflo@latest init --full --no-global --force

# 2. 起 daemon
ruflo daemon start

# 3. 初始化 swarm
ruflo swarm init --topology hive-mind --max-agents 8

# 4. 给个目标
ruflo task create \
  --goal "Research top 5 brand-memory startups, summarize their tech stack"
```

Ruflo 会自动：
1. Queen 把任务拆成 5 个独立调研
2. Spawn 5 worker（每个负责一个 startup）
3. Workers 写结果到共享 HNSW memory
4. Queen 汇总输出

---

## 6. 真实使用场景（**对你直接有用**）

### 场景 ① SC4062 Grounded Image Agent
- 你已有的项目，需要 multi-step ReAct（20 步）
- Hive-mind 适配：Queen 规划，Workers 做 retrieve / generate / verify
- HNSW memory 存"哪些 prompt 生成质量好"，下次复用

### 场景 ② Twitter Pipeline 跨 Mac swarm
- Server (64GB) + Portable (48GB) 通过 Tailscale 互通
- Server 跑爬虫 worker，Portable 跑 LLM 生成 worker
- 共享 memory 存"哪些 tweet 拿到高互动"

### 场景 ③ CanMarket 4-Agent 升级
- 当前是 OpenClaw 原生 a2a
- 加 Ruflo 一层：HNSW memory 存"哪些 strategy 转化率高"
- Designer agent 调用记忆做 reference

### 场景 ④ Knowledge worker 重活
- 写报告 / 做调研 / 多源汇总
- Hive-mind 比 pipeline 快（并行）+ 共享 memory（不重复劳动）

---

## 7. Swarm 反模式（不是所有问题都该 swarm）

⚠️ **避免 swarm 的场景**：

| 场景 | 为什么 |
|---|---|
| 任务 < 5 步 | 起 swarm 的 overhead 大于收益 |
| 强顺序依赖 | swarm 的并行优势用不上 |
| 创意 / 设计任务 | 投票会平庸化结果 |
| 调试 / 修 bug | 单一上下文更可靠（Devin 2.0 选择） |

**判断标准**：你的任务能拆成 ≥3 个独立子任务吗？能 → 考虑 swarm。不能 → 用 pipeline / 单 agent。

---

## 8. 动手实验

`swarm_test.sh` 在本目录。要跑请确保：
1. `~/Desktop/ruflo-spike` 已 `init --full`
2. 装了 ONNX runtime（`npm install @xenova/transformers` 自动）
3. 有 Anthropic API key

跑通预期：
- Queen 输出任务拆解（看 `.claude-flow/logs/`）
- 5 个 worker 并发跑（每个 ~30-60s）
- 最终输出在 `.claude-flow/data/results/`

---

## 9. 关键 Takeaway

```
┌─────────────────────────────────────────────────────────────┐
│ ① Swarm = topology + shared memory + coordination           │
│   缺一不可。光并发不叫 swarm，那叫 fan-out                  │
├─────────────────────────────────────────────────────────────┤
│ ② HNSW vector memory 是 swarm 的"工作记忆"                  │
│   能 in-process 嵌入是关键性能优势                          │
├─────────────────────────────────────────────────────────────┤
│ ③ Hive-Mind 适配"调研 / 多视角 / 探索式"任务                │
│   不适配创意 / 调试 / 强顺序                                │
└─────────────────────────────────────────────────────────────┘
```

下一节 → **Lab 5: 评估** 教你怎么科学地证明你的 swarm 比单 agent 强。
