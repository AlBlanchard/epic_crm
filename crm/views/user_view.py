import click
from rich.console import Console
from ..database import SessionLocal
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController
from ..views.view import BaseView
from getpass import getpass
from ..errors.exceptions import UserCancelledInput
from ..utils.app_state import AppState
from typing import Optional, List, Iterable, Any, Dict
from ..utils.validations import Validations

validate_number = Validations.validate_number


class UserView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()
        self.user_ctrl = UserController()

    def _choose_role(
        self, roles: list[dict], *, max_attempts: int | None = None
    ) -> str:
        if not roles:
            raise ValueError("Aucun rôle n'existe encore. Créez-en d'abord (admin).")

        self.console.print("\n[bold]Rôles disponibles[/bold]")
        for r in roles:
            self.console.print(f"• [cyan]{r['id']}[/cyan] — {r['name']}")

        default_id = roles[0]["id"]
        attempts = 0

        while True:
            if max_attempts is not None and attempts >= max_attempts:
                raise ValueError(
                    "Nombre maximal d'essais atteint pour la sélection du rôle."
                )

            try:
                chosen_id = self.get_valid_input(
                    "Sélectionner le role_id souhaité",
                    default=default_id,
                    transform=int,
                )
            except Exception:
                # get_valid_input gère déjà AppState et annulation
                raise

            row = next((r for r in roles if r["id"] == chosen_id), None)
            if not row:
                self.app_state.set_error_message(
                    f"Rôle {chosen_id} introuvable. Réessaie."
                )
                attempts += 1
                continue
            return row["name"]

    @staticmethod
    def _asdict_user(o: Any) -> Dict[str, Any]:
        if isinstance(o, dict):
            return o
        roles_attr = getattr(o, "roles", [])
        if roles_attr and not isinstance(roles_attr, str):
            try:
                roles_attr = ", ".join([getattr(r, "name", str(r)) for r in roles_attr])
            except Exception:
                roles_attr = str(roles_attr)
        return {
            "id": getattr(o, "id", ""),
            "username": getattr(o, "username", ""),
            "email": getattr(o, "email", ""),
            "employee_number": getattr(o, "employee_number", ""),
            "roles": roles_attr,
            "created_at": getattr(o, "created_at", ""),
        }

    @staticmethod
    def get_valid_password(
        prompt: str = "Mot de passe : ",
        *,
        confirm: bool = True,
        quit_aliases: Iterable[str] = ("q", "quit", "exit"),
        allow_empty: bool = False,
        max_attempts: Optional[int] = 3,
    ) -> str:
        """
        Demande un mot de passe masqué à l'utilisateur avec confirmation optionnelle.
        - `confirm`: demande une confirmation si True.
        - `quit_aliases`: valeurs pour annuler (insensibles à la casse).
        - `allow_empty`: autorise vide si True.
        - `max_attempts`: nombre max d'essais (None = illimité).
        """
        attempts = 0
        aliases = {a.casefold().strip() for a in quit_aliases}

        while True:
            if max_attempts is not None and attempts >= max_attempts:
                AppState.set_error_message("Nombre maximal d'essais atteint.")
                raise ValueError("Essais max atteints, retour au menu.")

            try:
                AppState.display_error_or_success_message()
                pwd = getpass(prompt).strip()

                # Quit intention
                if pwd.casefold() in aliases:
                    AppState.set_neutral_message("Action annulée par l'utilisateur.")
                    raise UserCancelledInput("Action annulée par l'utilisateur.")

                # Gestion vide
                if not pwd and not allow_empty:
                    AppState.set_error_message("Mot de passe obligatoire. Réessaie.")
                    attempts += 1
                    continue

                # Confirmation si demandé
                if confirm:
                    pwd_confirm = getpass("Confirmer le mot de passe : ").strip()

                    # Quit intention à la confirmation
                    if pwd_confirm.casefold() in aliases:
                        AppState.set_neutral_message(
                            "Action annulée par l'utilisateur."
                        )
                        raise UserCancelledInput("Action annulée par l'utilisateur.")

                    if pwd != pwd_confirm:
                        AppState.set_error_message(
                            "Les mots de passe ne correspondent pas. Réessaie."
                        )
                        attempts += 1
                        continue

                return pwd

            except KeyboardInterrupt:
                AppState.set_neutral_message("Action annulée par l'utilisateur.")
                raise
            except EOFError:
                AppState.set_neutral_message("Action annulée par l'utilisateur.")
                raise

    def create_user_flow(self):
        try:
            self._clear_screen()

            username = self.get_valid_input("Nom d'utilisateur pour le test")
            email = self.get_valid_input("Email pour le test")
            employee_number = self.get_valid_input(
                "Numéro d'employé pour le test", transform=int
            )
            password = self.get_valid_password("Mot de passe pour le test : ")

            with SessionLocal() as session:
                users = UserController(session=session)
                roles = RoleController(session=session)

                chosen_role_name = self._choose_role(roles.list_roles())

                self.console.print("[dim]Création de l'utilisateur...[/dim]")
                new_user = users.create_user(
                    {
                        "username": username,
                        "email": email,
                        "employee_number": employee_number,
                        "password": password,
                    }
                )

                self.console.print("[dim]Assignation du rôle...[/dim]")
                users.add_role(new_user["id"], chosen_role_name)

                self.app_state.set_success_message(
                    f"Utilisateur créé : {new_user['username']} (id={new_user['id']}) {chosen_role_name}"
                )

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))

    def list_users(self, selector: bool = False) -> None:
        self._clear_screen()
        rows = self.user_ctrl.list_users()
        rows = [self._asdict_user(r) for r in rows]
        self._print_table(
            "[cyan]Utilisateurs[/cyan]",
            [
                "id",
                "username",
                "email",
                "employee_number",
                "roles",
                "created_at",
            ],
            rows,
        )

        if selector:
            self.console.print("[dim]Sélectionnez un utilisateur...[/dim]")
            self.app_state.display_error_or_success_message()
            str_user_id = self.get_valid_input(
                "ID de l'utilisateur : ",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )

            user_id = int(str_user_id)

            # revalidation côté ctrl, source de vérité
            _ = self.user_ctrl.get_user(int(str_user_id))

            # ignore car l'IDE ne comprend pas que la validation empêche que ce soit None
            return user_id  # type: ignore

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()

    def update_user_flow(self, user_id: int | None = None) -> tuple[int, dict] | None:
        try:
            # Sélection si pas d'id fourni
            if user_id is None:
                user_id = self.list_users(selector=True)
                if user_id is None:
                    # annulé
                    return

            # Récup info actuelle (pour afficher des défauts lisibles)
            user = self.user_ctrl.get_user(user_id)  # dict ou modèle
            current = self._asdict_user(user) if not isinstance(user, dict) else user

            # Demander les champs (laisser vide = ne pas changer)
            self.console.print(
                f"\n[bold]Modification de l'utilisateur #{user_id}[/bold]"
            )
            username = self.get_valid_input(
                f"Nouveau nom", default=f"{current.get('username','')}"
            )
            email = self.get_valid_input(
                f"Nouvel email", default=f"{current.get('email','')}"
            )
            employee_number = self.get_valid_input(
                f"Nouveau numéro d'employé",
                default=f"{current.get('employee_number','')}",
                transform=lambda s: int(s) if s.strip() else None,
            )
            password = self.get_valid_password(
                "Nouveau mot de passe (laisser vide pour ne pas changer)",
                allow_empty=True,
            )

            if password == "":
                # Permet d'éviter d'exposer le mot de passe dans le défault
                password = None  # Ne pas changer le mot de passe si vide

            # Construire le payload sans champs vides
            payload: dict = {}
            if username:
                username.strip()
                payload["username"] = username.strip()
            if email:
                email.strip()
                payload["email"] = email.strip()
            if isinstance(employee_number, int):
                payload["employee_number"] = employee_number
            if password:
                password.strip()
                payload["password"] = password

            if not payload:
                self.app_state.set_neutral_message("Aucune modification réalisée.")
                return

            return user_id, payload

        except UserCancelledInput:
            self.app_state.set_neutral_message("Modification annulée.")
        except Exception as e:
            self.app_state.set_error_message(str(e))


