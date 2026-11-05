from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import time


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        values = parse_qs(urlparse(self.path).query).get('seconds', ['5'])
        try:
            delay_seconds = int(values[0])
        except (IndexError, ValueError):
            self.send_json(400, 'seconds must be an integer from 1 to 30.')
            return

        if not 1 <= delay_seconds <= 30:
            self.send_json(400, 'seconds must be an integer from 1 to 30.')
            return

        time.sleep(delay_seconds)
        self.send_json(200, f'Response delayed by {delay_seconds} seconds.', delay_seconds)

    def send_json(self, status_code, message, delay_seconds=None):
        body = {'code': status_code, 'message': message}
        if delay_seconds is not None:
            body['delaySeconds'] = delay_seconds

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(body).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
