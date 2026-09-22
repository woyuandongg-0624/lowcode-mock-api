from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import re

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

    def validate_type(self, val, expected_type):
        """入参强类型校验逻辑"""
        if val is None:
            return True, "Valid"
        
        if expected_type == "string":
            is_valid = isinstance(val, str)
        elif expected_type == "number":
            is_valid = isinstance(val, (int, float)) and not isinstance(val, bool)
        elif expected_type == "boolean":
            is_valid = isinstance(val, bool)
        elif expected_type == "datetime":
            is_valid = isinstance(val, str) and bool(re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', val))
        elif expected_type == "object":
            is_valid = isinstance(val, dict)
        elif expected_type == "array":
            is_valid = isinstance(val, list)
        else:
            is_valid = True

        actual_type = type(val).__name__ if not isinstance(val, bool) else "bool"
        status_msg = "Valid" if is_valid else f"Type Mismatch: Expected {expected_type}, got {actual_type}"
        return is_valid, status_msg

    def process_request(self):
        param_type, raw_body = self.parse_request_data()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        if param_type == 'root_array':
            echo_list = raw_body if isinstance(raw_body, list) else []
            self.wfile.write(json.dumps(echo_list).encode('utf-8'))
            return

        input_dict = raw_body if isinstance(raw_body, dict) else {}
        validation_errors = {}

        # 定义字段与期望类型的映射
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

        # 遍历入参，检查是否有类型错误
        for field, exp_type in type_checks.items():
            if field in input_dict:
                is_valid, msg = self.validate_type(input_dict[field], exp_type)
                if not is_valid:
                    validation_errors[field] = msg

        # ----------------------------------------------------
        # 1. 拦截逻辑：如果有类型校验错误，返回 code: 400 失败响应
        # ----------------------------------------------------
        if validation_errors:
            error_response = {
                "code": 400,
                "msg": "Param Validation Failed",
                "errors": validation_errors,
                "receivedInput": raw_body
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
            return

        # ----------------------------------------------------
        # 2. 校验通过：返回 code: 0 正常出参
        # ----------------------------------------------------
        response_data = {
            "code": 0,
            "msg": "success",
            "receivedInput": raw_body
        }

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

        self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
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