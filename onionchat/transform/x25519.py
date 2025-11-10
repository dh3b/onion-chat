from onionchat.core.transform_core import TransformCore
from onionchat.core.conn_core import ConnectionCore
from onionchat.utils.enc_socket import EncryptedSocket

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes, serialization

class X25519Transform(TransformCore):
    """Ephemeral key exchange (X25519)
    
    Args:
        layer (ConnectionCore): The connection layer to transform.
    """

    def __init__(self, layer: ConnectionCore) -> None:
        super().__init__(layer)

    @staticmethod
    def get_layer() -> type[ConnectionCore]:
        return ConnectionCore

    def transform(self) -> ConnectionCore:
        try:
            sock = self._layer.get_client()
        except ValueError as e:
            raise ValueError("Connection not established before X25519 transform") from e

        # generate ephemeral keypair
        priv = X25519PrivateKey.generate()
        pub = priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )  # 32 bytes

        try:
            sock.sendall(pub)
        except Exception as e:
            raise ConnectionError(f"Failed to send public key: {e}")

        # helper to recv exact length (propagates socket.timeout)
        def recv_exact(n: int) -> bytes:
            parts = []
            remaining = n
            while remaining > 0:
                chunk = sock.recv(remaining)
                if not chunk:
                    return b""
                parts.append(chunk)
                remaining -= len(chunk)
            return b"".join(parts)

        peer_pub = recv_exact(32)
        if not peer_pub or len(peer_pub) != 32:
            raise ConnectionError("Failed to receive peer public key")

        try:
            peer_pub_obj = X25519PublicKey.from_public_bytes(peer_pub)
            shared = priv.exchange(peer_pub_obj)  # 32 bytes shared secret
        except Exception as e:
            raise ConnectionError(f"X25519 exchange failed: {e}")

        # derive two 32-byte keys (send / recv) deterministically
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=64,
            salt=None,
            info=b"onionchat x25519 handshake"
        )
        key_material = hkdf.derive(shared)
        key_a = key_material[:32]
        key_b = key_material[32:]

        if pub > peer_pub:
            send_key, recv_key = key_a, key_b
        else:
            send_key, recv_key = key_b, key_a

        enc_sock = EncryptedSocket(sock, send_key, recv_key)
        try:
            self._layer.client = enc_sock  # type: ignore
        except Exception:
            pass

        return self._layer