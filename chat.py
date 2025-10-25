import logging
from onionchat.conns.p2p import PeerConnection
from onionchat.handlers.cedit_cli import CEditCLI as CEHandler
from onionchat.utils import constants
from argparse import ArgumentParser

logging.basicConfig(
    level=logging.INFO,
    format=constants.logging_format
)

def main() -> None:
    parser = ArgumentParser(
        description="OnionChat Command Line Interface"
    )

    parser.add_argument(
        "dest_ip",
        type=str,
        help="Destination IPv4 address to connect to"
    )

    args = parser.parse_args()

    peer_conn = PeerConnection(args.dest_ip)
    peer_conn.est_connection()
    try:
        conn = peer_conn.get_client()
    except Exception as e:
        logging.critical(f"Could not establish P2P connection: {e}")
        return

    cli_handler = CEHandler(conn)
    cli_handler.open()

if __name__ == '__main__':
    main()