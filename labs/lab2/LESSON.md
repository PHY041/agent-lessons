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

| 维度 | **MCP** | **Google A2A** | **IBM ACP** ⚠️ | **ANP** |
|---|---|---|---|---|
| 发布方 | Anthropic | Google → Linux Foundation | BeeAI/IBM (已 archived，并入 A2A)| W3C Community Group draft |
| 解决问题 | agent ↔ tool | agent ↔ agent | 历史方案，已被 A2A 取代 | 去中心化 agent 网络 + 身份 |
| Transport | stdio / Streamable HTTP | JSON-RPC over HTTPS / gRPC / REST | REST + JSON envelope | HTTP + W3C DID |
| 消息格式 | JSON-RPC 2.0 | JSON-RPC 2.0 (`message/send`) | Custom JSON (FIPA-inspired) | DID-signed JSON |
| 身份系统 | 无（信任 client） | Signed AgentCards (v0.3) | HTTP auth | DID (first-class) |
| 流式输出 | ✅ via SSE / Streamable HTTP | ✅ via SSE | ✅ via SSE | ✅ |
| 主要用户 | Claude Code, Cursor 等 100+ 客户端 | Google Cloud, Salesforce, AWS Bedrock 等（50+ launch partners）| BeeAI runtime 内部 | pre-spec |
| GitHub | 已有数百 servers | A2A SDK 23.6K stars | i-am-bee/acp（archived 路径）| ANP-Agent-Network |

> ⚠️ **ACP status update (2026-05)**: ACP 已经折叠并入 A2A 项目，作为 historical contribution。如果你今天想用，**默认选 A2A**，ACP 的 performative 概念可作设计参考。

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

每个 A2A agent 都暴露 `/.well-known/agent-card.json`（**注意当前 spec 用 `agent-card.json` 不是 `agent.json`**）：

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

### ACP — IBM 的早期方案（已 archived，并入 A2A）

ACP 借鉴了 1990s FIPA 标准（performative 概念），用于早期 agent 之间的 RESTful 通信。**当前已被 A2A 取代**——历史 schema 大致这样：

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

**关注点**：FIPA-style performatives（`request` / `inform` / `agree` / `refuse` / `confirm` 等）作为消息分类是好主意，A2A 在此之上做了简化。新项目直接用 A2A 即可。

### ANP — emerging 去中心化协议（pre-spec）

ANP（Agent Network Protocol）目前是 W3C Community Group 的 draft 阶段。强调**去中心化身份**（DID, decentralized identifier）——agent 靠加密签名互相认证，不需要中心化注册中心。

参考 schema（**实现细节仍在演进**）：

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

**当前状态**：未 production-ready，只用于研究。如果你长期看好"跨组织 agent 网络"，关注它的 spec 进展，但短期项目不要赌。

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

### 场景 ② Google A2A — 50+ launch partners
- Google 发布 A2A 时公布了 **50+ technology partners**（Salesforce / SAP / Workday / ServiceNow / Box 等）
- 公开公告: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
- 注：媒体二手报道经常把这个数字放大，**官方声明是"more than 50 technology partners"**

### 场景 ③ A2A — 三大云 hyperscaler 原生支持
- AWS Bedrock AgentCore + Azure AI Foundry + Google Agent Engine 都 ship 了 native A2A endpoints
- 跨厂商 agent 互通是 A2A 的杀手级用例

### 场景 ④ ACP（历史）— IBM watsonx Orchestrate
- 早期企业 agent 协作（HR / 财务 / 客服），现在新 deployment 走 A2A
- 老项目 audit trail 可作参考

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
