from abc import ABC, abstractmethod
from socket import socket
import onionchat.config as cfg
from onionchat.utils.types import EmptySocket, EmptyConnection

class ConnectionCore(ABC):
    """Core connection creation. (Virtual class)
    
    Args:
        dest_ip (str): Destination IPv4 address
        port (int): Destination port
    """

    def __init__(self, dest_ip: str, port: int = cfg.port) -> None:
        self.dest_ip = dest_ip
        self.port = port
        self.is_server: bool | EmptyConnection = EmptyConnection()
        self.client: socket | EmptySocket = EmptySocket() 

    @abstractmethod
    def est_connection(self, *args, **kwargs) -> None:
        """Establish connection (connect or host)."""
        ...

    @abstractmethod
    def get_client(self) -> socket:
        """Return an established client socket (raise on missing)."""
        ...