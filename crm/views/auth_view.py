import click
from rich.console import Console

from ..auth.auth import Authentication
from ..database import SessionLocal
from crm.auth.config import TOKEN_PATH

console = Console()


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

    @click.command(name="login")
    def login_cmd():
        """
        Demande les identifiants, appelle Authentication.authenticate_user,
        sauvegarde access+refresh en JSON. Les JTI sont enregistrés côté Authentication.
        """
        username = click.prompt("Nom d'utilisateur")
        password = click.prompt("Mot de passe", hide_input=True)

        with SessionLocal() as session:
            try:
                pair = Authentication.authenticate_user(username, password, session)
            except Exception as e:
                console.print(f"[red]Échec de connexion : {e}[/red]")
                raise SystemExit(1)

        # Sauvegarde locale JSON (access + refresh)
        Authentication.save_tokens(pair["access_token"], pair["refresh_token"])

        console.print(
            f"[green]Authentifié avec succès.[/green] Bienvenue, [bold]{username}[/bold]!"
        )

    @click.command(name="logout")
    def logout_cmd():
        """
        Déconnexion locale : supprime le fichier de tokens.
        """
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
            console.print("[yellow]Déconnecté (tokens locaux supprimés).[/yellow]")
        else:
            console.print("[dim]Aucun token local à supprimer.[/dim]")
