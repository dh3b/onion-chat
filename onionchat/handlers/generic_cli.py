import threading
import socket
import logging
from onionchat.utils.typing_classes import *
from onionchat.core.generic_chat import GenericChatCore

logger = logging.getLogger(__name__)

class GenericCLIHandler(GenericChatCore):
    """CLI chat interface."""

    def __init__(self, sock: socket.socket | EmptySocket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        if isinstance(sock, EmptySocket):
            logger.critical("Provided socket has not estabilished conenction")
            raise RuntimeError("Provided socket has not estabilished conenction")
        super().__init__(sock, encoding, recv_timeout)
        self.client_pref = str(sock.getpeername()[0])
        self.running = False
    
    def open(self) -> None:
        """Start chat session."""
        self.running = True
        self._handle_ui()
    
    def _handle_ui(self) -> None:
        t_in = threading.Thread(target=self._in_thread)
        t_out = threading.Thread(target=self._out_thread)

        logger.debug("Started input thread")
        t_in.start()

        logger.debug("Started ouput thread")
        t_out.start()

        t_in.join()
        t_out.join()
        
        self.sock.close()

    def _in_thread(self) -> None:
        while self.running:
            msg = input("> ").strip()

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
                logger.info("\nConnection lost")
                self.running = False
                break

    def _out_thread(self) -> None:
        while self.running:
            msg = super().recv_msg()
            
            if isinstance(msg, EmptyMessage):
                continue
            
            if isinstance(msg, TerminateConnection) or msg.strip() == "__exit__":
                logger.info("\nPeer disconnected")
                self.running = False
                break

            print(f"\n{self.client_pref}:{msg}\n> ", end="", flush=True)