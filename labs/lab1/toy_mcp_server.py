#!/usr/bin/env python3
"""
最小 MCP server — 50 行实现完整的 MCP 协议 stdio transport
教学目的：让你看清 MCP 不是黑魔法，就是 JSON-RPC 2.0 over stdin/stdout

跑法（教学）：
    printf '%s\n%s\n%s\n' \
      '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
      '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
      '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"echo","arguments":{"text":"hi"}}}' \
      | python3 toy_mcp_server.py
"""
import sys
import json


def respond(id_, result=None, error=None):
    """MCP 响应必须从 stdout 输出，每条一行 JSON。stderr 留给日志。"""
    msg = {"jsonrpc": "2.0", "id": id_}
    if error:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def log(text):
    sys.stderr.write(f"[toy-mcp] {text}\n")
    sys.stderr.flush()


TOOLS = [{
    "name": "echo",
    "description": "把输入原样返回（教学用最小工具）",
    "inputSchema": {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    },
}]


def handle(msg):
    method = msg.get("method")
    id_ = msg.get("id")
    params = msg.get("params") or {}

    if method == "initialize":
        # 客户端（如 Claude Code）发来的握手——告诉我们它支持什么
        respond(id_, {
            "protocolVersion": "2025-03-26",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "toy-mcp", "version": "0.1.0"},
        })

    elif method == "tools/list":
        # 客户端来问"你有哪些工具"
        respond(id_, {"tools": TOOLS})

    elif method == "tools/call":
        # 客户端来调用某个工具
        name = params.get("name")
        args = params.get("arguments") or {}
        if name == "echo":
            respond(id_, {
                "content": [{"type": "text", "text": f"echo: {args.get('text', '')}"}]
            })
        else:
            respond(id_, error={"code": -32602, "message": f"unknown tool: {name}"})

    elif method and method.startswith("notifications/"):
        # 通知不需要响应
        log(f"notification {method} (no response)")

    else:
        respond(id_, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    log("starting")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            handle(json.loads(line))
        except Exception as e:
            log(f"error: {e}")


if __name__ == "__main__":
    main()
