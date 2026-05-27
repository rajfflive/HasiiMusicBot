import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

START_TIME = time.time()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = int(time.time() - START_TIME)
        h = uptime // 3600
        m = (uptime % 3600) // 60
        s = uptime % 60
        body = f"OK | Uptime: {h}h {m}m {s}s".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Health server running on port {port}")
    server.serve_forever()
