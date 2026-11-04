from http.server import BaseHTTPRequestHandler
import socket
import struct
import sys


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.close_connection = True
        linger = struct.pack('hh', 1, 0) if sys.platform == 'win32' else struct.pack('ii', 1, 0)
        self.connection.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_LINGER,
            linger
        )
        self.connection.close()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
