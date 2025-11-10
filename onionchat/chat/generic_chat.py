import socket
import json
from onionchat.utils.types import *
from onionchat.core.chat_core import ChatCore
from typing import Optional, Dict

class GenericChat(ChatCore):
    """Core messaging over socket.
    
    Args:
        sock (socket.socket): Socket connection object
        encoding (str): Message encoding type
        recv_timeout (float): Receive timeout
    """

    def __init__(self, sock: socket.socket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        super().__init__(sock, encoding, recv_timeout)

    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        """Send message to peer.
        
        Args:
            msg: Message to send
        """

        data = {
            "msg": msg
        }

        try:
            self.sock.sendall(json.dumps(data).encode(self.encoding))
        except (BrokenPipeError, OSError):
            return TerminateConnection()

    def recv_msg(self) -> TerminateConnection | EmptyMessage | Dict:
        """Receive message from peer.
        
        Returns:
            Message string, EmptyMessage on timeout, or TerminateConnection
        """

        try:
            data = self.sock.recv(1024)
            if not data:
                return TerminateConnection()
            return json.loads(data.decode(self.encoding))
        except socket.timeout:
            return EmptyMessage()
        except (ConnectionResetError, OSError):
            return TerminateConnection()