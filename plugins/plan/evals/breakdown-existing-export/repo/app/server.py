from datetime import date
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from app.orders import export_orders_csv


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/admin/orders/export.csv":
            q = parse_qs(url.query)
            body = export_orders_csv(
                date.fromisoformat(q["from"][0]), date.fromisoformat(q["to"][0])
            )
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.end_headers()
            self.wfile.write(body.encode())
            return
        self.send_response(404)
        self.end_headers()
