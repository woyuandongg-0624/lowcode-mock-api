from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse
import json

class handler(BaseHTTPRequestHandler):
    def process_request(self):
        # 1. 读取并解析 Body 数据
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
        # 校验：检查入参是否为严格的纯字符串数组
        # ----------------------------------------------------
        if isinstance(raw_body, list):
            # 检查数组内每个元素是否均为 string
            invalid_elements = [x for x in raw_body if not isinstance(x, str)]
            
            if invalid_elements:
                # 如果包含非 string 类型的元素（如数字、对象、布尔等），返回 400 校验错误
                error_response = {
                    "code": 400,
                    "msg": "Validation Error: Every item in the array must be a string.",
                    "invalidElements": invalid_elements,
                    "receivedInput": raw_body
                }
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
                return

            # 校验成功：原样镜像返回字符串数组，或者处理后返回
            self.wfile.write(json.dumps(raw_body, ensure_ascii=False).encode('utf-8'))
            return

        # 如果入参连数组都不是（比如传了 dict 或基础类型），返回默认的字符串数组出参
        default_response = ["Apple", "Banana", "Orange", "Cherry"]
        self.wfile.write(json.dumps(default_response, ensure_ascii=False).encode('utf-8'))
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