#!/usr/bin/env python3
"""
Phoenix Layer 1 Server — 长驻 HTTP 服务器，直连 Ollama API。

用途：不死鸟架构层 1 的执行后端。跳过 Hermes delegate_task 的 ~18s 初始化开销，
直接通过 Ollama API 调用本地模型，总延迟 ~0.6s。

用法：
  python3 phoenix-l1-server.py [模型名] [端口]

默认：
  模型: qwen2.5:7b
  端口: 11999

端点：
  POST /chat     {"message": "你好"}      → {"reply": "你好！"}
  POST /reset    {}                        → {"status": "ok"}

注意：
  - curl 调用时必须加 --noproxy '*'，否则 http_proxy 环境变量会拦截
  - 默认维护对话历史（最多 10 轮），/reset 清空
  - 使用 shell=False + 分离的 subprocess 启动，避免阻塞
"""

import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

DEFAULT_MODEL = "qwen2.5:7b"
DEFAULT_PORT = 11999
MAX_HISTORY = 10  # 保留最近的对话轮数


class PhoenixL1Handler(BaseHTTPRequestHandler):
    conversation_history = []  # class-level, shared across requests

    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()
        self.send_header("Allow", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid JSON"}).encode())
            return

        if self.path == "/reset":
            PhoenixL1Handler.conversation_history.clear()
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return

        if self.path != "/chat":
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "not found"}).encode())
            return

        message = data.get("message", "")
        if not message:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "empty message"}).encode())
            return

        # 构建 Ollama 请求（带历史上下文）
        ollama_messages = []
        for h in PhoenixL1Handler.conversation_history:
            ollama_messages.append({"role": "user", "content": h["user"]})
            ollama_messages.append({"role": "assistant", "content": h["assistant"]})
        ollama_messages.append({"role": "user", "content": message})

        ollama_payload = {
            "model": self.server.model_name,
            "messages": ollama_messages,
            "stream": False,
            "options": {"num_predict": 512},
        }

        try:
            result = subprocess.run(
                [
                    "curl", "-s", "--noproxy", "*",
                    "--max-time", "30",
                    "-X", "POST",
                    "http://localhost:11434/api/chat",
                    "-d", json.dumps(ollama_payload),
                ],
                capture_output=True,
                text=True,
                timeout=35,
            )

            if result.returncode != 0:
                raise RuntimeError(f"Ollama curl failed: {result.stderr.strip()}")

            ollama_resp = json.loads(result.stdout)
            reply = ollama_resp.get("message", {}).get("content", "")
            if not reply:
                reply = ollama_resp.get("response", "")

        except Exception as e:
            self._set_headers(500)
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            return

        # 保留历史
        PhoenixL1Handler.conversation_history.append(
            {"user": message, "assistant": reply}
        )
        if len(PhoenixL1Handler.conversation_history) > MAX_HISTORY:
            PhoenixL1Handler.conversation_history.pop(0)

        self._set_headers(200)
        self.wfile.write(json.dumps({"reply": reply}).encode())

    def log_message(self, format, *args):
        """静默日志，仅输出到 stderr。"""
        sys.stderr.write("[PhoenixL1] %s - %s\n" % (self.client_address[0], format % args))


class PhoenixL1Server(HTTPServer):
    """带模型名称属性的 HTTP 服务器。"""

    def __init__(self, server_address, RequestHandlerClass, model_name):
        self.model_name = model_name
        super().__init__(server_address, RequestHandlerClass)


def main():
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT

    server = PhoenixL1Server(("127.0.0.1", port), PhoenixL1Handler, model)
    print(f"[PhoenixL1] Layer 1 server started: model={model}, port={port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[PhoenixL1] Shutting down...", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()
