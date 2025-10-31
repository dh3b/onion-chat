from onionchat.core.conn_core import ConnectionCore
from onionchat.core.chat_core import ChatCore
from onionchat.core.handler_core import HandlerCore

logging_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

CoreT = ConnectionCore | ChatCore | HandlerCore

CONNS = {
    "p2p": "onionchat.conn.p2p:PeerConnection"
}

CHATS = {
    "generic": "onionchat.chat.generic_chat:GenericChat",
    "payload": "onionchat.chat.payload_chat:PayloadChat"
}

HANDLERS = {
    "generic_cli": "onionchat.handler.generic_cli:GenericCLIHandler",
    "cedit_cli": "onionchat.handler.cedit_cli:CEditCLI"
}

TRANSFORMS = {
    "ssl": "onionchat.transform.ssl_wrap:SSLWrap"
}

# help(generic_chat.GenericChat)