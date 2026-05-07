#!/usr/bin/env python3
"""
30 行 multi-agent 评估脚本 — 4 维度
跑法：
    1. 准备 eval_set.jsonl，每行 {"id":"...", "question":"...", "gold":"..."}
    2. 替换 agent_fn 为你真实的 agent 调用
    3. python3 eval_agent.py
"""
import json
import time
import statistics
from pathlib import Path


def evaluate(agent_fn, dataset: list[dict], n_seeds: int = 3) -> dict:
    """
    agent_fn(task: str) -> {'answer': str, 'tokens_in': int, 'tokens_out': int}
    """
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
                    # Sonnet 4.6 价格示例：$3/M in, $15/M out
                    "cost": out["tokens_in"] * 3e-6 + out["tokens_out"] * 1.5e-5,
                })
            except Exception as e:
                per_seed.append({
                    "ok": False,
                    "latency": time.perf_counter() - t0,
                    "cost": 0,
                    "err": str(e),
                })
        accs = [r["ok"] for r in per_seed]
        results.append({
            "task_id": task["id"],
            "pass@1": sum(accs) / len(accs),
            "consistent": len(set(accs)) == 1,
            "avg_latency": statistics.mean(r["latency"] for r in per_seed),
            "avg_cost_usd": statistics.mean(r["cost"] for r in per_seed),
        })
    return {
        "accuracy": statistics.mean(r["pass@1"] for r in results),
        "robustness": sum(r["consistent"] for r in results) / len(results),
        "p50_latency": statistics.median(r["avg_latency"] for r in results),
        "total_cost_usd": sum(r["avg_cost_usd"] for r in results),
        "n_tasks": len(results),
        "details": results,
    }


if __name__ == "__main__":
    eval_path = Path(__file__).parent / "eval_set.jsonl"
    if not eval_path.exists():
        # 教学样例
        print("⚠️  eval_set.jsonl 不存在，用样例数据。\n")
        dataset = [
            {"id": "q01", "question": "What does MCP stand for?", "gold": "Model Context Protocol"},
            {"id": "q02", "question": "Who created Ruflo?", "gold": "Reuven Cohen"},
        ]
    else:
        dataset = [json.loads(line) for line in eval_path.read_text().splitlines() if line.strip()]

    # Mock agent — 替换为你真实的实现
    def mock_agent(question: str):
        return {
            "answer": "Model Context Protocol" if "MCP" in question else "TODO",
            "tokens_in": 100,
            "tokens_out": 50,
        }

    report = evaluate(mock_agent, dataset, n_seeds=3)

    print("=" * 60)
    print(f"4 维评估报告 ({report['n_tasks']} tasks)")
    print("=" * 60)
    print(f"  Accuracy:      {report['accuracy']:.2%}")
    print(f"  Robustness:    {report['robustness']:.2%}  (跨 seed 一致)")
    print(f"  P50 Latency:   {report['p50_latency']:.3f}s")
    print(f"  Total Cost:    ${report['total_cost_usd']:.4f}")
    print()
    print(json.dumps(report["details"], indent=2))
