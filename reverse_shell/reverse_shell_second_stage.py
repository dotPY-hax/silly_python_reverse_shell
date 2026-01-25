import subprocess
import time
import threading
import os


class InteractiveShell:
    def __init__(self):
        self.shell_process = None
        self.reader = None
        self.keep_reading = True

    def bash(self):
        self.spawn_interactive_shell("/bin/bash")

    def powershell(self):
        self.spawn_interactive_shell("powershell.exe -ep bypass")

    def spawn_interactive_shell(self, shell_command):
        shell_command = shell_command.split(" ")
        bash = subprocess.Popen(shell_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True, start_new_session=True)
        os.set_blocking(bash.stdout.fileno(), False)
        os.set_blocking(bash.stderr.fileno(), False)
        self.shell_process = bash
        self.reader = threading.Thread(target=self.reader_thread_function)
        self.reader.start()

    def reader_thread_function(self):
         while self.keep_reading:
            result = self._read()
            if result: print(result, end="", flush=True)
            time.sleep(0.25)

    def input(self, command_line):
        self.shell_process.stdin.write(command_line)
        self.shell_process.stdin.flush()

    def _read(self):
        data = ""
        self.shell_process.stdout.flush()
        self.shell_process.stderr.flush()
        stdout = "".join(self.shell_process.stdout.readlines())
        stderr = "".join(self.shell_process.stderr.readlines())
        stdout = stdout if isinstance(stdout, str) else ""
        stderr = stderr if isinstance(stderr, str) else ""
        data += stdout
        data += stderr
        return data

    def kill(self):
        self.keep_reading = False
        self.shell_process.terminate()

interactive_shell = InteractiveShell()
if os.name == 'nt':
    interactive_shell.powershell()
else:
    interactive_shell.bash()

def run_shell_command(command):
    command = command if isinstance(command, str) else command.encode()
    interactive_shell.input(command)

def os_system(command):
    process = subprocess.run(command, shell=True, capture_output=True)
    output = process.stdout + process.stderr
    print(output.decode())

os.system = os_system
# =============== CUT HERE =====================

# THIS DOESNT WORK!! yet...
from importlib.abc import SourceLoader
import importlib.util
import sys

class FilelessSourceLoader(SourceLoader):
    def __init__(self, module_name, source):
        self.source_bytes = source
        self.name = module_name
        super().__init__()

    def get_data(self, path):
        return self.source_bytes

    def get_filename(self, fullname):
        return ""

# THIS ONLY WORKS HALF yet...
def import_module_from_source(module_name, source):
    loader = FilelessSourceLoader(module_name, source)
    spec = importlib.util.spec_from_loader(module_name, loader)
    module_object = importlib.util.module_from_spec(spec)
    loader.exec_module(module_object)
    sys.modules[module_name] = module_object
    globals()[module_name] = module_object
    locals()[module_name] = module_object

# DEBUG ONLY!!
def import_module_from_path(name, path):
    with open(path, "rb") as f:
        import_module_from_source(name, f.read())

