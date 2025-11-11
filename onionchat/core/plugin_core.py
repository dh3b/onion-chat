from abc import ABC, abstractmethod
from typing import Any, Type, Generic
from onionchat.utils.types import CoreT
from onionchat.core.chat_core import ChatCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.handler_core import HandlerCore

class PluginCore(Generic[CoreT], ABC):
    """Core plugin interface. (Virtual class)
    
    Args:
        layer (CoreT): The layer type a plugin applies to
    """

    def __init__(self, layer: CoreT) -> None:
        self._layer: CoreT = layer

    @staticmethod
    @abstractmethod
    def get_layer() -> type[CoreT]:
        """Return the layer type this plugin applies to."""
        ...
    
    @abstractmethod
    def transform(self, *args, **kwargs) -> CoreT:
        """Transform the layer and return the modified layer instance."""
        ...
