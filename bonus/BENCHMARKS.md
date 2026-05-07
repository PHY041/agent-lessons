# Bonus: Multi-Agent Benchmarks 深度调研

> 2026-05 最新数据。来源：HAL Princeton, SWE-bench, AgentBench, WebArena 官方 leaderboards + Berkeley RDI 研究。

---

## 1. 5 大核心 Benchmark 实时数据

> ⚠️ **Source 类型区分**（影响数字可信度）：
> - **官方** = 该 benchmark 自己的 leaderboard
> - **HAL/Steel** = 第三方学术 / community 维护的 leaderboard
> - **BenchLM** = 第三方聚合站点（model-page 数字，未必跟 official 完全对齐）
> - **官方公告** = 模型 vendor 自己宣布的数字

| Benchmark | 测什么 | 单 Agent Baseline | Multi-Agent SOTA | Source 类型 | 主流架构 |
|---|---|---|---|---|---|
| **GAIA** (466 题) | 通用 assistant：推理+多模态+浏览+工具 | GPT-5 Mini bare 44.8% | OPS-Agentic-Search **92.4%** / HAL+Sonnet 4.5 74.6% | HAL/Steel community | Scaffolded planner + tool-use ensemble |
| **SWE-bench Verified** (500 任务) | 真实 GitHub bug fix | mini-SWE-agent ReAct ~50% | Claude Mythos Preview **93.9%** / Opus 4.7 Adaptive 87.6% | BenchLM (model-page) | Multi-rollout + review/critic agent |
| **AgentBench** (8 环境) | OS/DB/Web/卡牌/家居 全栈 | GPT-4 ~4.0/10 | 分环境差异巨大，整体 SOTA <6.5/10 | 官方（THUDM）| 注意：聚合分掩盖单环境 0 分塌陷 |
| **WebArena** (812 任务, 5 站点) | 真实网站多步操作 | 早期 14% | Claude Mythos Preview **68.7%** | BenchLM (model-page) | Planner + Executor + Memory 三层 |
| **Magentic-One/Bench** | 异构模态协作 | 单 agent baseline | Orchestrator + specialists **+3-4pp** | 官方（Microsoft）| Hierarchical, ledger-based 任务台账 |

---

## 2. 关键洞察（**对工程决策有用**）

### Insight #1 — Scaffold > Model

GAIA 上加 framework 加分约 **+30pp**（44.8 → 74.6）。

**意味着**：架构选对**比换更强模型重要**。一个 scaffolded GPT-4 可以打败 bare 的 Claude Opus。

### Insight #2 — 公开 benchmark 不可信

Berkeley RDI 2026-04-12 实证：8 个主流 benchmark 都能被 reward hacking 攻破。

OpenAI 已**停报 SWE-bench**——前沿模型训练污染严重。

**意味着**：必须自建 held-out 私有集才有真信号。

### Insight #3 — 聚合分会塌陷

AgentBench 综合 70% 可能是"6 个环境 90% + 2 个环境 0%"。

**意味着**：要看 **per-environment floor**，不只是平均。worst-environment 0 分意味着遇到长尾任务直接挂。

### Insight #4 — Multi-agent 经常不划算

Anthropic 自家 Multi-Agent Research：**+90.2% accuracy 但 15x token 消耗**。

**意味着**：只有"信息密集 + 单次价值高"的任务（深度研究、合规审查）才值 multi-agent。日常任务用单 agent 更经济。

---

## 3. 评估脚本（**30 行 Python，可直接跑**）

完整代码见 `../labs/lab5/eval_agent.py`，关键逻辑：

```python
def evaluate(agent_fn, dataset: list[dict], n_seeds: int = 3) -> dict:
    """4 维评估：accuracy / token_cost / latency / robustness"""
    results = []
    for task in dataset:
        per_seed = []
        for _ in range(n_seeds):  # robustness = 跨 seed 一致性
            t0 = time.perf_counter()
            try:
                out = agent_fn(task["question"])
                ok = str(out["answer"]).strip().lower() == str(task["gold"]).strip().lower()
                per_seed.append({
                    "ok": ok,
                    "latency": time.perf_counter() - t0,
                    "cost": out["tokens_in"] * 3e-6 + out["tokens_out"] * 1.5e-5,
                })
            except Exception as e:
                per_seed.append({"ok": False, "latency": 0, "cost": 0, "err": str(e)})
        # 汇总每题 4 维
        results.append({...})
    return {
        "accuracy": ...,
        "robustness": ...,    # 跨 seed 一致比例
        "p50_latency": ...,
        "total_cost_usd": ...,
    }
```

---

## 4. 3 条铁律（**实操层面**）

```
┌─────────────────────────────────────────────────────────────┐
│ ① 先建 30-50 题私有 held-out 集，再跑公开 bench              │
│   公开 bench 数据污染 + reward hacking 严重，私有集才是真信号│
├─────────────────────────────────────────────────────────────┤
│ ② 永远同时报 4 维（accuracy + cost + latency + robustness）  │
│   ≥3 seeds。+5pp accuracy 但 cost×3 不报你会做错决策         │
├─────────────────────────────────────────────────────────────┤
│ ③ AgentBench 类聚合分要看 per-env 拆解                       │
│   "70% 综合"可能是"6 个 90% + 2 个 0%"，长尾会塌陷            │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 决策矩阵 — 该不该上 multi-agent

| Accuracy 提升 | Cost 涨幅 | 决策 |
|---|---|---|
| +20pp | <2x | ✅ 上 swarm |
| +10pp | 2-3x | ⚠️ 看具体场景（用户单次价值多大）|
| +5pp | >3x | ❌ 单 agent 够了 |
| 持平或下降 | 任何 | ❌ swarm 错配场景 |

---

来源：
- [HAL: GAIA Leaderboard (Princeton)](https://hal.cs.princeton.edu/gaia)
- [Steel.dev GAIA Leaderboard](https://leaderboard.steel.dev/leaderboards/gaia/)
- [SWE-bench Leaderboards](https://www.swebench.com/)
- [SWE-bench Verified 2026 (BenchLM)](https://benchlm.ai/benchmarks/sweVerified)
- [WebArena Benchmark 2026](https://benchlm.ai/benchmarks/webArena)
- [AgentBench (THUDM, ICLR'24)](https://github.com/THUDM/AgentBench)
- [AI Agent Framework Scorecard 2026](https://rapidclaw.dev/blog/ai-agent-benchmarks-2026)
- [Berkeley RDI Trustworthy Benchmarks](https://rdi.berkeley.edu/blog/trustworthy-benchmarks-cont/)
- [Beyond Accuracy: Enterprise Agentic Eval Framework (arXiv:2511.14136)](https://arxiv.org/html/2511.14136v1)
