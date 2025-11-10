from socket import socket
from onionchat.utils.types import EmptyConnection, TerminateConnection, EmptyMessage
from abc import ABC, abstractmethod
from typing import Optional, Dict

class ChatCore(ABC):
    """Core messaging over socket. (Virtual class)
    
    Args:
        sock (socket.socket): Socket connection object
    """

    # I could make this core dependent on ConnectionCore, but maybe someone would
    # like to use it with their own socket management.
    # Besides it doesnt break anything to keep it this way.
    def __init__(self, sock: socket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        self.sock = sock
        self.sock.settimeout(recv_timeout)
        self.encoding = encoding

    @abstractmethod
    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        pass

    @abstractmethod
    def recv_msg(self) -> Dict | TerminateConnection | EmptyMessage:
        pass

    # @abstractmethod
    # def ping(self) -> bool:
    #     pass

    def close(self) -> None:
        self.sock.close()