import ssl
import logging
from socket import socket
from onionchat.utils.types import EmptySocket
from onionchat.core.plugin_core import PluginCore
from onionchat.core.conn_core import ConnectionCore

logger = logging.getLogger(__name__)

class SSLWrap(PluginCore):
    """SSL/TLS wrapping plugin

    Args:
        layer (ConnectionCore): ConnectionCore instance to wrap with SSL
    """

    def __init__(self, layer: ConnectionCore) -> None:
        super().__init__(layer)

    @staticmethod
    def get_layer() -> type[ConnectionCore]:
        return ConnectionCore

    def transform(self) -> ConnectionCore:
        return self._layer
        # todo
    