import socket
from typing import Dict, Optional
import json
from time import time
import onionchat.config as cfg
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.chat_core import ChatCore
from onionchat import __protocol_version__
from onionchat.utils.types import *

class PayloadChat(ChatCore):
    """Chat with payload handling.
    
    Args:
        connection (ConnectionCore): Connection prepared socket
        encoding (str): Message encoding type
        recv_timeout (float): Receive timeout
        payload_flags (str): Payload handling flags

    Flags:
        Metadata:
        - 's': sender's IP
        - 'r': receiver's IP
        - 't': timestamp
        - 'x': data type (else raw text)
        - 'v': protocol version
        Encryption:
        - 'e': signature data
        - 'n': sequence number
        Extra:
        - 'p': push title
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

        # flag functionallity
        self.flag_encode = {
            's': self.conn.host_ip,
            'r': self.conn.dest_ip,
            't': lambda: time(),
            'x': 'text',
            'v': __protocol_version__,
            'e': None, # signature data placeholder
            'n': None, # sequence number placeholder
            'p': None # push title placeholder
        }

        # flag titles
        self.flag_titles = {
            's': "sender_ip",
            'r': "recv_ip",
            't': "timestamp",
            'x': "data_type",
            'v': "ver",
            'e': "sig_data",
            'n': "seq_num",
            'p': "push"
        }    

    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        payload = {}
        for flag in self.payload_flags:
            val = self.flag_encode[flag]
            # call callables (e.g., timestamp) to get the actual value
            payload[self.flag_titles[flag]] = val() if callable(val) else val
        payload["msg"] = msg

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
            data = self.sock.recv(length).decode(self.encoding)
            return json.loads(data)
        except json.JSONDecodeError:
            return {'msg': 'system[JSON decode error. Invalid message format.]'}
        except socket.timeout:
            return EmptyMessage()
        except (ConnectionResetError, OSError):
            return TerminateConnection()
