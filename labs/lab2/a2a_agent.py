#!/usr/bin/env python3
"""
最小 A2A agent — 教学用
实现 Google A2A 协议的核心：Agent Card + message/send

跑法：
    pip install fastapi uvicorn
    python3 a2a_agent.py

    # 另一个终端 — 当前 spec 路径：
    curl http://localhost:8001/.well-known/agent-card.json
    curl -X POST http://localhost:8001/a2a/v1 \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc":"2.0","id":"t1","method":"message/send",
           "params":{"message":{"role":"user",
           "parts":[{"kind":"text","text":"hello a2a"}]}}}'

    # REST 风格（A2A v0.3 也支持）：
    curl -X POST http://localhost:8001/message:send \\
      -H "Content-Type: application/json" \\
      -d '{"jsonrpc":"2.0","id":"t1","method":"message/send",
           "params":{"message":{"role":"user",
           "parts":[{"kind":"text","text":"hello a2a"}]}}}'
"""
import uuid
from datetime import datetime, timezone

try:
    from fastapi import FastAPI
    import uvicorn
except ImportError:
    print("Need: pip install fastapi uvicorn")
    raise SystemExit(1)


app = FastAPI(title="EchoAgent A2A demo")


def _agent_card_payload():
    return {
        "name": "EchoAgent",
        "description": "教学用 — 把你的话原样回给你",
        "version": "1.0.0",
        "url": "http://localhost:8001/a2a/v1",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "skills": [{
            "id": "echo",
            "name": "Echo",
            "description": "Echoes input text back",
            "tags": ["demo", "echo"],
        }],
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
    }


@app.get("/.well-known/agent-card.json")
def agent_card():
    """A2A 协议的核心：发现机制。
    Current spec (2025-11): 文件名是 agent-card.json
    任何 A2A client 通过这个 URL 找到 agent 的能力。
    """
    return _agent_card_payload()


@app.get("/.well-known/agent.json")
def agent_card_legacy():
    """向后兼容的旧 spec 路径。"""
    return _agent_card_payload()


def _err(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


@app.post("/a2a/v1")
def handle(req: dict):
    """A2A JSON-RPC endpoint (method: message/send)."""
    method = req.get("method")
    msg_id = req.get("id")

    if method != "message/send":
        return _err(msg_id, -32601, f"method not found: {method}")

    # 边界校验 — 不要直接 index
    params = req.get("params") or {}
    message = params.get("message") or {}
    parts = message.get("parts") or []
    if not isinstance(parts, list) or not parts:
        return _err(msg_id, -32602, "invalid params: message.parts is required and must be a non-empty list")

    text = next(
        (p.get("text", "") for p in parts if isinstance(p, dict) and p.get("kind") == "text"),
        None,
    )
    if text is None:
        return _err(msg_id, -32602, "invalid params: no text part found in message.parts")

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "id": str(uuid.uuid4()),
            "status": {
                "state": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "history": [
                {
                    "role": "agent",
                    "parts": [{"kind": "text", "text": f"echo: {text}"}],
                    "messageId": str(uuid.uuid4()),
                }
            ],
            "artifacts": [
                {
                    "artifactId": str(uuid.uuid4()),
                    "name": "echo-result",
                    "parts": [{"kind": "text", "text": f"echo: {text}"}],
                }
            ],
        },
    }


# REST 风格 alias（A2A v0.3 spec 也支持 POST /message:send）
@app.post("/message:send")
def handle_rest(req: dict):
    return handle(req)


if __name__ == "__main__":
    print("[a2a-agent] starting on http://localhost:8001")
    print("[a2a-agent] Agent Card: http://localhost:8001/.well-known/agent.json")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="warning")
