#!/usr/bin/env python3
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM_HOST = "127.0.0.1"
UPSTREAM_PORT = 8765
LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 8766

HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}


class ReadOnlyProxy(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _proxy(self, head_only=False):
        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=15)
        try:
            headers = {
                "Host": f"{UPSTREAM_HOST}:{UPSTREAM_PORT}",
                "User-Agent": self.headers.get("User-Agent", "Tuus-readonly-proxy"),
                "Accept": self.headers.get("Accept", "*/*"),
                "Accept-Language": self.headers.get("Accept-Language", "nl,en;q=0.8"),
                "Cache-Control": "no-cache",
            }
            conn.request("GET", self.path, headers=headers)
            resp = conn.getresponse()
            body = b"" if head_only else resp.read()

            self.send_response(resp.status, resp.reason)
            for key, value in resp.getheaders():
                if key.lower() in HOP_BY_HOP or key.lower() == "content-length":
                    continue
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Tuus-Mode", "read-only")
            self.end_headers()
            if body:
                self.wfile.write(body)
        finally:
            conn.close()

    def do_GET(self):
        self._proxy(False)

    def do_HEAD(self):
        self._proxy(True)

    def _deny_write(self):
        body = b'{"error":"read-only public demo"}'
        self.send_response(405, "Method Not Allowed")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Allow", "GET, HEAD")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    do_POST = _deny_write
    do_PUT = _deny_write
    do_PATCH = _deny_write
    do_DELETE = _deny_write

    def log_message(self, fmt, *args):
        print(f"{self.client_address[0]} - {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ReadOnlyProxy)
    print(f"Tuus read-only proxy: http://{LISTEN_HOST}:{LISTEN_PORT}")
    print(f"Upstream: http://{UPSTREAM_HOST}:{UPSTREAM_PORT}")
    server.serve_forever()
