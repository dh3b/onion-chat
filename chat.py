import logging
from typing import Tuple
from argparse import ArgumentParser, RawTextHelpFormatter
import onionchat.config as cfg
from onionchat.pipeline_builder import PipelineBuilder
from onionchat.utils.funcs import load_class
import ast

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=cfg.logging_level,
    format=cfg.logging_format
)

def cls_help_pair(alias: str) -> Tuple[str, str]:
    cls = {**cfg.CONNS, **cfg.CHATS, **cfg.HANDLERS, **cfg.PLUGINS}
    path = cls.get(alias)
    if not path:
        return (alias, "Unknown class alias")

    return (alias, load_class(path).__doc__ or "No documentation available")

def format_choices(mapping: dict) -> str:
    lines = []
    for k in mapping.keys():
        alias, doc = cls_help_pair(k)
        f_doc = "\n".join("\t" + line for line in doc.splitlines())
        lines.append(f"{alias}\n{f_doc}")
    return "\n" + "\n\n".join(lines)

def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description="OnionChat, secure comms CLI.\nArgs format --key=value, eg. --dest-ip=127.0.0.1"
    )

    parser.add_argument(
        "conn",
        type=str,
        nargs="?",
        default=cfg.default_conn,
        help=f"Connection type:{format_choices(cfg.CONNS)}\n"
    )

    parser.add_argument(
        "chat",
        type=str,
        nargs="?",
        default=cfg.default_chat,
        help=f"Chat type:{format_choices(cfg.CHATS)}\n"
    )

    parser.add_argument(
        "handler",
        type=str,
        nargs="?",
        default=cfg.default_handler,
        help=f"Handler type:{format_choices(cfg.HANDLERS)}\n"
    )

    parser.add_argument(
        "-pl", "--plugins",
        type=str,
        nargs="*",
        default=cfg.default_plugins,
        help=f"Plugins to apply:{format_choices(cfg.PLUGINS)}\n",
        dest="plugins"
    )

    return parser

def main() -> None:
    parser = build_parser()
    args, unknown = parser.parse_known_args()

    custom_args = {}
    def parse_value(value: str):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    for arg in unknown:
        if '=' in arg:
            key, value = arg.split('=', 1)
            custom_args[key.lstrip('--').replace('-', '_')] = parse_value(value)

    pline = PipelineBuilder(args.conn, args.chat, args.handler, args.plugins, custom_args)
    handler = pline.build()
    handler.open()

if __name__ == '__main__':
    main()