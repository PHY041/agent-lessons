# Lab 5 — 评估：科学证明你的 swarm 比单 agent 强

> **学完你会**：知道 multi-agent 系统怎么科学评估——不是只看 accuracy，要看 4 维（accuracy / token cost / latency / robustness）。能写一个 30 行的评估脚本跑自己的 held-out 集。

---

## 1. 为什么必须做评估？

multi-agent 系统的常见**幻觉**：

❌ "我加了 5 个 agent，accuracy 涨了 5%！" — 但 token 成本涨了 3x，延迟涨了 4x，可能根本不划算
❌ "公开 benchmark 我们 SOTA！" — 公开 benchmark 训练数据污染严重，私有任务可能塌陷
❌ "看起来更好了" — 没有 baseline，没有 multi-seed，没有置信区间

**底层逻辑**：multi-agent 加 accuracy 经常是在牺牲 cost / latency / robustness 换的。**单看一维评估会做错架构决策**。

---

## 2. 5 个核心 Benchmark（**真实数据，2026 年最新**）

| Benchmark | 测什么 | 单 Agent Baseline | Multi-Agent SOTA | 主流架构 |
|---|---|---|---|---|
| **GAIA** (466 题) | 通用 assistant：推理+多模态+浏览+工具 | GPT-5 Mini bare 44.8% | OPS-Agentic-Search **92.4%** / HAL+Sonnet 4.5 74.6% | Scaffolded planner + tool-use ensemble |
| **SWE-bench Verified** (500 任务) | 真实 GitHub bug fix | mini-SWE-agent ReAct loop ~50% | Claude Mythos Preview **93.9%** / Opus 4.7 Adaptive 87.6% | Multi-rollout + review/critic agent |
| **AgentBench** (8 环境) | OS/DB/Web/卡牌/家居 全栈 agent | GPT-4 ~4.0/10 综合 | 分环境差异巨大，整体 SOTA <6.5/10 | 注意：聚合分掩盖单环境 0 分塌陷 |
| **WebArena** (812 任务, 5 站点) | 真实网站多步操作 | 早期 14% | Claude Mythos Preview **68.7%** | Planner + Executor + Memory 三层 |
| **Magentic-One/Bench** | 异构模态协作 | 单 agent baseline | Orchestrator + specialists **+3-4pp** | Hierarchical, ledger-based 任务台账 |

**关键洞察**：scaffold 比模型差异大——GAIA 上 framework 加分约 +30pp（44.8 → 74.6）。意味着**架构选对比换更强模型重要**。

---

## 3. 公开 Benchmark 的陷阱

⚠️ **Berkeley RDI 2026-04-12 实证**：8 个主流 benchmark 都能被 reward hacking 攻破。

⚠️ **OpenAI 已停报 SWE-bench**——因为前沿模型训练污染严重。

⚠️ **AgentBench 聚合分塌陷**：综合 70% 可能是"6 个环境 90% + 2 个环境 0%"，遇到长尾 task 直接挂。

**所以**：永远先建 **30-50 题私有 held-out 集**，再跑公开 bench。私有集才是真信号。

---

## 4. 30 行 Python 评估脚本（**可直接跑**）

`eval_agent.py` 已在本目录：

```python
# eval_agent.py — 4 维度评估：accuracy / token_cost / latency / robustness
import json, time, statistics
from pathlib import Path

def evaluate(agent_fn, dataset: list[dict], n_seeds: int = 3) -> dict:
    """agent_fn(task: str) -> {'answer': str, 'tokens_in': int, 'tokens_out': int}"""
    results = []
    for task in dataset:
        per_seed = []
        for seed in range(n_seeds):  # robustness = 跨 seed 一致性
            t0 = time.perf_counter()
            try:
                out = agent_fn(task["question"])
                ok = str(out["answer"]).strip().lower() == str(task["gold"]).strip().lower()
                per_seed.append({
                    "ok": ok,
                    "latency": time.perf_counter() - t0,
                    # Sonnet 4.6 价格示例：$3/M in, $15/M out
                    "cost": out["tokens_in"] * 3e-6 + out["tokens_out"] * 1.5e-5
                })
            except Exception as e:
                per_seed.append({
                    "ok": False,
                    "latency": time.perf_counter() - t0,
                    "cost": 0,
                    "err": str(e)
                })
        accs = [r["ok"] for r in per_seed]
        results.append({
            "task_id": task["id"],
            "pass@1": sum(accs) / len(accs),
            "consistent": len(set(accs)) == 1,
            "avg_latency": statistics.mean(r["latency"] for r in per_seed),
            "avg_cost_usd": statistics.mean(r["cost"] for r in per_seed)
        })
    return {
        "accuracy": statistics.mean(r["pass@1"] for r in results),
        "robustness": sum(r["consistent"] for r in results) / len(results),
        "p50_latency": statistics.median(r["avg_latency"] for r in results),
        "total_cost_usd": sum(r["avg_cost_usd"] for r in results),
        "n_tasks": len(results),
        "details": results
    }

if __name__ == "__main__":
    dataset = json.loads(Path("eval_set.jsonl").read_text())  # [{id, question, gold}]
    print(json.dumps(evaluate(
        lambda q: {"answer": "TODO", "tokens_in": 100, "tokens_out": 50},
        dataset
    ), indent=2))
```

---

## 5. 自己建 held-out 集（**实操**）

