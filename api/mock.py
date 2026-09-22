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
                
                # 场景：根节点直接是数组/列表 (C# List<T>)
                if isinstance(raw_body, list):
                    return 'root_array', raw_body
                
                if isinstance(raw_body, dict) and 'type' in raw_body:
                    param_type = raw_body['type']
            except Exception:
                pass

        return param_type, raw_body

    def check_field_type(self, val, expected_type):
        """校验具体字段的数据类型是否正确"""
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
        status_msg = "Valid" if is_valid else f"Expected type '{expected_type}', but got '{actual_type}'"
        return is_valid, status_msg

    def process_request(self):
        param_type, raw_body = self.parse_request_data()

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # 1. 根节点是数组的特殊场景
        if param_type == 'root_array':
            echo_list = raw_body if isinstance(raw_body, list) else []
            self.wfile.write(json.dumps(echo_list, ensure_ascii=False).encode('utf-8'))
            return

        input_dict = raw_body if isinstance(raw_body, dict) else {}
        validation_errors = {}

        # 2. 定义 type 与必须且唯一匹配的入参字段规范
        type_spec = {
            "string": ("stringIn", "string"),
            "number": ("numberIn", "number"),
            "boolean": ("booleanIn", "boolean"),
            "datetime": ("dateTimeIn", "datetime"),
            "object": ("objectIn", "object"),
            "array_string": ("stringArrayIn", "array"),
            "array_number": ("numberArrayIn", "array"),
            "array_boolean": ("booleanArrayIn", "array"),
            "array_datetime": ("dateTimeArrayIn", "array"),
            "array_object": ("objectArrayIn", "array")
        }

        # 所有用于传入具体数据的保留入参字段列表（排除控制字段 type）
        all_input_fields = {field for field, _ in type_spec.values()}

        # ----------------------------------------------------
        # 3. 严格匹配校验逻辑
        # ----------------------------------------------------
        if param_type in type_spec:
            req_field, exp_type = type_spec[param_type]

            # 校验 A：检查 Body 中是否缺少该 type 对应的专有入参字段
            if req_field not in input_dict:
                validation_errors[req_field] = f"Missing required parameter '{req_field}' for type '{param_type}'"
            else:
                # 校验 B：检查字段数据类型是否符合规范
                is_valid, msg = self.check_field_type(input_dict[req_field], exp_type)
                if not is_valid:
                    validation_errors[req_field] = msg

            # 校验 C：严格排他性校验——不允许传入与其他 type 冲突的非相关字段
            for field in input_dict.keys():
                if field != 'type' and field in all_input_fields and field != req_field:
                    validation_errors[field] = f"Invalid field '{field}' for type '{param_type}'. Expected only '{req_field}'"

        # ----------------------------------------------------
        # 4. 如果校验失败：返回 code: 400 与详细错误原因
        # ----------------------------------------------------
        if validation_errors:
            error_response = {
                "code": 400,
                "msg": f"Validation Error: Input parameters do not match required spec for type '{param_type}'",
                "errors": validation_errors,
                "receivedInput": raw_body
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
            return

        # ----------------------------------------------------
        # 5. 校验通过：返回对应强类型的正确出参
        # ----------------------------------------------------
        response_data = {
            "code": 0,
            "msg": "success",
            "receivedInput": raw_body
        }

        if param_type == 'string':
            response_data["stringVal"] = input_dict["stringIn"]
        elif param_type == 'number':
            response_data["numberVal"] = input_dict["numberIn"]
        elif param_type == 'boolean':
            response_data["booleanVal"] = input_dict["booleanIn"]
        elif param_type == 'datetime':
            response_data["dateTimeVal"] = input_dict["dateTimeIn"]
        elif param_type == 'object':
            response_data["objectVal"] = input_dict["objectIn"]
        elif param_type == 'array_string':
            response_data["stringArray"] = input_dict["stringArrayIn"]
        elif param_type == 'array_number':
            response_data["numberArray"] = input_dict["numberArrayIn"]
        elif param_type == 'array_boolean':
            response_data["booleanArray"] = input_dict["booleanArrayIn"]
        elif param_type == 'array_datetime':
            response_data["dateTimeArray"] = input_dict["dateTimeArrayIn"]
        elif param_type == 'array_object':
            response_data["objectArray"] = input_dict["objectArrayIn"]
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