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

        if status_code == 204 or 300 <= status_code < 400:
            body = None
        elif 200 <= status_code < 300:
            body = json.dumps({
                'code': status_code,
                'message': f'Mock response with HTTP status {status_code}'
            })
        else:
            body = json.dumps({
                'errCode': status_code,
                'errMessage': f'Mock errResponse with HTTP status {status_code}',
                "data": {
                    "id": "mock-001",
                    "name": "测试数据",
                    "status": True,
                    "count": 100,
                    "details": {
                        "type": "mock",
                        "description": "This is a mock object"
                    },
                    "items": ["A", "B", "C"]
                }
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