写一个 `eval_set.jsonl`，每行一个 JSON：

```jsonl
{"id":"q01","question":"What does MCP stand for?","gold":"Model Context Protocol"}
{"id":"q02","question":"Who created Ruflo?","gold":"Reuven Cohen"}
{"id":"q03","question":"What's the default port of claude-peers broker?","gold":"7899"}
```

**好的 held-out 集的标准**：

1. **小但密**：30-50 题足够发现差异，不需要几百题
2. **覆盖你的真实场景**：不要抄 GAIA / SWE-bench，要抄你产品**真实用户怎么用**
3. **gold 要确定性可判**：避免开放式问题，要么是 multiple choice，要么是字符串精确匹配
4. **私有不公开**：泄漏出去就废了
5. **每季度更新一次**：避免你的系统 overfit 到这 50 题

---

## 6. 评估你的 Multi-Agent 系统 — 完整流程

### 步骤

```
1. 建 held-out 集 (50 题)
2. 跑 single-agent baseline (Claude Sonnet 直接答)
3. 跑你的 swarm
4. 对比 4 维：accuracy / cost / latency / robustness
5. 算 ROI: (acc_swarm - acc_single) / (cost_swarm / cost_single)
```

### 决策矩阵

| Accuracy 提升 | Cost 涨幅 | 决策 |
|---|---|---|
| +20pp | <2x | ✅ 上 swarm |
| +10pp | 2-3x | ⚠️ 看具体场景 |
| +5pp | >3x | ❌ 单 agent 够了 |
| 持平或下降 | 任何 | ❌ swarm 错配场景 |

### 真实参考

- **Anthropic 自己**：Multi-agent research +90.2% accuracy，但 **15x token 消耗**
- 这意味着只有"信息密集 + 单次价值高"的任务（深度研究、合规审查）才值得

---

## 7. 真实使用场景

### 场景 ① 给 SC4062 image agent 做评估
- 建 50 题 held-out（每题：prompt + 期望的视觉风格描述）
- 跑 single agent vs hive-mind swarm
- 测：visual quality (人工评) / prompt cost / 生成时间

### 场景 ② Twitter pipeline 评估
- 50 个真实 user query（"帮我找 indie hacker 关于 SaaS 定价的讨论"）
- single agent vs swarm（爬 + 总结 + 互动）
- 测：召回率 / token cost / 用户满意度

### 场景 ③ CanMarket 4-Agent 评估
- 50 个真实 brand brief
- pipeline (4 agents) vs single agent
- 测：strategy 质量人工打分 / cost / 时间

### 场景 ④ 给 gstack workflow 评估
- 50 个真实 PR
- gstack /office-hours → /plan → /ship vs 直接让 Claude 写
- 测：merge 通过率 / dev 时间 / bug 率

---

## 8. 3 条实操建议（**对齐**给你）

```
┌─────────────────────────────────────────────────────────────┐
│ ① 先建 30-50 题私有 held-out 集，再跑公开 bench              │
│   公开 bench 数据污染 + reward hacking 严重                  │
├─────────────────────────────────────────────────────────────┤
│ ② 永远同时报 4 维（accuracy + cost + latency + robustness）  │
│   ≥3 个 seed。Multi-agent +5pp accuracy 但 cost×3 你不能不知 │
├─────────────────────────────────────────────────────────────┤
│ ③ AgentBench 类聚合分要看 per-env 拆解                       │
│   "70% 综合"可能是"6 个 90% + 2 个 0%"，长尾会挂              │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 关键 Takeaway

```
┌─────────────────────────────────────────────────────────────┐
│ ① 没有评估的 multi-agent 系统是迷信                          │
│   "感觉更好"不是结论，数字才是                               │
├─────────────────────────────────────────────────────────────┤
│ ② Scaffold > Model                                          │
│   架构选对比换更强模型重要（GAIA +30pp）                     │
├─────────────────────────────────────────────────────────────┤
│ ③ 4 维评估 + 私有 held-out 集 = 工程师该有的素养             │
│   这是 multi-agent 工程师 vs ppt 选手的分水岭                │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. 延伸阅读

- HAL GAIA Leaderboard: https://hal.cs.princeton.edu/gaia
- SWE-bench: https://www.swebench.com/
- AgentBench (THUDM): https://github.com/THUDM/AgentBench
- Berkeley RDI Trustworthy Benchmarks: https://rdi.berkeley.edu/blog/trustworthy-benchmarks-cont/
- 论文：Beyond Accuracy: Enterprise Agentic Eval Framework (arXiv:2511.14136)

---

## 课程结束 🎓

恭喜，你完成了 5 lab 的 a2a 学习路径：

```
Lab 1: MCP 协议       ── agent ↔ tool 怎么通信
Lab 2: A2A 协议对比    ── agent ↔ agent 4 大协议
Lab 3: Pipeline 拓扑   ── 5 命名 agent 真实流水线
Lab 4: Swarm + 记忆    ── Hive-Mind + HNSW 持久记忆
Lab 5: 评估           ← 你在这里
```

**下一步建议**：
- 看 `bonus/A2A_DEEP_DIVE.md` — 协议层最新研究
- 看 `bonus/PAPERS.md` — 8 篇必读论文
- 选一个真实项目（SC4062 / Twitter pipeline / CanMarket）跑一遍 5-lab 学到的东西
