import socket
from onionchat.utils.types import *
from onionchat.core.chat_core import ChatCore
from typing import Optional

class GenericChatCore(ChatCore):
    """Core messaging over socket.
    
    Args:
        sock: Socket connection object
        encoding: Message encoding type
        recv_timeout: Receive timeout
    """

    def __init__(self, sock: socket.socket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        super().__init__(sock)
        self.sock.settimeout(recv_timeout)
        self.encoding = encoding

    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        """Send message to peer.
        
        Args:
            msg: Message to send
        """

        try:
            self.sock.sendall(msg.encode(self.encoding))
        except (BrokenPipeError, OSError):
            return TerminateConnection()

    def recv_msg(self) -> TerminateConnection | EmptyMessage | str:
        """Receive message from peer.
        
        Returns:
            Message string, EmptyMessage on timeout, or TerminateConnection
        """

        try:
            data = self.sock.recv(1024)
            if not data:
                return TerminateConnection()
            return data.decode(self.encoding)
        except socket.timeout:
            return EmptyMessage()
        except (ConnectionResetError, OSError):
            return TerminateConnection()