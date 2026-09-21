from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. 解析请求 URL 中的 Query 参数 (?type=xxx)
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        
        # 获取 type 参数，默认为空
        type_param = query_params.get('type', [None])[0]

        # 2. 设置响应状态码与响应头（含 CORS 跨域配置）
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # 3. 根据 type 参数匹配不同的数据类型与结构
        response_data = {}

        if type_param == 'string':
            response_data = {"code": 0, "msg": "success", "data": "Hello LowCode"}
            
        elif type_param == 'number':
            response_data = {"code": 0, "msg": "success", "data": 2026}
            
        elif type_param == 'boolean':
            response_data = {"code": 0, "msg": "success", "data": True}
            
        elif type_param == 'array':
            response_data = {"code": 0, "msg": "success", "data": ["apple", "banana", "cherry"]}
            
        elif type_param == 'null':
            response_data = {"code": 0, "msg": "success", "data": None}
            
        elif type_param == 'missing':
            # 故意缺少 data 字段
            response_data = {"code": 0, "msg": "success"}
            
        elif type_param == 'mismatch':
            # 数字格式的字符串，测试类型混淆
            response_data = {"code": 0, "msg": "success", "data": "2026"}
            
        elif type_param == 'nested':
            # 复杂嵌套结构
            response_data = {
                "code": 0,
                "msg": "success",
                "data": {
                    "user": {
                        "id": 1001,
                        "profile": {
                            "name": "Tester",
                            "is_admin": True,
                            "tags": ["qa", "automation"]
                        }
                    },
                    "list": [
                        {"item_id": 1, "val": 10.5},
                        {"item_id": 2, "val": None}
                    ]
                }
            }
        else:
            response_data = {
                "code": 0,
                "msg": "Please specify a valid ?type= parameter.",
                "supported_types": ["string", "number", "boolean", "array", "null", "missing", "mismatch", "nested"]
            }

        # 4. 将 Python 字典序列化为 JSON 并返回
        self.wfile.write(json.dumps(response_data).encode('utf-8'))
        return

    # 处理 CORS 预检请求
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        return