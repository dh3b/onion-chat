logging_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

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
    "ssl": "onionchat.transform.ssl_wrap:SSLWrap",
    "save_history": "onionchat.transform.save_history:SaveHistory"
}

# help(generic_chat.GenericChat)