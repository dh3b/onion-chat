import threading
import socket
import logging
from onionchat.utils.types import *
from onionchat.chat.generic_chat import GenericChat
from onionchat.core.chat_core import ChatCore
from onionchat.core.handler_core import HandlerCore

logger = logging.getLogger(__name__)

class GenericCLIHandler(HandlerCore):
    """CLI chat interface.

    Accepts either:
      - a ChatCore instance, or
      - a raw socket.socket (backwards compatible).
    """

    def __init__(self, core_or_sock: ChatCore | socket.socket | EmptySocket, encoding: str = "utf-8", recv_timeout: float = 1.0) -> None:
        # Accept a prepared core
        if isinstance(core_or_sock, ChatCore):
            core = core_or_sock
        else:
            # If socket-like, build a GenericChatCore wrapper (keeps old API)
            if isinstance(core_or_sock, EmptySocket):
                logger.critical("Provided socket has not estabilished conenction")
                raise RuntimeError("Provided socket has not estabilished conenction")
            core = GenericChat(core_or_sock, encoding, recv_timeout)

        super().__init__(core)
        self.client_pref = str(self.core.sock.getpeername()[0])
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
        
        self.core.sock.close()

    def _in_thread(self) -> None:
        while self.running:
            msg = input("> ").strip()

            if not msg:
                continue

            if msg == "exit":
                try:
                    self.core.send_msg("__exit__")
                except:
                    pass
                self.running = False
                break

            try:
                self.core.send_msg(msg)
            except (BrokenPipeError, OSError):
                logger.info("\nConnection lost")
                self.running = False
                break

    def _out_thread(self) -> None:
        while self.running:
            msg = self.core.recv_msg()
            
            if isinstance(msg, EmptyMessage):
                continue
            
            if isinstance(msg, TerminateConnection) or msg.strip() == "__exit__":
                logger.info("\nPeer disconnected")
                self.running = False
                break

            print(f"\n{self.client_pref}:{msg}\n> ", end="", flush=True)