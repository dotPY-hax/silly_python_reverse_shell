import argparse

from reverse_shell.reverse_shell_handler import reverse_shell_handler

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Silly Python Reverse Shell by dotpy")
    parser.add_argument("ip", type=str, help="The local ip")
    parser.add_argument("port", type=int, default=42069, help="The local port to listen on", nargs="?")
    args = parser.parse_args()
    reverse_shell_handler(args.ip, args.port)
