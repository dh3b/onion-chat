from typing import Dict, Any, List
import logging
from onionchat.config import CONNS, CHATS, HANDLERS, PLUGINS
from onionchat.utils.types import CoreT
from onionchat.core.chat_core import ChatCore
from onionchat.core.handler_core import HandlerCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.plugin_core import PluginCore
from onionchat.utils.funcs import load_class

logger = logging.getLogger(__name__)

class PipelineBuilder:
    """Prepare connection, 3 layer chat pipeline
    
    Args:
        conn (str): Connection type alias
        chat (str): Chat type alias
        handler (str): Handler type alias
        plugins (List[str] | None): List of plugin type aliases
        args (Dict[str, Any] | None): Additional arguments to pass to components

    Returns:
        HandlerCore: Fully built chat handler instance
    """

    def __init__(
        self,
        conn: str = "p2p",
        chat: str = "generic",
        handler: str = "cedit_cli",
        plugins: List[str] | None = None,
        args: Dict[str, Any] | None = None
    ) -> None:
        try:
            self.conn_cls = load_class(CONNS[conn])
            self.chat_cls = load_class(CHATS[chat])
            self.handler_cls = load_class(HANDLERS[handler])
            self.plugins_cls = [load_class(PLUGINS[p]) for p in plugins] if plugins else []
        except KeyError as e:
            logger.critical(f"Invalid pipeline component alias: {e}")
            raise ValueError(f"Invalid pipeline component alias: {e}")
        self.args = args or {}        

    def build(self) -> HandlerCore:
        # Layer 1: Connection
        conn = PipelineBuilder.instantiate_class(self.conn_cls, self.args)
        # estabilish connection require extra kwargs
        conn.est_connection(**PipelineBuilder.validate_args(conn.est_connection, self.args))
        conn = self._apply_plugins(conn, self.plugins_cls)
        assert isinstance(conn, ConnectionCore)
        try:
            conn_socket = conn.get_client()
            self.args["sock"] = conn_socket
        except ValueError:
            logger.critical("Failed to establish connection")
            raise ConnectionError("Failed to establish connection")

        # Layer 2: Chat
        chat = PipelineBuilder.instantiate_class(self.chat_cls, self.args)
        chat = self._apply_plugins(chat, self.plugins_cls)
        assert isinstance(chat, ChatCore)
        self.args["chat"] = chat

        # Layer 3: Handler
        handler = PipelineBuilder.instantiate_class(self.handler_cls, self.args)
        handler = self._apply_plugins(handler, self.plugins_cls)
        assert isinstance(handler, HandlerCore)

        return handler

    def _apply_plugins(self, layer: CoreT, plugins_cls: List[type[PluginCore]]) -> CoreT:
        for plugin_cls in plugins_cls:
            if not isinstance(layer, plugin_cls.get_layer()):
                continue
            t = PipelineBuilder.instantiate_class(plugin_cls, {"layer": layer})
            try:
                layer = t.transform(**PipelineBuilder.validate_args(t.transform, self.args))
            except Exception as e:
                logger.error(f"Error applying plugin {plugin_cls.__name__}: {e}")
                raise
        return layer    

    @staticmethod
    def validate_args(func, args: Dict) -> Dict:
            """Filter a dict to only include keys that are valid arguments for a function."""
            import inspect

            sig = inspect.signature(func)
            return {k: v for k, v in args.items() if k in sig.parameters}

    @staticmethod
    def instantiate_class(cls, args: Dict): # type: ignore (cls means any class here)
            return cls(**PipelineBuilder.validate_args(cls.__init__, args))