import importlib
import logging
import inspect
from inspect import Parameter
from typing import Tuple, Any
from onionchat.core.chat_core import ChatCore
from onionchat.core.handler_core import HandlerCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.utils.types import EmptySocket

logger = logging.getLogger(__name__)

class PipelineInit:
    """Prepare connection, 3 layer chat pipeline"""

    def __init__(
        self,
        conn_path: str = "onionchat.conn.p2p:PeerConnection",
        core_path: str = "onionchat.chat.generic_chat:GenericChat",
        handler_path: str = "onionchat.handler.cedit_cli:CEditCLI",
        port: int = 49152,
        encoding: str = "utf-8",
        recv_timeout: float = 1.0,
        transforms: list[tuple[str, dict]] | None = None,
    ) -> None:
        self.conn_path = conn_path
        self.core_path = core_path
        self.handler_path = handler_path
        self.port = port
        self.encoding = encoding
        self.recv_timeout = recv_timeout
        # transforms: list of (class_path, kwargs_dict)
        self.transforms = transforms or []

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

    def _call_transform(self, transform_instance, kwargs: dict):
        """Call transform_instance.transform with only supported kwargs."""
        tm = transform_instance.transform
        sig = inspect.signature(tm)
        params = sig.parameters
        # If transform accepts **kwargs, pass everything
        if any(p.kind == Parameter.VAR_KEYWORD for p in params.values()):
            filtered = kwargs
        else:
            filtered = {k: v for k, v in kwargs.items() if k in params}
        return tm(**filtered)
    
    def _run_if_transform(self, layer: ConnectionCore | ChatCore | HandlerCore | None) -> ConnectionCore | ChatCore | HandlerCore | None:
        """Run configured transforms against `layer` and return the (possibly) transformed layer."""
        for t in self.transforms:
            try:
                t_path, t_kwargs = t
            except Exception:
                raise ValueError("Transforms must be list of (class_path, kwargs_dict) tuples")
            TCls = self._load_class(t_path)
            t_inst = TCls(layer)
            if not t_inst.check_tf_type(layer):
                continue

            try:
                res = self._call_transform(t_inst, t_kwargs)
            except TypeError:
                # fallback to no-arg call
                res = t_inst.transform()

            # If a transform returns None, keep the previous layer
            if res is not None:
                layer = res

        return layer

    def build(
        self,
        dest_ip: str,
        con_attempt_lim: int = 5,
        con_timeout: float = 5.0,
        host_timeout: float = 1.0,
        host_listen_lim: float = 60.0,
    ) -> Tuple[ConnectionCore, ChatCore, HandlerCore]:
        """Init chat"""

        self._run_if_transform(None)
        
        # Load classes
        ConnCls = self._load_class(self.conn_path)
        CoreCls = self._load_class(self.core_path)
        HandlerCls = self._load_class(self.handler_path)

        # Build connection
        conn = ConnCls(dest_ip, port=self.port)
        try:
            conn.est_connection(con_attempt_lim, con_timeout, host_timeout, host_listen_lim)
        except TypeError:
            conn.est_connection()

        conn = self._run_if_transform(conn)
        if not isinstance(conn, ConnectionCore):
            raise RuntimeError("Connection transform did not return a ConnectionCore instance")
        client_sock = conn.get_client()

        # Build core
        core = None
        try:
            core = CoreCls(client_sock, encoding=self.encoding, recv_timeout=self.recv_timeout)
        except TypeError:
            core = CoreCls(client_sock)

        core = self._run_if_transform(core)
        if not isinstance(core, ChatCore):
            raise RuntimeError("Chat transform did not return a ChatCore instance")

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
        
        self._run_if_transform(handler)
        if not isinstance(handler, HandlerCore):
            raise RuntimeError("Handler transform did not return a HandlerCore instance")

        return conn, core, handler