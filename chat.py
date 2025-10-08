import logging
from onionchat.conns.p2p import PeerConnection
from onionchat.handlers.generic_cli import GenericCLIHandler
from onionchat.utils import constants

logging.basicConfig(
    level=logging.INFO,
    format=constants.logging_format
)

if __name__ == '__main__':

    peer_ip = input("Enter peer IP address: ")
    print("Establishing connection...")
    peer_conn = PeerConnection(peer_ip)
    peer_conn.est_connection()
    chat = GenericCLIHandler(peer_conn.get_client())
    chat.open()