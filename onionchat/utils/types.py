from typing import TypeVar, TYPE_CHECKING

class TerminateConnection: pass
class EmptyMessage: pass
class EmptySocket: pass
class EmptyConnection: pass

if TYPE_CHECKING:
    from onionchat.core.conn_core import ConnectionCore
    from onionchat.core.chat_core import ChatCore
    from onionchat.core.handler_core import HandlerCore

CoreT = TypeVar("CoreT", "ConnectionCore", "ChatCore", "HandlerCore")