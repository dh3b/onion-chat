from typing import Dict, Any, List
import importlib
import inspect
import logging
from onionchat.config import CONNS, CHATS, HANDLERS, TRANSFORMS
from onionchat.core.chat_core import ChatCore
from onionchat.core.handler_core import HandlerCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.utils.funcs import load_class

logger = logging.getLogger(__name__)

class PipelineBuilder:
    """Prepare connection, 3 layer chat pipeline"""

    def __init__(
        self,
        conn: str = "p2p",
        chat: str = "generic",
        handler: str = "cedit_cli",
        transforms: List[str] | None = None,
        args: Dict[str, Any] | None = None
    ) -> None:
        try:
            self.conn_path = CONNS[conn]
            self.chat_path = CHATS[chat]
            self.handler_path = HANDLERS[handler]
            self.transform_paths = [TRANSFORMS[t] for t in transforms] if transforms else []
        except KeyError as e:
            logger.critical(f"Invalid pipeline component alias: {e}")
            raise ValueError(f"Invalid pipeline component alias: {e}")
        self.args = args or {}        

    def build(self) -> HandlerCore:
        # Load transforms
        transforms = []
        for transform_path in self.transform_paths or []:
            transforms.append(self._instantiate_class(load_class(transform_path)))

        # Layer 1: Connection
        conn = self._instantiate_class(load_class(self.conn_path))
        # estabilish connection require extra kwargs
        sig = inspect.signature(conn.est_connection)
        valid_args = {k: v for k, v in self.args.items() if k in sig.parameters}
        conn.est_connection(**valid_args)
        try:
            conn_socket = conn.get_client()
            self.args["sock"] = conn_socket
        except ValueError:
            logger.critical("Failed to establish connection")
            raise ConnectionError("Failed to establish connection")

        # Layer 2: Chat
        chat = self._instantiate_class(load_class(self.chat_path))
        self.args["chat"] = chat

        # Layer 3: Handler
        handler = self._instantiate_class(load_class(self.handler_path))

        return handler
    
    def _instantiate_class(self, cls):
        sig = inspect.signature(cls.__init__)
        valid_args = {k: v for k, v in self.args.items() if k in sig.parameters}
        return cls(**valid_args)