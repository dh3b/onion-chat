from abc import ABC, abstractmethod
from typing import Any
from onionchat.config import CoreT
from onionchat.core.chat_core import ChatCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.handler_core import HandlerCore

class TransformCore(ABC):
    """Core transform interface. (Virtual class)
    
    Args:
        layer (CoreT): The layer type a transform applies to
    """

    def __init__(self, layer: CoreT) -> None:
        self._layer = layer

    @staticmethod
    @abstractmethod
    def get_layer() -> type[CoreT]:
        """Return the layer type this transform applies to."""
        pass
    
    @abstractmethod
    def transform(self, *args, **kwargs) -> CoreT:
        """Transform data going through the layer."""
    
