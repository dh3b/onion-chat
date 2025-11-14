from socket import socket
from onionchat.utils.types import EmptyConnection, TerminateConnection, EmptyMessage
from onionchat import config as cfg
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
    def __init__(self, sock: socket, encoding: str = cfg.encoding, recv_timeout: float = cfg.recv_timeout) -> None:
        self.sock = sock
        self.sock.settimeout(recv_timeout)
        self.encoding = encoding

    @abstractmethod
    def send_msg(self, msg: str) -> Optional[TerminateConnection]:
        ...

    @abstractmethod
    def recv_msg(self) -> Dict | TerminateConnection | EmptyMessage:
        ...

    # @abstractmethod
    # def ping(self) -> bool:
    #     pass

    def close(self) -> None:
        self.sock.close()