from abc import ABC, abstractmethod
from typing import Any
from onionchat.core.chat_core import ChatCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.handler_core import HandlerCore

class TransformCore(ABC):
    """Core transform interface. (Virtual class)
    
    Args:
        layer (ConnectionCore | ChatCore | HandlerCore | None): The layer type a transform applies to
    """

    def __init__(self, layer: ConnectionCore | ChatCore | HandlerCore | None ) -> None:
        self._layer = layer
        if isinstance(layer, ConnectionCore):
            self._n_layer = 1
        elif isinstance(layer, ChatCore):
            self._n_layer = 2
        elif isinstance(layer, HandlerCore):
            self._n_layer = 3
        else:
            self._n_layer = 0

    def check_tf_type(self, layer: ConnectionCore | ChatCore | HandlerCore | None) -> bool:
        """Check if the transform is applied to the correct layer type."""
        if self.n_layer == 1 and isinstance(layer, ConnectionCore):
            return True
        elif self.n_layer == 2 and isinstance(layer, ChatCore):
            return True
        elif self.n_layer == 3 and isinstance(layer, HandlerCore):
            return True
        elif self.n_layer == 0 and layer is None:
            return True
        return False
    
    @property
    def n_layer(self) -> int:
        """Return the layer number this transform takes place after."""
        return self._n_layer
    
    @abstractmethod
    def transform(self, *args, **kwargs) -> ConnectionCore | ChatCore | HandlerCore | None:
        """Transform data going through the layer."""
    
