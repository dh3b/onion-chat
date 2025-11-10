from abc import ABC, abstractmethod
from typing import Any, Type, Generic
from onionchat.utils.types import CoreT
from onionchat.core.chat_core import ChatCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.handler_core import HandlerCore

class TransformCore(Generic[CoreT], ABC):
    """Core transform interface. (Virtual class)
    
    Args:
        layer (CoreT): The layer type a transform applies to
    """

    def __init__(self, layer: CoreT) -> None:
        self._layer: CoreT = layer

    @staticmethod
    @abstractmethod
    def get_layer() -> type[CoreT]:
        """Return the layer type this transform applies to."""
        ...
    
    @abstractmethod
    def transform(self, *args, **kwargs) -> CoreT:
        """Transform data going through the layer."""
        ...
