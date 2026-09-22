from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def process_request(self):
        # 1. 解析 Query 参数
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        param_type = query_params.get('type', [None])[0]

        # 2. 读取并解析 Body 数据
        raw_body = None
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            try:
                body_bytes = self.rfile.read(content_length)
                raw_body = json.loads(body_bytes.decode('utf-8'))
            except Exception:
                pass

        # 设置 HTTP 响应头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # ----------------------------------------------------
        # 场景 A：入参本身就是 JSON 数组 [ ... ]
        # ----------------------------------------------------
        if isinstance(raw_body, list):
            # 根节点是数组时，直接将接收到的数组原样作为出参返回
            self.wfile.write(json.dumps(raw_body, ensure_ascii=False).encode('utf-8'))
            return

        # ----------------------------------------------------
        # 场景 B：根节点是对象，根据 type 参数直接返回纯数组出参
        # ----------------------------------------------------
        input_dict = raw_body if isinstance(raw_body, dict) else {}
        if not param_type and 'type' in input_dict:
            param_type = input_dict['type']

        # 预设的强类型纯数组响应数据
        array_responses = {
            "int": [101, 202, 303, 404, 505],
            "double": [99.9, 88.8, 77.7, 66.6],
            "string": ["Apple", "Banana", "Orange", "Grape"],
            "boolean": [True, False, True, True],
            "datetime": ["2026-01-01T00:00:00Z", "2026-09-21T18:46:47Z"],
            "object": [
                {"id": 1, "name": "Item Alpha", "status": "active"},
                {"id": 2, "name": "Item Beta", "status": "inactive"}
            ]
        }

        # 如果匹配到对应的 type，直接返回纯数组 [ ... ]
        if param_type in array_responses:
            self.wfile.write(json.dumps(array_responses[param_type], ensure_ascii=False).encode('utf-8'))
            return

        # 场景 C：如果既不是数组入参，也没有匹配到 type，默认返回提示列表
        default_array = [
            {"notice": "This endpoint returns a raw JSON Array."},
            {"supported_types": ["int", "double", "string", "boolean", "datetime", "object"]}
        ]
        self.wfile.write(json.dumps(default_array, ensure_ascii=False).encode('utf-8'))
        return

    def do_GET(self):
        self.process_request()

    def do_POST(self):
        self.process_request()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return