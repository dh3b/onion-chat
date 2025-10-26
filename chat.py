import importlib
import logging
from argparse import ArgumentParser
from typing import Tuple, Any
from onionchat.core.chat_core import ChatCore
from onionchat.handler.handler_core import HandlerCore
from onionchat.conn.conn_core import ConnectionCore
from onionchat.utils import constants

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=constants.logging_format
)

class PipelineInit:
    """Prepare connection, 3 layer chat pipeline"""

    def __init__(
        self,
        conn_path: str = "onionchat.conn.p2p:PeerConnection",
        core_path: str = "onionchat.core.generic_chat:GenericChatCore",
        handler_path: str = "onionchat.handler.cedit_cli:CEditCLI",
        port: int = 49152,
        encoding: str = "utf-8",
        recv_timeout: float = 1.0,
    ) -> None:
        self.conn_path = conn_path
        self.core_path = core_path
        self.handler_path = handler_path
        self.port = port
        self.encoding = encoding
        self.recv_timeout = recv_timeout

    def _load_class(self, path: str):
        """Load a class from 'module:Class' or 'module.Class' style string."""
        if ":" in path:
            mod_path, cls_name = path.split(":", 1)
        elif "." in path:
            mod_path, cls_name = path.rsplit(".", 1)
        else:
            raise ValueError("Provide full module path, e.g. 'onionchat.conn.p2p:PeerConnection'")

        mod = importlib.import_module(mod_path)
        return getattr(mod, cls_name)

    def build(
        self,
        dest_ip: str,
        con_attempt_lim: int = 5,
        con_timeout: float = 5.0,
        host_timeout: float = 1.0,
        host_listen_lim: float = 60.0,
    ) -> Tuple[ConnectionCore, ChatCore, HandlerCore]:
        """Init chat"""
        
        # Load classes
        ConnCls = self._load_class(self.conn_path)
        CoreCls = self._load_class(self.core_path)
        HandlerCls = self._load_class(self.handler_path)

        conn = ConnCls(dest_ip, port=self.port)
        try:
            conn.est_connection(con_attempt_lim, con_timeout, host_timeout, host_listen_lim)
        except TypeError:
            conn.est_connection()

        client_sock = conn.get_client()

        # Build core
        core = None
        try:
            core = CoreCls(client_sock, encoding=self.encoding, recv_timeout=self.recv_timeout)
        except TypeError:
            core = CoreCls(client_sock)

        # Build handler
        handler = None
        try:
            handler = HandlerCls(core)
        except TypeError:
            # fallback: try passing socket (old-style handlers accept socket)
            try:
                handler = HandlerCls(client_sock)
            except TypeError:
                logger.error("Unable to instantiate handler class with known signatures")
                raise

        return conn, core, handler
    
def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="OnionChat Command Line Interface"
    )

    parser.add_argument(
        "dest_ip",
        type=str,
        help="Destination IPv4 address to connect to"
    )

    parser.add_argument(
        "--conn",
        type=str,
        default="onionchat.conn.p2p:PeerConnection",
        help="Connection class path (module:Class)."
    )

    parser.add_argument(
        "--core",
        type=str,
        default="onionchat.core.generic_chat:GenericChatCore",
        help="Core class path (module:Class)."
    )

    parser.add_argument(
        "--handler",
        type=str,
        default="onionchat.handler.cedit_cli:CEditCLI",
        help="Handler class path (module:Class)."
    )

    return parser
    
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    pline = PipelineInit(conn_path=args.conn, core_path=args.core, handler_path=args.handler)
    try:
        conn, core, handler = pline.build(args.dest_ip)
    except Exception as e:
        logging.critical(f"Could not establish P2P connection or instantiate components: {e}")
        return

    handler.open()

if __name__ == '__main__':
    main()