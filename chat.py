import logging
from argparse import ArgumentParser
from onionchat.utils import constants
from onionchat.chat_pipeline import PipelineInit

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=constants.logging_format
)
    
def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="OnionChat Command Line Interface"
    )

    parser.add_argument(
        "dest_ip",
        type=str,
        help="Destination IPv4 address to connect to"
    )

    parser.add_argument(
        "--conn",
        type=str,
        default="onionchat.conn.p2p:PeerConnection",
        help="Connection class path (module:Class)."
    )

    parser.add_argument(
        "--core",
        type=str,
        default="onionchat.chat.generic_chat:GenericChat",
        help="Core class path (module:Class)."
    )

    parser.add_argument(
        "--handler",
        type=str,
        default="onionchat.handler.cedit_cli:CEditCLI",
        help="Handler class path (module:Class)."
    )

    return parser
    
def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    pline = PipelineInit(conn_path=args.conn, core_path=args.core, handler_path=args.handler)
    try:
        conn, core, handler = pline.build(args.dest_ip)
    except Exception as e:
        logging.critical(f"Could not establish P2P connection or instantiate components: {e}")
        return

    handler.open()

if __name__ == '__main__':
    main()