# Lab 1 — 看穿 MCP 协议

> **学完你会**：自己写一个最小 MCP server，看清 Claude Code 跟工具之间到底在塞什么字符串。

---

## 1. 为什么要从 MCP 开始？

MCP（Model Context Protocol，Anthropic 2024-11 发布）是当前 agent-to-agent 协作最广泛部署的协议。Claude Code、Cursor、Continue.dev、VS Code Copilot 都支持。

**痛点**：很多教程把 MCP 讲得像黑魔法。其实它本质就是 **JSON-RPC 2.0 over stdio**。

50 行 Python 就能写一个完整的 MCP server。本课结束你就能看到。

---

## 2. 协议本质（**这一节最重要**）

```
MCP 消息格式 = JSON-RPC 2.0
MCP transport 选项：
  ① stdio (本地 child process)        ← 本课重点
  ② Streamable HTTP (远程 server)     ← 2025-11-25 spec 正式版
```

**完整 MCP spec**: https://modelcontextprotocol.io/specification/2025-03-26  
（实际表面比这里展示的多，但本课聚焦最常用的 stdio + tools 路径）

**最常见的协议方法**（学完这些足够你写 80% 的 MCP server）：

| 方向 | Method | 作用 |
|---|---|---|
| 客户端→服务端 | `initialize` | 握手，交换版本和能力 |
| 客户端→服务端 (notification) | `notifications/initialized` | 客户端确认初始化完成（**lifecycle 必需**）|
| 客户端→服务端 | `tools/list` | 列出可用工具 |
| 客户端→服务端 | `tools/call` | 调用某个工具 |
| 服务端→客户端 | `notifications/*` | 主动推送（无需响应）|

> ⚠️ 注：完整 MCP 还有 `resources/*`、`prompts/*`、`logging/*` 等子树。本课只覆盖 `tools` 路径。学完想深入再看官方 spec。

**stdio transport 3 条铁律**：

1. **stdout 只能输出协议消息**（每行一条 JSON）
2. **stderr 留给日志**——`print()` 进 stdout 不是合法 JSON 整个 server 直接挂
3. **每条消息一行**（newline-delimited JSON）

---

## 3. claude-peers — 你机器上跑着的真实 a2a 例子

`claude-peers-mcp` 已经装在 `~/claude-peers-mcp/`，是一个让多个 Claude Code 实例互相通信的 MCP server。

### 三层架构

```
┌──────────────────────────────────────────────────────────────┐
│ Claude Code 进程 A          Claude Code 进程 B               │
│        ↓ stdio                    ↓ stdio                    │
│  ┌──────────────────┐        ┌──────────────────┐            │
│  │ server.ts (MCP)  │        │ server.ts (MCP)  │            │
│  │  per-instance    │        │  per-instance    │            │
│  └────────┬─────────┘        └────────┬─────────┘            │
│           │ HTTP (POST)               │ HTTP (POST)          │
│           └──────────────┬────────────┘                      │
│                          ↓                                   │
│              ┌───────────────────────┐                       │
│              │ broker.ts (singleton) │                       │
│              │ localhost:7899        │                       │
│              │ + SQLite              │                       │
│              └───────────────────────┘                       │
└──────────────────────────────────────────────────────────────┘
```

**为什么要 broker？** MCP server 是 **per-instance**——每个 Claude 进程一个，进程之间天然隔离。要协调多 Claude 实例就得有共享 daemon。

`server.ts:68-93` 看 `ensureBroker()`：第一个启动的 Claude 实例顺手把 broker 拉起来 detach 掉，后续实例发现已经在跑就直接连。**这是个非常实用的设计模式**——任何 multi-agent 系统都可以借鉴。

---

## 4. 真实调用 trace — 当你按 `list_peers`

**Step 1**：Claude Code（客户端）写到 stdin
```json
{"jsonrpc":"2.0","id":42,"method":"tools/call",
 "params":{"name":"list_peers","arguments":{"scope":"machine"}}}
```

**Step 2**：`server.ts:239` 的 `CallToolRequestSchema` handler 接到，进 `case "list_peers"` (line 243)

**Step 3**：调 `brokerFetch("/list-peers", ...)`——内部就是 HTTP POST 到 localhost:7899

**Step 4**：broker 查 SQLite，返回 peers 列表

**Step 5**：server.ts:264-275 把 peers 格式化成人类可读 text，stdout 写：
```json
{"jsonrpc":"2.0","id":42,
 "result":{"content":[{"type":"text","text":"Found 2 peer(s)..."}]}}
```

---

