#!/bin/bash
# 合并所有 markdown 成一份完整教程
set -e
cd "$(dirname "$0")/.."

OUT="build/tutorial.md"

cat > "$OUT" <<'EOF'
---
title: "Agent-to-Agent 学习教程"
subtitle: "5 Labs · 真代码 · 真使用场景"
author: "Haoyang Pang"
date: "2026-05-08"
---

\newpage

# 教程导读

这是一份关于 agent-to-agent 协作的实操教程，涵盖：

- **MCP 协议** — Anthropic 的 agent ↔ tool 标准
- **A2A / ACP / ANP** — Google / IBM / W3C 的 agent ↔ agent 协议
- **拓扑模式** — Pipeline / Fan-out / Hive-Mind
- **共享记忆** — HNSW vector memory
- **科学评估** — 4 维度（accuracy / cost / latency / robustness）

每节 lab 都包含：

1. 协议/概念解析
2. 真实代码示例
3. 真实使用场景
4. 反模式警告
5. Takeaway 三条

\newpage

EOF

echo "## 目录" >> "$OUT"
echo "" >> "$OUT"
echo "1. Lab 1 — 看穿 MCP 协议" >> "$OUT"
echo "2. Lab 2 — A2A 协议对比" >> "$OUT"
echo "3. Lab 3 — Pipeline 拓扑实战" >> "$OUT"
echo "4. Lab 4 — Swarm + HNSW 记忆" >> "$OUT"
echo "5. Lab 5 — 评估" >> "$OUT"
echo "6. Bonus — A2A 协议生态深度调研" >> "$OUT"
echo "7. Bonus — Multi-Agent Benchmarks 调研" >> "$OUT"
echo "" >> "$OUT"
echo '\newpage' >> "$OUT"
echo "" >> "$OUT"

for lab in lab1 lab2 lab3 lab4 lab5; do
  echo "" >> "$OUT"
  cat "labs/$lab/LESSON.md" >> "$OUT"
  echo "" >> "$OUT"
  echo '\newpage' >> "$OUT"
  echo "" >> "$OUT"
done

cat bonus/A2A_DEEP_DIVE.md >> "$OUT"
echo "" >> "$OUT"
echo '\newpage' >> "$OUT"
echo "" >> "$OUT"
cat bonus/BENCHMARKS.md >> "$OUT"

wc -l "$OUT"
echo "✅ Combined → $OUT"
