# query_chord.py
import socket
import sys
import json
import random

def query_node(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", port))
        key = random.randint(0, 255)
        cmd = f"find_successor {key}\r\n"
        s.sendall(cmd.encode("utf-8"))
        data = s.recv(1024)
        s.close()
        if not data:
            return None
        return json.loads(data.decode("utf-8"))
    except Exception as e:
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 query_chord.py <port>")
        sys.exit(1)
    port = int(sys.argv[1])
    result = query_node(port)
    if result:
        print(f"Lookup succeeded → successor = {result}")
    else:
        print("Lookup failed or timed out.")
