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
                
                # 场景：根节点直接是数组 (List<T>)
                if isinstance(raw_body, list):
                    return 'root_array', raw_body
                
                if isinstance(raw_body, dict) and 'type' in raw_body:
                    param_type = raw_body['type']
            except Exception:
                pass

        return param_type, raw_body

    def check_field_type(self, val, expected_type):
        """严格的数据类型校验函数（精确区分 int 和 float/double）"""
        if val is None:
            return True, "Valid"
        
        if expected_type == "int":
            is_valid = isinstance(val, int) and not isinstance(val, bool)
        elif expected_type == "double":
            is_valid = isinstance(val, float) and not isinstance(val, bool)
        elif expected_type == "string":
            is_valid = isinstance(val, str)
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

    def send_cors_headers(self):
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def process_request(self):
        param_type, raw_body = self.parse_request_data()

        # 1. 根节点直接是数组的特殊场景
        if param_type == 'root_array':
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            echo_list = raw_body if isinstance(raw_body, list) else []
            self.wfile.write(json.dumps(echo_list, ensure_ascii=False).encode('utf-8'))
            return

        input_dict = raw_body if isinstance(raw_body, dict) else {}
        validation_errors = {}

        # 2. 定义 type 与必须匹配的（入参字段, 类型描述）规范
        type_spec = {
            "int": ("intIn", "int"),
            "double": ("doubleIn", "double"),
            "string": ("stringIn", "string"),
            "boolean": ("booleanIn", "boolean"),
            "datetime": ("dateTimeIn", "datetime"),
            "object": ("objectIn", "object"),
            "array_int": ("intArrayIn", "array"),
            "array_double": ("doubleArrayIn", "array"),
            "array_string": ("stringArrayIn", "array"),
            "array_boolean": ("booleanArrayIn", "array"),
            "array_datetime": ("dateTimeArrayIn", "array"),
            "array_object": ("objectArrayIn", "array"),
            "all_types": (None, None)
        }

        # ----------------------------------------------------
        # 3. 校验逻辑（包含非法 type 校验）
        # ----------------------------------------------------
        if param_type in type_spec:
            req_field, exp_type = type_spec[param_type]

            if req_field:
                # 校验 A：检查 Body 中是否缺少当前 type 对应的入参字段
                if req_field not in input_dict:
                    validation_errors[req_field] = f"Missing required parameter '{req_field}' for type '{param_type}'"
                else:
                    # 校验 B：检查当前 type 对应的字段类型是否正确
                    is_valid, msg = self.check_field_type(input_dict[req_field], exp_type)
                    if not is_valid:
                        validation_errors[req_field] = msg
        elif param_type is not None:
            # 校验 C：传入了不支持或拼错的 type（如 "objec"）
            validation_errors["type"] = f"Unsupported or invalid type '{param_type}'. Supported types: {list(type_spec.keys())}"

        # ----------------------------------------------------
        # 4. 校验失败：返回 HTTP 400 响应
        # ----------------------------------------------------
        if validation_errors:
            self.send_response(400)
            self.send_cors_headers()
            self.end_headers()
            
            error_response = {
                "code": 400,
                "msg": f"Validation Error: Invalid parameter or unsupported type '{param_type}'.",
                "errors": validation_errors,
                "receivedInput": raw_body
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
            return

        # ----------------------------------------------------
        # 5. 校验通过：返回 HTTP 200 响应及对应的强类型出参
        # ----------------------------------------------------
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

        response_data = {
            "code": 0,
            "msg": "success",
            "receivedInput": raw_body
        }

        if param_type == 'int':
            response_data["intVal"] = input_dict["intIn"]
        elif param_type == 'double':
            response_data["doubleVal"] = input_dict["doubleIn"]
        elif param_type == 'string':
            response_data["stringVal"] = input_dict["stringIn"]
        elif param_type == 'boolean':
            response_data["booleanVal"] = input_dict["booleanIn"]
        elif param_type == 'datetime':
            response_data["dateTimeVal"] = input_dict["dateTimeIn"]
        elif param_type == 'object':
            response_data["objectVal"] = input_dict["objectIn"]
        elif param_type == 'array_int':
            response_data["intArray"] = input_dict["intArrayIn"]
        elif param_type == 'array_double':
            response_data["doubleArray"] = input_dict["doubleArrayIn"]
        elif param_type == 'array_string':
            response_data["stringArray"] = input_dict["stringArrayIn"]
        elif param_type == 'array_boolean':
            response_data["booleanArray"] = input_dict["booleanArrayIn"]
        elif param_type == 'array_datetime':
            response_data["dateTimeArray"] = input_dict["dateTimeArrayIn"]
        elif param_type == 'array_object':
            response_data["objectArray"] = input_dict["objectArrayIn"]
        elif param_type == 'all_types':
            response_data.update({
                "intVal": input_dict.get("intIn", 2026),
                "doubleVal": input_dict.get("doubleIn", 99.99),
                "stringVal": input_dict.get("stringIn", "Test String"),
                "booleanVal": input_dict.get("booleanIn", True),
                "dateTimeVal": input_dict.get("dateTimeIn", "2026-09-21T18:46:47Z"),
                "objectVal": input_dict.get("objectIn", {"key": "value"}),
                "intArray": input_dict.get("intArrayIn", [1, 2, 3]),
                "doubleArray": input_dict.get("doubleArrayIn", [10.5, 20.8, 30.0]),
                "stringArray": input_dict.get("stringArrayIn", ["A", "B"]),
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
        self.send_cors_headers()
        self.end_headers()
        return