## 5. 关键创新点 — Channel Push（**这个最值得学**）

普通 MCP 是**纯请求-响应**——客户端不问，服务端不说话。

但 claude-peers 想让 Claude 实例之间**真正实时通信**——A 发消息给 B，B 应该立刻收到，不是等 B 下次主动 poll。

**`server.ts:431-442` 的精髓**：

```typescript
await mcp.notification({
  method: "notifications/claude/channel",     // 自定义 notification 类型
  params: {
    content: msg.text,                        // 消息正文
    meta: {
      from_id: msg.from_id,
      from_summary: fromSummary,              // 发送方在干什么
      from_cwd: fromCwd,                      // 发送方在哪个目录
      sent_at: msg.sent_at,
    },
  },
});
```

配合 `server.ts:148-149` 的 capability 声明：

```typescript
capabilities: {
  experimental: { "claude/channel": {} },     // 声明我会用 channel 推送
  tools: {},
}
```

### 这是怎么做到的？

1. broker 那边收到消息后存进 SQLite
2. server.ts 每秒 poll 一次（`pollAndPushMessages`，line 405-450）
3. 一旦发现新消息，立刻发 `notifications/claude/channel`
4. Claude Code 客户端把这个 notification 当成"用户消息"插进对话流

### 对你的启发

**轮询 + push notification 是最简单可行的实时 a2a 模式**。

不需要 WebSocket、不需要服务总线，1 秒轮询足够 agent 协作场景。

---

## 6. 动手实验 — 跑通 50 行 Python MCP server

`toy_mcp_server.py` 已经在本目录。直接跑：

```bash
cd ~/Desktop/agent-lessons/labs/lab1

printf '%s\n%s\n%s\n%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"echo","arguments":{"text":"你好 a2a 世界"}}}' \
  | python3 toy_mcp_server.py
```

> 注意第 2 条消息：`notifications/initialized` 是 lifecycle **必需**的——客户端 initialize 之后必须发这条 notification 告诉 server 准备好了。

### 真实输出

```json
[toy-mcp] starting
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-03-26",
 "capabilities": {"tools": {}}, "serverInfo": {"name": "toy-mcp", "version": "0.1.0"}}}
{"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "echo",
 "description": "把输入原样返回（教学用最小工具）",
 "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}},
 "required": ["text"]}}]}}
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text",
 "text": "echo: 你好 a2a 世界"}]}}
```

---

## 7. 真实使用场景

学完 MCP 你能做这些事：

### 场景 ① 给 Claude Code 接私有数据源
- 写一个 MCP server 暴露你的 Notion / Linear / 内部 API
- Claude Code 自动发现并能查询
- 例子：`mcp__github__*` 那些工具就是 GitHub 写的 MCP server

### 场景 ② 跨进程 agent 协作
- claude-peers 模式：让多个 Claude / Cursor / Codex 实例互发消息
- 用 broker daemon 做 fan-out
- 案例：你已经在跑这个

### 场景 ③ 给非 Claude 模型提供工具
- MCP 是协议无关的——任何 client 实现协议都能用
- OpenAI Codex CLI、Continue.dev、VS Code Copilot Chat 都接 MCP
- 写一次 server，所有 client 受益

### 场景 ④ 把外部 service 包成"工具"
- 你的 Telegram bot、Twitter scraper、Reddit poster 都可以包成 MCP
- 然后 Claude Code 直接调用，不用每次粘贴 API 文档

---

## 8. 关键 Takeaway（对齐 3 条）

```
┌─────────────────────────────────────────────────────────────┐
│ ① MCP 消息格式是 JSON-RPC 2.0                               │
│   → transport 可以是 stdio（本地 child process）            │
│     或 Streamable HTTP（远程 server）                       │
├─────────────────────────────────────────────────────────────┤
│ ② 真正的 a2a 实时通信靠 notifications/*                     │
│   → 服务端"主动推"是非标准但极强大的扩展                    │
├─────────────────────────────────────────────────────────────┤
│ ③ 多实例协调 = per-instance MCP + 共享 daemon (broker)      │
│   → 这个模式适用于任何 multi-agent 场景                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. 延伸阅读

- MCP 官方文档: https://modelcontextprotocol.io/
- MCP 官方 spec: https://spec.modelcontextprotocol.io/
- Anthropic MCP 公告: https://www.anthropic.com/news/model-context-protocol
- Awesome MCP servers: https://github.com/punkpeye/awesome-mcp-servers

下一节 → **Lab 2: A2A 协议对比** 看 Google A2A、ANP、ACP 怎么挑战 MCP。
