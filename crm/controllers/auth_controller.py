from getpass import getpass
from rich.console import Console

from typing import Dict, Any, Optional
from .base import AbstractController
from ..auth.auth import Authentication
from ..auth.auth import JTIManager
from ..crud.user_crud import UserCRUD
from ..serializers.user_serializer import UserSerializer

console = Console()


class AuthController(AbstractController):
    """Contrôleur d'auth minimal basé sur tes classes Authentication et JTIManager."""

    def _setup_services(self) -> None:
        self.users = UserCRUD(self.session)
        self.serializer = UserSerializer()
        self.jti_store = JTIManager()

    # --- Flux interactifs ---
    def login_interactive(self) -> bool:
        """Demande login/pass et appelle self.login()."""
        username = input("Nom d'utilisateur: ")
        password = getpass("Mot de passe: ")

        try:
            result = self.login(username, password)
            console.print(
                f"[green]{result['message']}[/green] Bienvenue, [bold]{username}[/bold]!"
            )
            return True
        except Exception as e:
            console.print(f"[red]Échec de connexion : {e}[/red]")
            return False

    def logout_interactive(self) -> None:
        """Appelle self.logout() et affiche le message."""
        result = self.logout()
        console.print(f"[yellow]{result['message']}[/yellow]")

    # --- Authentification ---
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """
        1) Auth via Authentication.authenticate_user
        2) Ajoute les JTI au store (access + refresh)
        3) Sauvegarde localement l'access token
        4) Retourne le profil + tokens
        """
        tokens = Authentication.authenticate_user(username, password, self.session)
        access = tokens["access_token"]
        refresh = tokens["refresh_token"]

        # Enregistrer les JTI AVANT toute vérif stricte
        access_payload = Authentication.verify_token_without_jti(access)
        refresh_payload = Authentication.verify_token_without_jti(refresh)
        if jti := access_payload.get("jti"):
            self.jti_store.add(jti)
        if jti := refresh_payload.get("jti"):
            self.jti_store.add(jti)

        # Sauvegarde de l'access token (via TOKEN_PATH)
        Authentication.save_token(access)

        # Profil courant
        user_id = int(access_payload["sub"])
        user = self.users.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable après authentification.")

        return {
            "message": "Authentification réussie.",
            "access_token": access,
            "refresh_token": refresh,
            "me": self.serializer.serialize(user),
        }

    def me(self) -> Dict[str, Any]:
        """
        Récupère le profil lié à l'access token stocké localement.
        Vérifie exp + signature + JTI (via verify_token).
        """
        token = Authentication.load_token()
        if not token:
            raise PermissionError("Non authentifié.")
        payload = Authentication.verify_token(token)
        user_id = int(payload["sub"])
        user = self.users.get_by_id(user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")
        return self.serializer.serialize(user)

    def me_safe(self):
        """Petit wrapper safe pour ne pas lever une exception si pas connecté"""
        try:
            return self.me()
        except Exception:
            return None

    def refresh(self, refresh_token: str) -> Dict[str, Any]:
        """
        Délègue à Authentication.refresh_access_token (qui :
        - vérifie le refresh (exp + JTI),
        - révoque l'ancien jti de refresh,
        - génère nouveaux access+refresh,
        - ajoute leurs JTI au store,
        - et sauvegarde le nouvel access token).
        Retourne simplement le nouvel access token.
        """
        new_access = Authentication.refresh_access_token(refresh_token)
        return {"message": "Access token rafraîchi.", "access_token": new_access}

    def logout(self, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Révoque l'access token courant (lu depuis TOKEN_PATH) et,
        si fourni, le refresh token. Puis supprime le fichier local.
        """
        # Access token
        access = Authentication.load_token()
        if access:
            try:
                payload = Authentication.verify_token_without_jti(access)
                if jti := payload.get("jti"):
                    self.jti_store.revoke(jti)
            finally:
                # Supprime le fichier même si le token est expiré/invalide
                from ..auth.config import TOKEN_PATH

                TOKEN_PATH.unlink(missing_ok=True)

        if refresh_token:
            try:
                payload = Authentication.verify_token_without_jti(refresh_token)
                if jti := payload.get("jti"):
                    self.jti_store.revoke(jti)
            except Exception:
                # Pas bloquant si le refresh est déjà invalide/expiré
                pass

        return {"message": "Déconnexion réussie."}
