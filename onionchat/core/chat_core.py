from socket import socket
from onionchat.utils.types import *
from abc import ABC, abstractmethod
from typing import Optional

class ChatCore(ABC):
    """Core messaging over socket. (Virtual class)
    
    Args:
        sock (socket.socket): Socket connection object
    """

    # I could make this core dependent on ConnectionCore, but maybe someone would
    # like to use it with their own socket management.
    # Besides it doesnt break anything to keep it this way.
    def __init__(self, sock: socket) -> None:
        self.sock = sock

    @abstractmethod
    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        pass

    @abstractmethod
    def recv_msg(self) -> str | TerminateConnection | EmptyMessage:
        pass

    # @abstractmethod
    # def ping(self) -> bool:
    #     pass

    def close(self) -> None:
        self.sock.close()