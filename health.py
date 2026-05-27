import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

START_TIME = time.time()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = int(time.time() - START_TIME)
        h, m, s = uptime // 3600, (uptime % 3600) // 60, uptime % 60
        body = f"OK | Uptime: {h}h {m}m {s}s".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args):
        pass

port = int(os.environ.get("PORT", 8080))
HTTPServer(("0.0.0.0", port), Handler).serve_forever()