# ---- commande Click qui instancie (ou réutilise) la vue et appelle le flow ----
@click.command(name="create-user")
@click.pass_context
def create_user_cmd(ctx: click.Context) -> None:
    # On réutilise la vue attachée au contexte si dispo, sinon on en crée une
    view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )
    view.create_user_flow()


@click.command(name="list-users")
@click.pass_context
def list_users_cmd(ctx: click.Context) -> None:
    # On réutilise la vue attachée au contexte si dispo, sinon on en crée une
    view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )
    view.list_users()


@click.command(name="update-user")
@click.option("--id", "user_id", type=int, help="ID de l'utilisateur à modifier")
@click.pass_context
def update_user_cmd(ctx: click.Context, user_id: int | None) -> None:
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")
    app_state = ctx.obj.get("app_state")

    # Vue
    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    # Controller
    ctrl: UserController | None = ctx.obj.get("user_controller")
    if ctrl is None:
        # Fallback si rien dans le contexte
        from crm.database import SessionLocal

        with SessionLocal() as session:
            ctrl = UserController(session=session)

            result = view.update_user_flow(user_id)
            if result is None:
                return  # annulé ou rien à faire

            uid, payload = result
            try:
                msg = ctrl.update_user(uid, **payload)
                if view.app_state:
                    view.app_state.set_success_message(str(msg))
            except Exception as e:
                if view.app_state:
                    view.app_state.set_error_message(str(e))
        return

    # Si un controller est déjà dans ctx.obj
    result = view.update_user_flow(user_id)
    if result is None:
        return
    uid, payload = result
    try:
        msg = ctrl.update_user(uid, **payload)
        if view.app_state:
            view.app_state.set_success_message(str(msg))
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))
