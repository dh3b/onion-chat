from onionchat.core.conn_core import ConnectionCore
from onionchat.utils.types import EmptyConnection, TerminateConnection, EmptyMessage
from onionchat import config as cfg
from abc import ABC, abstractmethod
from typing import Optional, Dict

class ChatCore(ABC):
    """Core messaging over socket. (Virtual class)
    
    Args:
        connection (ConnectionCore): Connection prepared socket
    """

    def __init__(self, conn: ConnectionCore, encoding: str = cfg.encoding, recv_timeout: float = cfg.recv_timeout) -> None:
        self.conn = conn
        try:
            self.sock = conn.get_client()
        except ValueError as e:
            raise RuntimeError(f"Failed to get client socket from connection: {e}") from e
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