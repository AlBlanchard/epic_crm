from pathlib import Path
from typing import Optional

TOKEN_PATH = Path.home() / ".epicevents_token"


def save_token(token: str):
    TOKEN_PATH.write_text(token)


def load_token() -> Optional[str]:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text()
    return None
