from time import time
import socket
import logging
from onionchat.utils.types import *
from onionchat.core.conn_core import ConnectionCore

logger = logging.getLogger(__name__)

class PeerConnection(ConnectionCore):
    """P2P connection handler.

    Args:
        dest_ip (str): Destination IPv4 address
        port (int): Destination port    
    """

    def __init__(self, dest_ip, port=49152) -> None:
        super().__init__(dest_ip, port)
        try:
            socket.inet_aton(dest_ip)
        except socket.error:
            logger.critical(f"{dest_ip} is not a valid ipv4 address")
            raise ValueError(f"{dest_ip} is not a valid ipv4 address")
        
        self.host_ip = socket.gethostbyname(socket.gethostname())
        self.rejected = []
        self.client = EmptySocket()

    def est_connection(self, con_attempt_lim: int = 5, con_timeout: float = 5.0, host_timeout: float = 1.0, host_listen_lim: float = 60.0) -> None:
        """Establish connection by connecting or hosting.
        
        Args:
            con_attempt_lim (int): Max connection attempts
            con_timeout (float): Timeout per connection attempt
            host_timeout (float): Timeout for accepting connections
            host_listen_lim (float): Max time to listen as host
        """

        self.client = self._con(con_attempt_lim, con_timeout)
        self.is_server = False if not isinstance(self.client, EmptySocket) else EmptyConnection()

        if isinstance(self.client, EmptySocket):
            logger.warning("Failed to connect, setting up host")
            self.client = self._host(host_listen_lim, host_timeout)
        self.is_server = True if not isinstance(self.client, EmptySocket) else EmptyConnection()

        if isinstance(self.client, EmptySocket):
            logger.error(f"Failed to peer with {self.dest_ip}. Host listen timed out ({host_listen_lim})")

    def _con(self, attempt_lim: int, timeout: float) -> socket.socket | EmptySocket:
        """Attempt to connect to peer.
        
        Args:
            attempt_lim: Max connection attempts
            timeout: Timeout per attempt
            
        Returns:
            Connected socket or None
        """

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)

        for _ in range(attempt_lim):
            try:
                sock.connect((self.dest_ip, self.port))
                logger.info(f"Connected to {self.dest_ip}:{self.port}")
                return sock
            except socket.timeout:
                continue
            except (ConnectionRefusedError, OSError) as e:
                logger.debug(f"While trying to connect: {e}")

        sock.close()
        return EmptySocket()
    
    def _host(self, listen_lim, timeout: float) -> socket.socket | EmptySocket:
        """Listen for peer connection.
        
        Args:
            listen_lim: Max time to listen
            timeout: Accept timeout
            
        Returns:
            Connected socket or None
        """

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(timeout)
        server.bind((self.host_ip, self.port))
        server.listen()
        logger.debug("Listening...")

        t_b = time()

        try:
            while time() - t_b < listen_lim:
                try:
                    sock, addr = server.accept()
                    ip, port = addr

                    if ip != self.dest_ip:
                        sock.close()
                        logger.debug(f"Rejected {ip}:{port}")
                        self.rejected.append(addr)
                        continue

                    logger.info(f"Peer connected ({self.dest_ip}:{self.port})")
                    return sock
                except socket.timeout:
                    continue
            return EmptySocket()
        
        finally:
            server.close()
    
    def get_client(self) -> socket.socket:
        """Get established client socket.
        
        Returns:
            Connected socket
        """

        if isinstance(self.client, EmptySocket):
            raise ValueError("Connection must be established first")
        return self.client