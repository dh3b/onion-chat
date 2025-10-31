from typing import List
import importlib

def wrap_text(text: str, threshold: int) -> List[str]:
        out = []
        while len(text) > threshold:
            out.append(text[:threshold])
            text = text[threshold:]
        return out + [text]

def load_class(path: str):
        """Load a class from 'module:Class' or 'module.Class' style string."""
        if ":" in path:
            mod_path, cls_name = path.split(":", 1)
        elif "." in path:
            mod_path, cls_name = path.rsplit(".", 1)
        else:
            raise ValueError("Provide full module path, e.g. 'onionchat.conn.p2p:PeerConnection'")

        mod = importlib.import_module(mod_path)
        return getattr(mod, cls_name)