import http.server
import random
import hashlib
import shutil
from http.server import HTTPServer
import mimetypes
import os

class DynamicRequestHandler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            local_file_path = self.server.paths[self.path.replace("/", "")]
            with open(local_file_path, "rb") as f:
                size = os.fstat(f.fileno()).st_size
                self.protocol_version = "HTTP/1.1"
                self.send_response(200)
                mimetype , _ = mimetypes.guess_type(local_file_path)
                mimetype = mimetype if mimetype else "application/octet-stream"
                self.send_header("Content-type", mimetype)
                self.send_header("Content-Length", str(size))
                self.end_headers()
                shutil.copyfileobj(f, self.wfile)
        except KeyError:
            print(f"path {self.path} is not a valid path")

class DynamicHTTPServer(HTTPServer):
    paths = {}
    def add_file(self, file_path):
        new_path = hashlib.md5(random.randbytes(69)).hexdigest()
        self.paths[new_path] = file_path
        return new_path
