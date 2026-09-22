from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re

class handler(BaseHTTPRequestHandler):
    def parse_request_data(self):
        """解析 Query 参数和 POST Body 数据"""
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
                
                # 场景：根节点直接是数组/列表 (List<T>)
                if isinstance(raw_body, list):
                    return 'root_array', raw_body
                
                if isinstance(raw_body, dict) and 'type' in raw_body:
                    param_type = raw_body['type']
            except Exception:
                pass

        return param_type, raw_body

    def validate_type(self, val, expected_type):
        """入参强类型校验逻辑函数"""
        if val is None:
            return True, "Valid (Null)"
        
        if expected_type == "string":
            is_valid = isinstance(val, str)
        elif expected_type == "number":
            # 排除 bool（在 Python 中 bool 是 int 的子类）
            is_valid = isinstance(val, (int, float)) and not isinstance(val, bool)
        elif expected_type == "boolean":
            is_valid = isinstance(val, bool)
        elif expected_type == "datetime":
            # 校验 ISO 8601 时间格式字符串，如 2026-09-21T18:46:47Z
            is_valid = isinstance(val, str) and bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', val))
        elif expected_type == "object":
            is_valid = isinstance(val, dict)
        elif expected_type == "array":
            is_valid = isinstance(val, list)
        else:
            is_valid = True

        actual_type = type(val).__name__ if not isinstance(val, bool) else "bool"
        status_msg = "Valid" if is_valid else f"Type Mismatch Error: Expected {expected_type}, but got {actual_type}"
        return is_valid, status_msg

    def process_request(self):
        param_type, raw_body = self.parse_request_data()

        # 设置响应头与 CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # ----------------------------------------------------
        # 1. 场景 A：根节点入参/出参均为数组 (对应 C# List<T>)
        # ----------------------------------------------------
        if param_type == 'root_array':
            echo_list = raw_body if isinstance(raw_body, list) else [
                {"id": 1, "name": "Item Alpha", "isActive": True},
                {"id": 2, "name": "Item Beta", "isActive": False}
            ]
            self.wfile.write(json.dumps(echo_list).encode('utf-8'))
            return

        # ----------------------------------------------------
        # 2. 场景 B：针对具体字段进行入参校验与强类型出参回传
        # ----------------------------------------------------
        input_dict = raw_body if isinstance(raw_body, dict) else {}
        validation_results = {}

        response_data = {
            "code": 0,
            "msg": "success",
            "receivedInput": raw_body
        }

        # 校验列表规则定义
        type_checks = {
            "stringIn": "string",
            "numberIn": "number",
            "booleanIn": "boolean",
            "dateTimeIn": "datetime",
            "objectIn": "object",
            "stringArrayIn": "array",
            "numberArrayIn": "array",
            "booleanArrayIn": "array",
            "dateTimeArrayIn": "array",
            "objectArrayIn": "array"
        }

        # 执行入参类型校验
        for field, exp_type in type_checks.items():
            if field in input_dict:
                is_valid, msg = self.validate_type(input_dict[field], exp_type)
                validation_results[field] = msg

        if validation_results:
            response_data["inputValidation"] = validation_results

        # 分支逻辑：将正确类型的出参填充给低代码平台绑定
        if param_type == 'string':
            response_data["stringVal"] = input_dict.get("stringIn", "Hello LowCode")

        elif param_type == 'number':
            response_data["numberVal"] = input_dict.get("numberIn", 2026)

        elif param_type == 'boolean':
            response_data["booleanVal"] = input_dict.get("booleanIn", True)

        elif param_type == 'datetime':
            response_data["dateTimeVal"] = input_dict.get("dateTimeIn", "2026-09-21T18:46:47Z")

        elif param_type == 'object':
            response_data["objectVal"] = input_dict.get("objectIn", {"userId": 1001, "userName": "Alice"})

        elif param_type == 'array_string':
            response_data["stringArray"] = input_dict.get("stringArrayIn", ["apple", "banana"])

        elif param_type == 'array_number':
            response_data["numberArray"] = input_dict.get("numberArrayIn", [10, 20, 30.5])

        elif param_type == 'array_boolean':
            response_data["booleanArray"] = input_dict.get("booleanArrayIn", [True, False])

        elif param_type == 'array_datetime':
            response_data["dateTimeArray"] = input_dict.get("dateTimeArrayIn", ["2026-01-01T08:00:00Z"])

        elif param_type == 'array_object':
            response_data["objectArray"] = input_dict.get("objectArrayIn", [{"itemId": 101, "itemName": "Item A"}])

        elif param_type == 'all_types':
            response_data.update({
                "stringVal": input_dict.get("stringIn", "Test String"),
                "numberVal": input_dict.get("numberIn", 123.45),
                "booleanVal": input_dict.get("booleanIn", True),
                "dateTimeVal": input_dict.get("dateTimeIn", "2026-09-21T18:46:47Z"),
                "objectVal": input_dict.get("objectIn", {"key": "value"}),
                "stringArray": input_dict.get("stringArrayIn", ["A", "B"]),
                "numberArray": input_dict.get("numberArrayIn", [1, 2, 3]),
                "booleanArray": input_dict.get("booleanArrayIn", [True, False]),
                "dateTimeArray": input_dict.get("dateTimeArrayIn", ["2026-01-01T00:00:00Z"]),
                "objectArray": input_dict.get("objectArrayIn", [{"id": 1}])
            })
        else:
            response_data["msg"] = "Ready for low-code platform parameter validation testing."

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