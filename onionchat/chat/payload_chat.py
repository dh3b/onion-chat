import socket
from typing import Dict, Optional
import json
from time import time
import onionchat.config as cfg
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.chat_core import ChatCore
from onionchat.utils.types import *

class PayloadChat(ChatCore):
    """Chat with payload handling.
    
    Args:
        connection (ConnectionCore): Connection prepared socket
        encoding (str): Message encoding type
        recv_timeout (float): Receive timeout
        payload_flags (str): Payload handling flags

    Flags:
        - 't': use timestamps
        - 'i': include sender's IP
    """

    def __init__(
        self,
        conn: ConnectionCore,
        encoding: str = cfg.encoding,
        recv_timeout: float = cfg.recv_timeout,
        payload_flags: str = cfg.payload_flags
    ) -> None:
        super().__init__(conn, encoding, recv_timeout)
        self.payload_flags = payload_flags
        self.include_timestamps = 't' in payload_flags
        self.include_ip = 'i' in payload_flags

    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        payload = {
            "msg": msg,
            "timestamp": time() if self.include_timestamps else None,
            "ip": self.sock.getsockname()[0] if self.include_ip else None
        }

        data = json.dumps(payload).encode(self.encoding)
        length = len(data).to_bytes(cfg.frame_len_bytes, byteorder=cfg.byteorder)

        try:
            self.sock.sendall(length + data)
        except (BrokenPipeError, OSError):
            return TerminateConnection()

    def recv_msg(self) -> Dict | TerminateConnection | EmptyMessage:
        try:
            length_data = self.sock.recv(cfg.frame_len_bytes)
            if not length_data:
                return TerminateConnection()
            length = int.from_bytes(length_data, cfg.byteorder)
            data = self.sock.recv(length)
            payload = json.loads(data.decode(self.encoding))
            return payload
        except socket.timeout:
            return EmptyMessage()
        except (ConnectionResetError, OSError, json.JSONDecodeError):
            return TerminateConnection()
