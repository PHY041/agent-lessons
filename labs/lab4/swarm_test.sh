#!/bin/bash
# Lab 4 — Swarm 实测脚本
#
# 前置条件：
#   - ~/Desktop/ruflo-spike 存在且已 init
#   - 有 Anthropic API key（已配在 ~/.claude.json 通常足够）
#   - 装了 bun 或 node 18+

set -e

SPIKE_DIR=~/Desktop/ruflo-spike

if [ ! -d "$SPIKE_DIR" ]; then
  echo "❌ $SPIKE_DIR 不存在。先跑 Lab 1 创建。"
  exit 1
fi

cd "$SPIKE_DIR"

echo "=== 1. 升级到 --full（如果还没升）==="
if [ ! -d ".claude-flow/data/hnsw" ]; then
  echo "升级中..."
  npx -y ruflo@latest init --full --no-global --force
else
  echo "已经是 full 配置"
fi

echo
echo "=== 2. 启动 daemon ==="
npx -y ruflo@latest daemon status || npx -y ruflo@latest daemon start &
sleep 3

echo
echo "=== 3. 初始化 hive-mind swarm ==="
npx -y ruflo@latest swarm init --topology hive-mind --max-agents 5

echo
echo "=== 4. 跑一个真实任务 ==="
echo "Goal: Find 3 brand-memory startups and summarize their tech stack"
npx -y ruflo@latest task create \
  --goal "Find 3 brand-memory or style-genome startups (not the obvious ones like Brandwatch / Sprout). For each, list: founders, tech stack, funding, differentiator."

echo
echo "=== 5. 等结果（约 60-120s）==="
sleep 60
npx -y ruflo@latest status

echo
echo "=== 6. 看输出 ==="
ls -la .claude-flow/data/results/ 2>/dev/null || echo "results 目录还没出来"
ls -la .claude-flow/logs/ 2>/dev/null | head -20

echo
echo "=== 7. 看共享 memory ==="
npx -y ruflo@latest memory list --top-k 5

echo
echo "完成。要清理：npx ruflo daemon stop"
