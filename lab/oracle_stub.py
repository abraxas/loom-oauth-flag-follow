#!/usr/bin/env python3
"""HTTP oracle. Records Authorization on MCP posts and answers JSON-RPC."""

from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

WITNESS = "LOOM-190-OAUTH-FLAG-FOLLOW-WITNESS"
_CAPTURES: list[dict[str, object]] = []
_LOCK = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:
        print(f"oracle {self.address_string()} {fmt % args}", flush=True)

    def _send(self, code: int, body: str) -> None:
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0]
        if path in ("/health", "/"):
            self._send(200, json.dumps({"status": "ok"}))
            return
        if path == "/captures":
            with _LOCK:
                self._send(200, json.dumps({"captures": list(_CAPTURES)}))
            return
        self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        body = raw.decode("utf-8", "replace")
        auth = self.headers.get("Authorization", "")
        path = self.path.split("?", 1)[0]
        bearer = auth.startswith("Bearer ") and len(auth) > len("Bearer ")
        rec: dict[str, object] = {
            "path": path,
            "authorization": auth,
            "bearer": bearer,
            "witness": WITNESS in auth,
        }
        with _LOCK:
            _CAPTURES.append(rec)
        print(
            f"oracle-capture path={path} bearer={bearer} witness={rec['witness']}",
            flush=True,
        )
        req_id: object = 1
        method = ""
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}
        if isinstance(parsed, dict):
            req_id = parsed.get("id", 1)
            method = str(parsed.get("method") or "")
        if method == "tools/list":
            result: dict[str, object] = {"tools": []}
        else:
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "serverInfo": {"name": "lab-oracle", "version": "1"},
            }
        self._send(200, json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}))


def main() -> None:
    host = os.environ.get("ORACLE_BIND", "0.0.0.0")
    port = int(os.environ.get("ORACLE_PORT", "80"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"oracle listening {host}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
