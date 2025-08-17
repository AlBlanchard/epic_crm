import click
from rich.console import Console

from ..auth.auth import Authentication
from ..database import SessionLocal
from crm.auth.config import TOKEN_PATH


class AuthView:

    @staticmethod
    def ensure_authenticated() -> bool:
        """
        - Charge les tokens locaux (JSON)
        - Vérifie l'access token (incl. JTI)
        - Si expiré: tente un refresh (rotation, JTI, sauvegarde déjà gérée côté Authentication)
        - Retourne True si la session est OK, False sinon.
        """
        tokens = Authentication.load_tokens()
        if not tokens:
            return False

        access, refresh = tokens
        if not access:
            return False

        # Access OK ?
        try:
            Authentication.verify_token(access)
            return True
        except Exception:
            pass  # on tentera le refresh

        # Pas de refresh dispo ?
        if not refresh:
            return False

        # Refresh (gère: vérif, révocation ancien JTI, rotation, ajout JTI, save JSON)
        try:
            _ = Authentication.refresh_access_token(refresh)
            return True
        except Exception:
            return False
