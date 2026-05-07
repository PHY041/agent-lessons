# Lab 2 — A2A 协议对比

> **学完你会**：知道 MCP / Google A2A / IBM ACP / ANP 4 大协议各管什么、payload 长啥样、什么时候用哪个。不再听营销 hype。

---

## 1. 为什么有 4 个协议？

2024-2025 年 a2a 协议出现了"小型混战"：

| 时间 | 事件 |
|---|---|
| 2024-11 | **Anthropic MCP** 发布 — agent ↔ tool |
| 2025-04 | **Google A2A** (Agent2Agent) 发布 — agent ↔ agent |
| 2025-05 | **IBM ACP** (Agent Communication Protocol) 进 Linux Foundation |
| 2025 | **ANP** (Agent Network Protocol) 中国开源社区 |

**底层逻辑**：MCP 解决"agent 怎么用工具"；A2A 解决"agent 怎么找到别的 agent 并合作"。**两者不冲突，是不同层**。

---

## 2. 一张图看清分工

```
┌────────────────────────────────────────────────────────────┐
│                                                             │
│   Agent Network Layer (谁能找到谁)                           │
│   ┌─────────────────────────────────────┐                  │
│   │  Google A2A  /  IBM ACP  /  ANP     │                  │
│   │  (agent ↔ agent discovery + comm)   │                  │
│   └─────────────────────────────────────┘                  │
│                  ↓ 单个 agent 内部                           │
│   ┌─────────────────────────────────────┐                  │
│   │  MCP                                │                  │
│   │  (agent ↔ tool/resource)            │                  │
│   └─────────────────────────────────────┘                  │
│                  ↓                                          │
│   底层 LLM (Claude / GPT / Gemini / Qwen)                   │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

**说人话**：
- 一个 agent 内部用 MCP 接工具
- 多个 agent 之间用 A2A/ACP/ANP 协作
- 单 agent 用 MCP，多 agent 系统两个都用

---

## 3. 协议对比表

| 维度 | **MCP** | **Google A2A** | **IBM ACP** | **ANP** |
|---|---|---|---|---|
| 发布方 | Anthropic | Google | IBM (Linux Foundation) | 中国开源社区 |
| 解决问题 | agent ↔ tool | agent ↔ agent | agent ↔ agent (企业级) | 跨组织 agent 网络 |
| Transport | stdio / HTTP+SSE | HTTP+JSON / gRPC | HTTP+JSON | HTTP+JSON / WebSocket |
| 消息格式 | JSON-RPC 2.0 | Custom JSON | Custom JSON (FIPA-inspired) | DID-based JSON |
| 身份系统 | 无（信任 client） | OIDC / OAuth | 企业 identity | DID (去中心化身份) |
| 流式输出 | ✅ via SSE | ✅ via SSE | ✅ via SSE | ✅ |
| 主要用户 | Claude Code, Cursor 等 100+ 客户端 | Google Cloud, Salesforce, Box | IBM watsonx 客户 | 国内项目较多 |
| GitHub | 已有数百 servers | A2A SDK + 50+ adopters | Apache 2.0 仓库 | ANP-Agent-Network |

---

## 4. 真实 payload 对比（**精确到代码层面**）

### MCP — 调用一个工具

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "tools/call",
  "params": {
    "name": "search_database",
    "arguments": {"query": "active users last 7 days"}
  }
}
```

### Google A2A — 给另一个 agent 发任务

```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "method": "message/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{
        "kind": "text",
        "text": "Generate a marketing plan for our Q3 launch"
      }],
      "messageId": "msg-456"
    }
  }
}
```

返回（流式）：

```json
{
  "jsonrpc": "2.0",
  "id": "task-123",
  "result": {
    "id": "task-123",
    "status": {"state": "working"},
    "history": [
      {"role": "agent", "parts": [{"kind": "text", "text": "Analyzing..."}]}
    ],
    "artifacts": [
      {"artifactId": "plan-001", "parts": [{"kind": "text", "text": "..."}]}
    ]
  }
}
```

### A2A 关键 — Agent Card（自我介绍）

每个 A2A agent 都暴露 `/.well-known/agent.json`：

```json
{
  "name": "MarketingPlanner",
  "description": "Generates Q3 marketing plans",
  "version": "1.0.0",
  "url": "https://marketing-agent.example.com/a2a/v1",
  "capabilities": {"streaming": true, "pushNotifications": true},
  "skills": [{
    "id": "generate-plan",
    "name": "Generate Marketing Plan",
    "tags": ["marketing", "strategy"]
  }],
  "defaultInputModes": ["text"],
  "defaultOutputModes": ["text", "file"]
}
```

**这是 A2A 最大的创新**——agents 通过 well-known URL 发现彼此能力，不需要预先配置。

### ACP — IBM 的方案（FIPA-inspired performatives）

