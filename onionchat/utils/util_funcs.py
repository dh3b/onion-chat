from typing import List

def wrap_text(text: str, threshold: int) -> List[str]:
        out = []
        while len(text) > threshold:
            out.append(text[:threshold])
            text = text[threshold:]
        return out + [text]