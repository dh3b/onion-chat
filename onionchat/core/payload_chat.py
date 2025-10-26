from onionchat.core.chat_core import ChatCore
import socket

class PayloadChatCore(ChatCore):
    
    def __init__(self, sock: socket.socket) -> None:
        super().__init__(sock)