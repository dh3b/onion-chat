import socket
import threading
import warnings
import time

class TerminateConnection(): pass
class EmptyMessage(): pass
class EmptySocket(): pass

class PeerConnection:
    """P2P connection handler."""

    def __init__(self, dest_ip, port=49152) -> None:
        try:
            socket.inet_aton(dest_ip)
        except socket.error:
            raise ValueError(f"{dest_ip} is not a valid ipv4 address")
        
        self.dest_ip = dest_ip
        self.host_ip = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.rejected = []
        self.client = EmptySocket()

    def est_connection(self, con_attempt_lim: int = 5, con_timeout: float = 5.0, host_timeout: float = 1.0, host_listen_lim: float = 60.0) -> None:
        """Establish connection by connecting or hosting.
        
        Args:
            con_attempt_lim: Max connection attempts
            con_timeout: Timeout per connection attempt
            host_timeout: Timeout for accepting connections
            host_listen_lim: Max time to listen as host
        """

        self.client = self._con(con_attempt_lim, con_timeout)

        if isinstance(self.client, EmptySocket):
            warnings.warn("Failed to connect, setting up host", RuntimeWarning)
            self.client = self._host(host_listen_lim, host_timeout)

        if isinstance(self.client, EmptySocket):
            raise RuntimeError(f"Failed to peer with {self.dest_ip}. Host listen timed out ({host_listen_lim})")

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
                return sock
            except (socket.timeout, ConnectionRefusedError, OSError):
                continue

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

        t_b = time.time()

        try:
            while time.time() - t_b < listen_lim:
                try:
                    sock, addr = server.accept()
                    ip, _ = addr

                    if ip != self.dest_ip:
                        sock.close()
                        self.rejected.append(addr)
                        continue

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

class ChatCore:
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
    
class ChatCLIHandler(ChatCore):
    """CLI chat interface."""

    def __init__(self, sock: socket.socket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        super().__init__(sock, encoding, recv_timeout)
        self.client_pref = str(sock.getpeername()[0])
    
    def open(self) -> None:
        """Start chat session."""

        self.running = True

        t_in = threading.Thread(target=self._in_thread)
        t_out = threading.Thread(target=self._out_thread)
        t_in.start()
        t_out.start()
        t_in.join()
        t_out.join()
        
        self.sock.close()

    def _in_thread(self) -> None:
        while self.running:
            msg = input("> ")

            if not msg:
                continue

            if msg == "exit":
                try:
                    super().send_msg("__exit__")
                except:
                    pass
                self.running = False
                break

            try:
                super().send_msg(msg)
            except (BrokenPipeError, OSError):
                print("\nConnection lost")
                self.running = False
                break

    def _out_thread(self) -> None:
        while self.running:
            msg = super().recv_msg()
            
            if isinstance(msg, EmptyMessage):
                continue
            
            if isinstance(msg, TerminateConnection) or msg.strip() == "__exit__":
                print("\nPeer disconnected")
                self.running = False
                break

            print(f"\n{self.client_pref}:{msg}\n> ", end="", flush=True)


if __name__ == '__main__':
    peer_ip = input("Enter peer IP address: ")
    print("Establishing connection...")
    peer_conn = PeerConnection(peer_ip)
    peer_conn.est_connection()
    chat = ChatCLIHandler(peer_conn.get_client())
    chat.open()