```json
{
  "performative": "request",
  "sender": "agent-alice",
  "receiver": "agent-bob",
  "content": {
    "action": "schedule_meeting",
    "params": {"date": "2026-05-10", "duration_min": 30}
  },
  "conversation_id": "conv-789",
  "reply_with": "msg-001"
}
```

ACP 显著借鉴了 1990s FIPA 标准（performative 概念）——`request` / `inform` / `agree` / `refuse` / `confirm` 等。**学术派**。

### ANP — DID-based 去中心化身份

```json
{
  "type": "AgentMessage",
  "from": "did:agent:0x1234...alice",
  "to": "did:agent:0x5678...bob",
  "messageId": "msg-uuid-001",
  "intent": "request_collaboration",
  "payload": {"task": "..."},
  "signature": "0xabcdef..."
}
```

ANP 强调**去中心化身份**（DID, decentralized identifier）——agent 不需要中心化注册中心，靠加密签名互相认证。**Web3 派**。

---

## 5. 选型决策树

```
你的场景是什么？
├─ 单 agent 接工具/数据源
│  └─→ MCP（生态最大，Claude Code/Cursor 都支持）
│
├─ 多 agent 协作（同一组织内）
│  └─→ Google A2A（Agent Card 发现机制最优雅）
│
├─ 多 agent 协作（企业，要 audit trail）
│  └─→ IBM ACP（FIPA-style，performative 明确）
│
├─ 跨组织 agent 网络（要去中心化）
│  └─→ ANP（DID 身份，无中心 registry）
│
└─ 不确定 / 试水
   └─→ MCP + 自定义 IPC（claude-peers 模式）
```

---

## 6. 真实使用场景（**已经 shipped 的，不是 future possibilities**）

### 场景 ① MCP — Claude Code + GitHub MCP
- 你已经在用 `mcp__github__create_pull_request` 等 25+ 工具
- 一行配置接通 GitHub，不用每次粘贴 API 文档

### 场景 ② Google A2A — Salesforce Agentforce
- Salesforce 用 A2A 让 Agentforce agents 之间互相调用
- 例如 LeadGen agent → Pricing agent → ContractDraft agent
- 公开 demo: https://www.salesforce.com/agentforce/

### 场景 ③ A2A — Box / Adobe / Box AI
- Box 集成 A2A 让 storage agent 跟 LLM agent 通信
- 公开案例: Google A2A blog 列了 50+ 早期 adopter

### 场景 ④ ACP — IBM watsonx Orchestrate
- 企业流程自动化，HR / 财务 / 客服 agent 协作
- 走 ACP 协议，每条消息有 audit log

### 场景 ⑤ ANP — 国内 agent 互联实验
- ANP-Agent-Network 仓库有几十个 agent 互联 demo
- 做跨域 agent 调用，DID 身份

---

## 7. 动手 — 写一个最小 A2A agent

`a2a_agent.py` 已在本目录。要点：

```python
# 暴露 Agent Card 在 /.well-known/agent.json
@app.get("/.well-known/agent.json")
def agent_card():
    return {
        "name": "EchoAgent",
        "description": "Echoes back what you send",
        "url": "http://localhost:8001/a2a/v1",
        "skills": [{"id": "echo", "name": "Echo"}]
    }

# 接 message/send
@app.post("/a2a/v1")
def handle(req: dict):
    if req["method"] == "message/send":
        text = req["params"]["message"]["parts"][0]["text"]
        return {
            "jsonrpc": "2.0",
            "id": req["id"],
            "result": {
                "id": str(uuid.uuid4()),
                "status": {"state": "completed"},
                "artifacts": [{
                    "artifactId": str(uuid.uuid4()),
                    "parts": [{"kind": "text", "text": f"echo: {text}"}]
                }]
            }
        }
```

跑：

```bash
pip install fastapi uvicorn
python3 a2a_agent.py &
curl http://localhost:8001/.well-known/agent.json
curl -X POST http://localhost:8001/a2a/v1 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"t1","method":"message/send",
       "params":{"message":{"role":"user",
       "parts":[{"kind":"text","text":"hi"}]}}}'
```

---

## 8. 关键 Takeaway

```
┌─────────────────────────────────────────────────────────────┐
│ ① MCP 跟 A2A 不打架，是不同层                                │
│   MCP: agent → tool                                          │
│   A2A: agent → agent                                         │
├─────────────────────────────────────────────────────────────┤
│ ② Agent Card (/.well-known/agent.json) 是 A2A 最大创新       │
│   像 robots.txt 一样标准化的"能力发现"机制                   │
├─────────────────────────────────────────────────────────────┤
│ ③ 选型按"信任边界"决定                                       │
│   组织内：MCP + A2A 够用                                     │
│   跨组织：ACP（企业级）/ ANP（去中心化）                     │
└─────────────────────────────────────────────────────────────┘
```

下一节 → **Lab 3: Pipeline 拓扑实战** 用 Claude Code Agent tool 起 5 个命名 agent 真实跑流水线。
