# Bonus: A2A 协议生态深度调研

> 这是基于 web research 的最新行业 snapshot（2026-05），不是教学，是参考资料。  
> 数据来源于 Anthropic / Google / IBM 官方文档 + 50+ 公开案例。

---

## 1. 4 大协议核心矩阵

| Dim | **MCP** (Anthropic) | **A2A** (Google → Linux Foundation) | **ACP** ⚠️ archived | **ANP** (pre-spec) |
|---|---|---|---|---|
| **Problem** | Tool/data access for one LLM | Peer agent collab across vendors | Historical: agent runtime (folded into A2A) | Decentralized agent discovery + identity |
| **Transport** | JSON-RPC 2.0 over stdio / Streamable HTTP (Nov 2025 spec) | JSON-RPC 2.0 over HTTPS, REST `POST /message:send`, gRPC `SendMessage` | REST over HTTP, JSON envelope (legacy) | HTTP + W3C DID (`did:wba`), end-to-end encrypted (work in progress) |
| **Primitives** | `tools`, `resources`, `prompts` | `AgentCard`, `Task`, `Message`, `Artifact` | `Run`, `Message[].parts[]` (legacy) | DID doc + payment hooks (draft) |
| **Identity** | Local trust / OAuth on remote | Signed AgentCards (v0.3) | HTTP auth, no native identity | First-class — DID + signature per message |
| **Status / stars** | Spec ~8K stars | 23.6K stars, **50+ launch partners** (per Google's announcement) | Project archived, folded into A2A | W3C Community Group draft (no production) |

**Mental model**：
- **MCP = 垂直**（LLM ↔ tools）
- **A2A = 水平**（agent ↔ agent across orgs）
- **ACP = runtime**（long-running stateful agents）
- **ANP = identity layer underneath**

---

## 2. Payload 例子（精确到代码）

### MCP — Tool Call
```jsonc
{"jsonrpc":"2.0","id":1,"method":"tools/call",
 "params":{"name":"read_file","arguments":{"path":"/x"}}}
```

### A2A — Message Send
```jsonc
{"jsonrpc":"2.0","id":"req-001","method":"message/send",
 "params":{"message":{"role":"user",
   "parts":[{"kind":"text","text":"..."}],"messageId":"..."}}}
```

### ACP — POST /runs
```jsonc
{"agent_name":"echo","input":[{"role":"user",
  "parts":[{"content":"Howdy!","content_type":"text/plain"}]}]}
```

### ANP — DID-Signed Message
```jsonc
{"type":"AgentMessage",
 "from":"did:wba:0x1234...alice",
 "to":"did:wba:0x5678...bob",
 "intent":"request_collaboration",
 "payload":{"task":"..."},
 "signature":"0xabcdef..."}
```

---

## 3. 真实生产部署案例（**已 shipped**，2025-2026）

| # | 公司/产品 | 协议 | 做什么 |
|---|---|---|---|
| 1 | **Block (Square)** | MCP | 内部工程工具 — Anthropic 原始 launch design partner |
| 2 | **Cloudflare** | MCP | `github.com/cloudflare/mcp` — Workers, R2, D1, KV 全套；提供 remote MCP-on-Workers 托管 |
| 3 | **Sourcegraph Cody** | MCP | OpenCtx → MCP 迁移 Q1 2025 |
| 4 | **Replit Agent + Ghostwriter** | MCP | IDE 内 tooling（Anthropic launch list）|
| 5 | **Zed Editor** | MCP | Context servers (#29370, spec 2025-03-26) |
| 6 | **Anthropic claude.ai Research** | Internal | Opus 4 lead + Sonnet 4 subagents → **+90.2% accuracy / 15× tokens** |
| 7 | **Salesforce Agentforce + ServiceNow + SAP Joule + Workday** | A2A | Cross-vendor agent handoffs (Google A2A 公告里的 50+ launch partners) |
| 8 | **AWS Bedrock AgentCore + Azure AI Foundry + Google Agent Engine** | A2A | 三大 hyperscaler 都 ship 了 native A2A endpoints |
| 9 | **Cognition Devin 2.0** | **拒绝 multi-agent** | 显式选择 single-threaded writes，多个 Devin 实例并行用 REST API。**重要反对派证据** |

---

## 4. 10 篇必读（精选，不超过 10）

1. **MCP Spec 2025-11-25** — https://modelcontextprotocol.io/specification/2025-11-25  
   Streamable HTTP 取代 SSE，当前权威源
2. **A2A Spec** — https://github.com/a2aproject/A2A/blob/main/docs/specification.md  
   AgentCard + Task + JSON-RPC，Linux Foundation 治理
3. **Anthropic — How we built our multi-agent research system**  
   https://www.anthropic.com/engineering/multi-agent-research-system  
   **唯一一个 ship 了的 multi-agent 产品的顶级工程博客**
4. **Cognition — Don't Build Multi-Agents**  
   https://cognition.ai/blog/dont-build-multi-agents  
   **采用 A2A 之前必读** — 最强反对派论点
5. **AutoGen paper** — https://arxiv.org/abs/2308.08155  
   Conversation-as-protocol，57.8K stars (Microsoft)
6. **MetaGPT paper** — https://arxiv.org/abs/2308.00352  
   SOPs as prompts，HumanEval 85.9% Pass@1，67.8K stars
7. **ChatDev paper** — https://arxiv.org/abs/2307.07924  
   虚拟软件公司，瀑布流 agent，33K stars
8. **Voyager (NeurIPS 2023)** — https://arxiv.org/abs/2305.16291  
   Lifelong learning agent in Minecraft；canonical "skill library" 模式
9. **CAMEL paper** — https://arxiv.org/abs/2303.17760  
   Role-playing pairs，CrewAI 的灵感来源
10. **ANP White Paper** — https://arxiv.org/html/2508.00007v1  
    去中心化身份层；唯一认真对待跨组织信任的协议

**额外推荐**：Simon Willison 注解版 Anthropic 文章 — https://simonwillison.net/2025/Jun/14/multi-agent-research-system/（5 分钟版）

---

## 5. 选型结论（**Bottom Line**）

```
┌─────────────────────────────────────────────────────────────┐
│ ✅ MCP 赢了垂直层（LLM ↔ tool）— 默认用                     │
│                                                              │
│ ✅ A2A 正在赢水平层（50+ launch partners + 三大云原生支持）  │
│   跨组织协作时采用                                           │
│                                                              │
│ ⚠️  ACP 已 archived — 历史项目，新系统不要选                 │
│                                                              │
│ 🔮 ANP 是 pre-spec 的去中心化协议 — 长期关注但短期不能用     │
│                                                              │
│ 🚨 用任何 A2A 之前先读 Cognition 反对派 —                    │
│    "Don't Build Multi-Agents" 是 2025-2026 最严密的反方论证   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. 给 Haoyang 的具体建议

基于你的 stack（gstack + claude-peers + OpenClaw + CanMarket）：

| 你的项目 | 该用什么协议 | 为什么 |
|---|---|---|
| Claude Code workflow | MCP（已用）+ Agent + SendMessage（内部）| 单 dev workflow 不需要 A2A |
| CanMarket 4-Agent | A2A（如果未来要给客户开放）| 跨组织时切换；现在 OpenClaw 内部够用 |
| OpenClaw Telegram bots | OpenClaw 原生 a2a | 别加 A2A 一层徒增复杂 |
| 跨 Mac (Server + Portable) | claude-peers + Tailscale | 已有，无需替换 |
| SC4062 image agent | Pipeline（Lab 3 模式）| 单任务多步，不需要协议层 |

**总结**：你目前**不需要**马上上 A2A。MCP 够用。等以后开放生态时再考虑。

---

来源：
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [A2A Specification](https://github.com/a2aproject/A2A/blob/main/docs/specification.md)
- [IBM ACP Repo](https://github.com/i-am-bee/acp)
- [ANP](https://agent-network-protocol.com/)
- [Anthropic Multi-Agent Research](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Cognition: Don't Build Multi-Agents](https://cognition.ai/blog/dont-build-multi-agents)
- [Google A2A Announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- [AWS Bedrock A2A Contract](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-a2a-protocol-contract.html)
