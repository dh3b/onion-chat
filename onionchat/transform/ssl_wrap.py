import ssl
from socket import socket
from onionchat.utils.types import EmptySocket
from onionchat.core.transform_core import TransformCore
from onionchat.core.conn_core import ConnectionCore

class SSLWrap(TransformCore):
    """SSL/TLS wrapping transform
    
    Args:
        conn (ConnectionCore): ConnectionCore instance to wrap with SSL
    """

    def __init__(self, conn: ConnectionCore) -> None:
        super().__init__(conn)

    def transform(self) -> ConnectionCore:
        if not isinstance(self._layer, ConnectionCore):
            raise TypeError("SSLWrap transform requires a ConnectionCore layer.")
        return self._layer
        # todo
    