import socket

# ===== READ FROM SOCKET =====
def read_from_socket(s):
    """Reads from socket until CRLF is received."""
    result = ""
    while True:
        data = s.recv(256)
        if not data:
            break
        # Convert bytes → string
        if isinstance(data, bytes):
            data = data.decode("utf-8")
        result += data
        if result.endswith("\r\n"):
            result = result[:-2]  # remove CRLF
            break
    return result


# ===== SEND TO SOCKET =====
def send_to_socket(s, msg):
    """Sends all data on socket, adding CRLF."""
    if isinstance(msg, str):
        msg = msg.encode("utf-8")
    elif isinstance(msg, bytes):
        pass  # already bytes
    else:
        msg = str(msg).encode("utf-8")
    s.sendall(msg + b"\r\n")
