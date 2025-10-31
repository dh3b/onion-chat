import logging
from typing import Tuple
from argparse import ArgumentParser
import onionchat.config as cfg
from onionchat.pipeline_builder import PipelineBuilder
from onionchat.utils.funcs import load_class

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format=cfg.logging_format
)

def cls_help_pair(alias: str) -> Tuple[str, str]:
    cls = {**cfg.CONNS, **cfg.CHATS, **cfg.HANDLERS, **cfg.TRANSFORMS}
    path = cls.get(alias)
    if not path:
        return (alias, "Unknown class alias")

    return (alias, load_class(path).__doc__ or "No documentation available")

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="OnionChat, secure comms CLI"
    )

    parser.add_argument(
        "dest_ip",
        type=str,
        help="Destination IPv4 address to connect to"
    )

    parser.add_argument(
        "conn",
        type=str,
        nargs="?",
        default="p2p",
        help=f"Connection type: {[{cls_help_pair(k)} for k in cfg.CONNS.keys()]}"
    )

    parser.add_argument(
        "chat",
        type=str,
        nargs="?",
        default="generic",
        help=f"Chat type: {[{cls_help_pair(k)} for k in cfg.CHATS.keys()]}"
    )

    parser.add_argument(
        "handler",
        type=str,
        nargs="?",
        default="cedit_cli",
        help=f"Handler type: {[{cls_help_pair(k)} for k in cfg.HANDLERS.keys()]}"
    )

    parser.add_argument(
        "--transforms",
        type=str,
        nargs="*",
        default=[],
        help=f"Transforms to apply: {[{cls_help_pair(k)} for k in cfg.TRANSFORMS.keys()]}"
    )

    return parser
    
def main() -> None:
    parser = build_parser()
    args, unknown = parser.parse_known_args()

    custom_args = {}
    for i in range(0, len(unknown), 2):
        if unknown[i].startswith("--"):
            key = unknown[i][2:]
            value = unknown[i + 1] if (i + 1) < len(unknown) else True
            custom_args[key] = value

    custom_args["dest_ip"] = args.dest_ip
    pline = PipelineBuilder(args.conn, args.chat, args.handler, args.transforms, custom_args)
    handler = pline.build()
    handler.open()

if __name__ == '__main__':
    main()