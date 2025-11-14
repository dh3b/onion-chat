from __future__ import annotations
from typing import Iterable, List
import importlib, json
from pathlib import Path
from socket import socket
from cryptography.hazmat.primitives import hashes
import onionchat.config as cfg

def _class_file(cls: type) -> Path:
    mod = importlib.import_module(cls.__module__)
    path = getattr(mod, "__file__", None)
    if not path:
        raise ValueError(f"No file for module {mod.__name__}")
    return Path(path).resolve()

def _sha256(data: bytes) -> bytes:
    h = hashes.Hash(hashes.SHA256())
    h.update(data)
    return h.finalize()

def digest_for_classes(classes: Iterable[type]) -> bytes:
    """Canonical digest of module files hosting the given classes."""
    entries = []
    for cls in classes:
        path = _class_file(cls)
        with open(path, "rb") as f:
            file_bytes = f.read()
        file_hash = _sha256(file_bytes).hex()
        entries.append({"module": cls.__module__, "class": cls.__name__, "path": str(path), "sha256": file_hash})
    entries.sort(key=lambda e: (e["module"], e["class"]))
    payload = json.dumps(entries, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _sha256(payload)

def select_classes_for_level(
    conn_cls: type, chat_cls: type, handler_cls: type, plugins_cls: List[type], level: str
) -> List[type]:
    if level == "broad":
        return [conn_cls]
    if level == "secure":
        wire_plugins = [p for p in plugins_cls if getattr(p, "wire_affecting", False)]
        return [conn_cls, chat_cls, *wire_plugins]
    # strict
    return [conn_cls, chat_cls, handler_cls, *plugins_cls]

def exchange_and_match(sock: socket, local_digest: bytes) -> bool:
    """Simple symmetric exchange: both sides send 32 bytes, then read 32 bytes, then compare."""
    if not local_digest or len(local_digest) != 32:
        raise ValueError("digest must be 32 bytes (SHA-256)")

    # send
    sock.sendall(local_digest)
    # recv
    peer = _recv_exact(sock, 32)
    return peer == local_digest

def _recv_exact(sock: socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return b""
        buf += chunk
    return buf