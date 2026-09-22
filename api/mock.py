from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def parse_request_data(self):
        """解析请求中的参数：优先从 POST Body 读取，若没有则从 URL Query 读取"""
        param_type = None
        raw_body = None
        
        # 1. 尝试从 URL Query 参数获取 ?type=xxx
        parsed_path = urlparse(self.path)
        query_params = parse_qs(parsed_path.query)
        if 'type' in query_params:
            param_type = query_params['type'][0]

        # 2. 从 POST Body 读取
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            try:
                body_bytes = self.rfile.read(content_length)
                raw_body = json.loads(body_bytes.decode('utf-8'))
                
                # 如果整个根入参就是数组/列表
                if isinstance(raw_body, list):
                    return 'root_array', raw_body
                
                if isinstance(raw_body, dict) and 'type' in raw_body:
                    param_type = raw_body['type']
            except Exception:
                pass

        return param_type, raw_body

    def process_request(self):
        param_type, raw_body = self.parse_request_data()

        # 设置响应头与 CORS 跨域配置
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # ----------------------------------------------------
        # 场景 A：整个根节点直接返回数组（C# 映射为 List<T>）
        # ----------------------------------------------------
        if param_type == 'root_array':
            response_data = [
                {"id": 1, "name": "Item Alpha", "isActive": True},
                {"id": 2, "name": "Item Beta", "isActive": False}
            ]
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        # ----------------------------------------------------
        # 场景 B：强类型对象字段映射（针对 C# 强类型 Model 解析）
        # ----------------------------------------------------
        # 基础公共返回结构
        response_data = {
            "code": 0,
            "msg": "success"
        }

        if param_type == 'string':
            response_data["stringVal"] = "Hello LowCode"

        elif param_type == 'number':
            response_data["numberVal"] = 2026

        elif param_type == 'boolean':
            response_data["booleanVal"] = True

        elif param_type == 'datetime':
            # C# DateTime/DateTimeOffset 可直接反序列化 ISO 8601 字符串
            response_data["dateTimeVal"] = "2026-09-21T18:46:47Z"

        elif param_type == 'object':
            response_data["objectVal"] = {
                "userId": 1001,
                "userName": "Alice",
                "role": "admin"
            }

        # --- 各基础类型的数组 (C# List<string>, List<int> 等) ---
        elif param_type == 'array_string':
            response_data["stringArray"] = ["apple", "banana", "cherry"]

        elif param_type == 'array_number':
            response_data["numberArray"] = [10, 20, 30, 100]

        elif param_type == 'array_boolean':
            response_data["booleanArray"] = [True, False, True]

        elif param_type == 'array_datetime':
            response_data["dateTimeArray"] = [
                "2026-01-01T08:00:00Z",
                "2026-09-21T18:46:47Z"
            ]

        elif param_type == 'array_object':
            response_data["objectArray"] = [
                {"itemId": 101, "itemName": "Item A", "inStock": True},
                {"itemId": 102, "itemName": "Item B", "inStock": False}
            ]

        elif param_type == 'null':
            response_data["nullVal"] = None

        elif param_type == 'all_types':
            # 一次性返回所有类型的字段，方便在低代码平台生成强类型 DTO/Model 结构
            response_data.update({
                "stringVal": "Test String",
                "numberVal": 123.45,
                "booleanVal": True,
                "dateTimeVal": "2026-09-21T18:46:47Z",
                "objectVal": {"key": "value"},
                "stringArray": ["A", "B"],
                "numberArray": [1, 2, 3],
                "booleanArray": [True, False],
                "dateTimeArray": ["2026-01-01T00:00:00Z"],
                "objectArray": [{"id": 1}]
            })

        else:
            response_data = {
                "code": 0,
                "msg": "Please specify a valid ?type= parameter.",
                "supported_types": [
                    "string", "number", "boolean", "datetime", "object",
                    "array_string", "array_number", "array_boolean", "array_datetime", "array_object",
                    "root_array", "all_types", "null"
                ]
            }

        self.wfile.write(json.dumps(response_data).encode('utf-8'))
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