from socket import socket
from onionchat.utils.typing_classes import *
from abc import ABC, abstractmethod
from typing import Optional

class ChatCore(ABC):
    """Core messaging over socket. (Virtual class)
    
    Args:
        sock: Socket connection object
    """

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