from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        values = parse_qs(urlparse(self.path).query).get('code', [])
        try:
            status_code = int(values[0])
        except (IndexError, ValueError):
            self.send_error_response(400, 'Path code must be an integer from 200 to 599.')
            return

        if not 200 <= status_code <= 599:
            self.send_error_response(400, 'Path code must be an integer from 200 to 599.')
            return

        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        if status_code not in (204, 205, 304):
            if status_code == 200:
                body = json.dumps({
                    'code': status_code,
                    'message': f'Mock response with HTTP status {status_code}'
                })
            else:
                body = json.dumps({
                    'errCode': status_code,
                    'errMessage': f'Mock errResponse with HTTP status {status_code}'
                })
            self.wfile.write(body.encode('utf-8'))

    def send_error_response(self, status_code, message):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps({
            'code': status_code,
            'message': message
        }).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
