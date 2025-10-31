from abc import ABC, abstractmethod
from onionchat.core.chat_core import ChatCore

class HandlerCore(ABC):
    """Abstract handler interface. Handlers drive the UI and use a ChatCore."""

    def __init__(self, chat: ChatCore) -> None:
        self.chat = chat

    @abstractmethod
    def open(self) -> None:
        """Start the UI / handler loop."""