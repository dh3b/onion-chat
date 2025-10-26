from abc import ABC, abstractmethod
from socket import socket

class ConnectionCore(ABC):
    """Abstract connection interface for P2P transports."""

    def __init__(self, dest_ip: str, port: int = 49152) -> None:
        self.dest_ip = dest_ip
        self.port = port

    @abstractmethod
    def est_connection(self, *args, **kwargs) -> None:
        """Establish connection (connect or host)."""

    @abstractmethod
    def get_client(self) -> socket:
        """Return an established client socket (raise on missing)."""