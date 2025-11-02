import socket
from typing import Dict, Optional
import json
from time import time
from onionchat.core.chat_core import ChatCore
from onionchat.utils.types import *

class PayloadChat(ChatCore):
    """Chat with payload handling.
    
    Args:
        sock (socket.socket): Socket connection object
        encoding (str): Message encoding type
        recv_timeout (float): Receive timeout
        payload_flags (str): Payload handling flags

    Flags:
        - 't': use timestamps
        - 'i': include sender's IP
    """

    def __init__(self, sock: socket.socket, encoding: str = "utf-8", recv_timeout: float = 1.0, payload_flags: str = "") -> None:
        super().__init__(sock)
        self.payload_flags = payload_flags
        self.encoding = encoding
        self.sock.settimeout(recv_timeout)
        self.include_timestamps = 't' in payload_flags
        self.include_ip = 'i' in payload_flags

    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        payload = {
            "msg": msg,
            "timestamp": time() if self.include_timestamps else None,
            "ip": self.sock.getsockname()[0] if self.include_ip else None
        }

        data = json.dumps(payload).encode(self.encoding)
        length = len(data).to_bytes(4, byteorder='big')

        try:
            self.sock.sendall(length + data)
        except (BrokenPipeError, OSError):
            return TerminateConnection()

    def recv_msg(self) -> Dict | TerminateConnection | EmptyMessage:
        length_data = self.sock.recv(4)
        if not length_data:
            return TerminateConnection()
        try:
            length = int.from_bytes(length_data, "big")
            data = self.sock.recv(length)
            payload = json.loads(data.decode(self.encoding))
            return payload
        except socket.timeout:
            return EmptyMessage()
        except (ConnectionResetError, OSError, json.JSONDecodeError):
            return TerminateConnection()
