import socket
import threading
import onionchat.config as cfg
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

class EncryptedSocket:
    """
    Small socket-like wrapper presenting key socket methods:

    Args:
        raw_sock: underlying connected socket.socket
        send_key: 32-byte key for encrypting outgoing messages
        recv_key: 32-byte key for decrypting incoming messages

    Methods:
        sendall(bytes)
        recv(bufsize) -> bytes (returns full decrypted message frame)
        settimeout, getpeername, getsockname, close
    """
    def __init__(self, raw_sock: socket.socket, send_key: bytes, recv_key: bytes):
        self._sock = raw_sock
        self._send_aead = ChaCha20Poly1305(send_key)
        self._recv_aead = ChaCha20Poly1305(recv_key)
        self._send_counter = 0
        self._recv_counter = 0
        self._lock = threading.Lock()

    # framing helpers
    def _nonce_from_counter(self, counter: int) -> bytes:
        # 12 bytes nonce: 4 zero bytes + 8-byte big-endian counter
        return b"\x00\x00\x00\x00" + counter.to_bytes(8, "big")

    def _recv_exact(self, n: int) -> bytes:
        parts = []
        remaining = n
        while remaining > 0:
            chunk = self._sock.recv(remaining)
            if not chunk:
                # connection closed
                return b""
            parts.append(chunk)
            remaining -= len(chunk)
        return b"".join(parts)
    
    def sendall(self, data: bytes):
        """Encrypt 'data' and send as: 4-byte len + ciphertext"""

        with self._lock:
            nonce = self._nonce_from_counter(self._send_counter)
            self._send_counter += 1
        ct = self._send_aead.encrypt(nonce, data, None)
        length = len(ct).to_bytes(4, "big")
        self._sock.sendall(length + ct)

    def recv(self, bufsize: int = cfg.enc_recv_buf) -> bytes:
        """Read a full framed ciphertext message, decrypt and return plaintext bytes."""

        # read 4-byte length
        length_data = self._recv_exact(4)
        if not length_data:
            return b""
        length = int.from_bytes(length_data, "big")
        if length <= 0:
            return b""
        ct = self._recv_exact(length)
        if not ct:
            return b""
        with self._lock:
            nonce = self._nonce_from_counter(self._recv_counter)
            self._recv_counter += 1
        try:
            pt = self._recv_aead.decrypt(nonce, ct, None)
            return pt
        except Exception:
            # authentication failed or other error -> treat as closed
            return b""
        
    def __getattr__(self, name):
        return getattr(self._sock, name)