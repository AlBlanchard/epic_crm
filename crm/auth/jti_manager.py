import json
from pathlib import Path
from typing import Optional, Set
from .auth import Authentication


class JTIManager:
    """
    Gère les JWT ID (jti) valides pour autoriser ou révoquer des tokens manuellement.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialise le gestionnaire avec un fichier de stockage JSON.
        """
        self.storage_path = storage_path or Path("valid_jtis.json")

        # Crée le fichier s'il n'existe pas
        if not self.storage_path.exists():
            self._save_jtis(set())

    def _load_jtis(self) -> Set[str]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError):
            return set()

    def _save_jtis(self, jtis: Set[str]):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(list(jtis), f, indent=2)

    def add(self, jti: str):
        jtis = self._load_jtis()
        jtis.add(jti)
        self._save_jtis(jtis)

    def revoke(self, jti: str):
        jtis = self._load_jtis()
        jtis.discard(jti)
        self._save_jtis(jtis)

    def revoke_refresh_jti(self, jti: str):
        """
        Révoque un token de rafraîchissement en supprimant son jti.
        """
        self.revoke(jti)

    def is_valid(self, jti: str) -> bool:
        return jti in self._load_jtis()

    def clear_all(self):
        self._save_jtis(set())
