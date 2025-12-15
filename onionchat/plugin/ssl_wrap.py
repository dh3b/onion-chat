import ssl
import logging
import socket
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

    wire_affecting: bool = True

    @staticmethod
    def get_layer() -> type[ConnectionCore]:
        return ConnectionCore

    def transform(
            self,
            cafile: str | None = None,
            capath: str | None = None,
            certfile: str | None = None,
            keyfile: str | None = None,
        ) -> ConnectionCore:

        sock = self._layer.get_client()

        if self._layer.is_host:
            
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            
        else:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        if certfile:
            ctx.load_cert_chain(certfile, keyfile)
        if cafile or capath:
            ctx.load_verify_locations(cafile=cafile, capath=capath)
        ctx.verify_mode = ssl.CERT_REQUIRED

        try:
            wrapped = ctx.wrap_socket(
                sock,
                server_side=self._layer.is_host,
                server_hostname=self._layer.dest_ip if not self._layer.is_host else None,
            )
        except Exception as e:
            logger.exception("TLS wrap/handshake failed")
            raise

        self._layer.client = wrapped
        return self._layer
