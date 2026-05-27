import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

port = int(os.environ.get("PORT", 8080))
HTTPServer(("0.0.0.0", port), Handler).serve_forever()
