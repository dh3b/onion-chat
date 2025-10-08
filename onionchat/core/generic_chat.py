import socket
from onionchat.utils.typing_classes import *

class GenericChatCore:
    """Core messaging over socket.
    
    Args:
        sock: Socket connection object
        encoding: Message encoding type
        recv_timeout: Receive timeout
    """

    def __init__(self, sock: socket.socket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        self.sock = sock
        self.sock.settimeout(recv_timeout)
        self.encoding = encoding
        self.running = False

    def send_msg(self, msg: str) -> None:
        """Send message to peer.
        
        Args:
            msg: Message to send
        """

        self.sock.sendall(msg.encode(self.encoding))

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