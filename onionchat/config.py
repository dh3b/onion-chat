import logging
from typing import Optional, Literal
from onionchat.components import CONNS, CHATS, HANDLERS, PLUGINS

# logging
logging_format: str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging_level = logging.INFO

# default pipeline components
default_conn: str = "p2p"
default_chat: str = "generic"
default_handler: str = "cedit_cli"
default_plugins: list[str] = []

# networking
port: int = 49152
con_attempt_lim: int = 5
con_timeout: float = 5.0
host_timeout: float = 1.0
host_listen_lim: float = 60.0

# chat settings
encoding: str = "utf-8"
recv_timeout: float = 1.0
payload_flags: str = ""

# framing/buffers
recv_buf: int = 1024
frame_len_bytes: int = 4
byteorder: Literal['little', 'big'] = "big"

# encrypted socket
enc_recv_buf: int = 4096

# handlers
input_sym: str = ">"
cedit_timestamps: bool = True
cedit_max_display_size: int = 1024
cedit_max_input_size: int = 256

# save_history plugin
log_file_path: Optional[str] = None
reset_history: bool = False
log_dir_name: str = ".onionchat_logs"
log_file_prefix: str = "chat_log_"
log_file_ext: str = ".txt"

# misc
unknown_client: str = "unknown"

# module signing
# note: this can't be set using the ui
module_sign_level: Literal['strict', 'secure', 'broad'] = "secure"
# PEM-encoded Ed25519 public keys of trusted signers (optional; empty -> skip signature auth)
trusted_signing_pubkeys: list[str] = []