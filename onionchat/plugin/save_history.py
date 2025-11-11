import pathlib
import logging
from onionchat.core.plugin_core import PluginCore
from onionchat.core.handler_core import HandlerCore

logger = logging.getLogger(__name__)

class SaveHistory(PluginCore):
    """Chat history saving plugin

    Args:
        layer (HandlerCore): Handler instance to save history for

    Transform args:
        log_file_path (str): Log file path, defaults to .onionchat_logs, named after a timestamp
        reset_history (bool): Whether to reset history on load
    """

    def __init__(self, layer: HandlerCore) -> None:
        super().__init__(layer)
        self.path = None
        self.reset_history = False
        self.encoding = self._layer.chat.encoding

    @staticmethod
    def get_layer() -> type[HandlerCore]:
        return HandlerCore
    
    def transform(self, log_file_path: str | None = None, reset_history: bool = False) -> HandlerCore:
        self.reset_history = reset_history
        if not log_file_path:
            try:
                self.path = pathlib.Path.home() / ".onionchat_logs" / f"chat_log_{self._layer.client_pref}.txt"
                self.path.parent.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                logger.error(f"Cannot create log file in home directory: {e}")
                return self._layer
        else:
            try:
                self.path = pathlib.Path(log_file_path).expanduser().resolve()
            except (ValueError, OSError) as e:
                logger.error(f"Invalid log file path: {e}")
                return self._layer
            
        self.orig_open = self._layer.open
        self._layer.open = self.open_wrapper
        return self._layer
            
    def open_wrapper(self) -> None:
        if not self.path:
            logger.error("Log file path not set. Cannot save chat history.")
            raise RuntimeError("Log file path not set. Cannot save chat history.")

        # Load history
        if not self.reset_history:
            try:
                if self.path.exists():
                    with open(self.path, "r", encoding=self.encoding) as log_file:
                        for line in log_file:
                            self._layer.history.append(line.rstrip("\n"))
            except (IOError, OSError, UnicodeDecodeError) as e:
                logger.error(f"Failed to load chat history: {e}")

        # Start the handler loop
        self.orig_open()

        # Save history
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding=self.encoding) as log_file:
                for msg in self._layer.history:
                    log_file.write(msg + "\n")
        except (IOError, OSError, UnicodeEncodeError) as e:
            logger.error(f"Failed to save chat history: {e}")

    def open(self) -> None:
        raise NotImplementedError("Use the wrapped layer.open instead.")