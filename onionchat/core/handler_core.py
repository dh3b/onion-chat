from abc import ABC, abstractmethod
from onionchat.core.chat_core import ChatCore

class HandlerCore(ABC):
    """Core chat UI / handler. (Virtual class)
    
    Args:
        chat (ChatCore): ChatCore instance to handle
    """

    def __init__(self, chat: ChatCore) -> None:
        self.chat = chat

    @abstractmethod
    def open(self) -> None:
        """Start the UI / handler loop."""