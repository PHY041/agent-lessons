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


def evaluate(agent_fn, dataset: list[dict], n_runs: int = 3) -> dict:
    """
    agent_fn(task: str) -> {'answer': str, 'tokens_in': int, 'tokens_out': int}

    n_runs: 同一任务重复执行的次数。
            对于 deterministic agent: n_runs=1 即可（多次不会变）。
            对于 stochastic agent (temperature>0): n_runs>=3 评估 repeatability。

    REPEATABILITY 注意：本脚本 *不主动注入 seed*——你的 agent_fn 内部需要
    自己处理随机性（设置 temperature、seed 参数等），如果它本身就是 deterministic
    那 n_runs=1。如果你想严格测试 robustness（对扰动输入的稳健性），需要在 dataset
    层面预先生成 paraphrase 变体，而不是依赖本脚本。
    """
    results = []
    for task in dataset:
        per_run = []
        for _ in range(n_runs):
            t0 = time.perf_counter()
            try:
                out = agent_fn(task["question"])
                ok = str(out["answer"]).strip().lower() == str(task["gold"]).strip().lower()
                per_run.append({
                    "ok": ok,
                    "latency": time.perf_counter() - t0,
                    # Sonnet 4.6 价格示例：$3/M in, $15/M out
                    "cost": out["tokens_in"] * 3e-6 + out["tokens_out"] * 1.5e-5,
                })
            except Exception as e:
                per_run.append({
                    "ok": False,
                    "latency": time.perf_counter() - t0,
                    "cost": 0.0,  # failure 没产生 cost
                    "err": str(e),
                })
        accs = [r["ok"] for r in per_run]
        results.append({
            "task_id": task["id"],
            "success_rate": sum(accs) / len(accs),  # 不是 pass@1，是 n_runs 内的均值
            "repeatable": len(set(accs)) == 1,
            "avg_latency": statistics.mean(r["latency"] for r in per_run),
            "task_total_cost_usd": sum(r["cost"] for r in per_run),  # 整 task 跑了 n_runs 次的总花费
            "errors": [r.get("err") for r in per_run if "err" in r],
        })
    return {
        "accuracy": statistics.mean(r["success_rate"] for r in results),
        "repeatability": sum(r["repeatable"] for r in results) / len(results),
        "p50_latency": statistics.median(r["avg_latency"] for r in results),
        "eval_total_cost_usd": sum(r["task_total_cost_usd"] for r in results),  # 整 eval run 真实花费
        "n_tasks": len(results),
        "n_runs_per_task": n_runs,
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

    report = evaluate(mock_agent, dataset, n_runs=3)

    print("=" * 60)
    print(f"4 维评估报告 ({report['n_tasks']} tasks × {report['n_runs_per_task']} runs)")
    print("=" * 60)
    print(f"  Accuracy:        {report['accuracy']:.2%}")
    print(f"  Repeatability:   {report['repeatability']:.2%}  (n_runs 内全一致)")
    print(f"  P50 Latency:     {report['p50_latency']:.3f}s")
    print(f"  Eval Total Cost: ${report['eval_total_cost_usd']:.4f}")
    print()
    print(json.dumps(report["details"], indent=2))
