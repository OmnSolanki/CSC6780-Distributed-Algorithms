import json
import socket
import threading

from address import Address
from settings import SIZE
from network import *

# decorator to make Remote's socket thread-safe
def requires_connection(func):
    """Initiates and cleans up connections with remote server"""
    def inner(self, *args, **kwargs):
        self.mutex_.acquire()
        try:
            self.open_connection()
            ret = func(self, *args, **kwargs)
        finally:
            self.close_connection()
            self.mutex_.release()
        return ret
    return inner


# class representing a remote peer
class Remote(object):
    def __init__(self, remote_address):
        self.address_ = remote_address
        self.mutex_ = threading.Lock()
        self.socket_ = None

    def open_connection(self):
        self.socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_.connect((self.address_.ip, self.address_.port))

    def close_connection(self):
        if self.socket_:
            self.socket_.close()
            self.socket_ = None

    def __str__(self):
        return f"Remote {self.address_}"

    def id(self, offset=0):
        return (self.address_.__hash__() + offset) % SIZE

    def send(self, msg):
        if isinstance(msg, str):
            msg = msg.encode("utf-8")
        self.socket_.sendall(msg + b"\r\n")

    def recv(self):
        # we used to have more complicated logic here
        # and we might have again, so I'm not getting rid of this yet
        return read_from_socket(self.socket_)

    def ping(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.address_.ip, self.address_.port))
            s.sendall(b"\r\n")
            s.close()
            return True
        except socket.error:
            return False

    @requires_connection
    def command(self, msg):
        self.send(msg)
        response = self.recv()
        return response

    @requires_connection
    def get_successors(self):
        self.send("get_successors")
        response = self.recv()
        if response == "":
            return []
        response = json.loads(response)
        return [Remote(Address(address[0], address[1])) for address in response]

    @requires_connection
    def successor(self):
        self.send("get_successor")
        response = json.loads(self.recv())
        return Remote(Address(response[0], response[1]))

    @requires_connection
    def predecessor(self):
        self.send("get_predecessor")
        response = self.recv()
        if response == "":
            return None
        response = json.loads(response)
        return Remote(Address(response[0], response[1]))

    @requires_connection
    def find_successor(self, id):
        self.send(f"find_successor {id}")
        response = json.loads(self.recv())
        return Remote(Address(response[0], response[1]))

    @requires_connection
    def closest_preceding_finger(self, id):
        self.send(f"closest_preceding_finger {id}")
        response = json.loads(self.recv())
        return Remote(Address(response[0], response[1]))

    @requires_connection
    def notify(self, node):
        self.send(f"notify {node.address_.ip} {node.address_.port}")
