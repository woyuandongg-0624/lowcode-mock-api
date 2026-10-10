from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import time

class handler(BaseHTTPRequestHandler):
    def parse_request_data(self):
        param_type = None
        raw_body = None
        
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        if 'type' in query_params:
            param_type = query_params['type'][0]

        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            try:
                body_bytes = self.rfile.read(content_length)
                raw_body = json.loads(body_bytes.decode('utf-8'))
                
                if isinstance(raw_body, list):
                    return 'root_array', raw_body
                
                if isinstance(raw_body, dict) and 'type' in raw_body:
                    param_type = raw_body['type']
            except Exception:
                pass

        return param_type, raw_body

    def send_cors_headers(self):
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def process_request(self):
        param_type, raw_body = self.parse_request_data()

        # ----------------------------------------------------
        # 核心：固定等待 125 秒，确保响应时间超过 100 秒
        # ----------------------------------------------------
        time.sleep(125)

        # ----------------------------------------------------
        # 设置 HTTP 状态码为 200 OK 并返回标准 JSON
        # ----------------------------------------------------
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

        response_data = {
            "code": 0,
            "msg": "success after 125 seconds delay",
            "receivedInput": raw_body,
            "delaySeconds": 125
        }

        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
        return

    def do_GET(self):
        self.process_request()

    def do_POST(self):
        self.process_request()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        return