from typing import Dict, Any, List
import logging
import onionchat.config as cfg
from onionchat.utils.types import CoreT
from onionchat.core.chat_core import ChatCore
from onionchat.core.handler_core import HandlerCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.core.plugin_core import PluginCore
from onionchat.utils.funcs import load_class
from onionchat.utils import module_sign as ms

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
        conn: str = cfg.default_conn,
        chat: str = cfg.default_chat,
        handler: str = cfg.default_handler,
        plugins: List[str] | None = cfg.default_plugins,
        args: Dict[str, Any] | None = None
    ) -> None:
        try:
            self.conn_alias = conn
            self.chat_alias = chat
            self.handler_alias = handler
            self.plugins_aliases = plugins or []

            self.conn_cls = load_class(cfg.CONNS[conn])
            self.chat_cls = load_class(cfg.CHATS[chat])
            self.handler_cls = load_class(cfg.HANDLERS[handler])
            self.plugins_cls = [load_class(cfg.PLUGINS[p]) for p in plugins] if plugins else []
        except KeyError as e:
            logger.critical(f"Invalid pipeline component alias: {e}")
            raise ValueError(f"Invalid pipeline component alias: {e}")
        self.args = args or {}

    def build(self) -> HandlerCore:
        # Layer 1: Connection
        conn = PipelineBuilder.instantiate_class(self.conn_cls, self.args)
        conn.est_connection(**PipelineBuilder.validate_args(conn.est_connection, self.args))

        level = getattr(cfg, "module_sign_level")
        if level != "broad":
            classes = ms.select_classes_for_level(self.conn_cls, self.chat_cls, self.handler_cls, self.plugins_cls, level)

            # map classes to user-provided aliases for readability
            alias_by_cls = {
                self.conn_cls: self.conn_alias,
                self.chat_cls: self.chat_alias,
                self.handler_cls: self.handler_alias,
            }
            for cls, alias in zip(self.plugins_cls, self.plugins_aliases):
                alias_by_cls[cls] = alias

            manifest = ms.manifest_for_classes(classes, alias_by_cls)
            mbytes = ms.serialize_manifest(manifest)
            ldigest = ms.digest_for_manifest_bytes(mbytes)

            try:
                peer_manifest = ms.exchange_manifest(conn.get_client(), mbytes)
            except Exception as e:
                logger.error(f"Module-sign manifest exchange failed: {e}")
                raise

            pdigest = ms.digest_for_manifest_bytes(ms.serialize_manifest(peer_manifest)) if peer_manifest else b""
            if not peer_manifest or pdigest != ldigest:
                logger.error("Peer module set mismatch")
                logger.info(f"Local: {ms.summarize_manifest(manifest)}")
                logger.info(f"Peer:  {ms.summarize_manifest(peer_manifest)}")
                raise ConnectionError("Peer module set mismatch")

            logger.info(f"Module set match: {ms.summarize_manifest(manifest)}")

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
        return {k: v for k, v in args.items() if k in sig.parameters} if (sig := inspect.signature(func)) else {}

    @staticmethod
    def instantiate_class(cls, args: Dict):
        return cls(**PipelineBuilder.validate_args(cls.__init__, args))