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
from ..auth.auth import Authentication


class UserView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()
        self.user_ctrl = UserController()

    def _choose_role(self, roles: list[dict], *, max_attempts: int | None = 3) -> str:
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
            return row["id"]

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
        - 'confirm': demande une confirmation si True.
        - 'quit_aliases': valeurs pour annuler (insensibles à la casse).
        - 'allow_empty': autorise vide si True.
        - 'max_attempts': nombre max d'essais (None = illimité).
        Renvoie un mdp hashé.
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

                if pwd == "" and not allow_empty:
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
                roles = RoleController(session=session)

                chosen_role_id = self._choose_role(roles.list_roles())

                self.console.print("[dim]Création de l'utilisateur...[/dim]")

                payload: dict = {
                    "username": username,
                    "email": email,
                    "employee_number": employee_number,
                    "password": password,
                }

                return payload, chosen_role_id

        except Exception as e:
            if isinstance(e, UserCancelledInput):
                self.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            else:
                self.app_state.set_error_message(str(e))

    def list_users(self, rows: list[dict], selector: bool = False) -> None:
        self._clear_screen()
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
            validate_number = Validations.validate_number
            self.console.print("[dim]Sélectionnez un utilisateur...[/dim]")
            str_user_id = self.get_valid_input(
                "ID de l'utilisateur",
                validate=validate_number,
                list_to_compare=[str(u["id"]) for u in rows],
            )

            user_id = int(str_user_id)

            # ignore car l'IDE ne comprend pas que la validation empêche que ce soit None
            return user_id  # type: ignore

        self.console.print("\n[dim]Appuyez sur Entrée pour revenir au menu...[/dim]")
        self.app_state.display_error_or_success_message()
        self.console.input()

    def update_user_infos_flow(self, user_dict: dict) -> tuple[int, dict] | None:
        self._clear_screen()
        try:
            user_id = user_dict["id"]
            current_username = user_dict["username"]
            current_email = user_dict["email"]
            current_employee_number = user_dict["employee_number"]

            self.console.print(
                f"\n[bold]Modification de l'utilisateur #{user_id}[/bold]"
            )
            username = self.get_valid_input(
                f"Nouveau nom", default=f"{current_username}"
            )
            email = self.get_valid_input(f"Nouvel email", default=f"{current_email}")
            employee_number = self.get_valid_input(
                f"Nouveau numéro d'employé",
                default=f"{current_employee_number}",
                transform=lambda s: int(s) if s.strip() else None,
            )

            payload: dict = {}
            if username:
                username.strip()
                payload["username"] = username.strip()
            if email:
                email.strip()
                payload["email"] = email.strip()
            if isinstance(employee_number, int):
                payload["employee_number"] = employee_number

            if not payload:
                raise UserCancelledInput("Aucune modification réalisée.")

            return user_id, payload

        except UserCancelledInput:
            self.app_state.set_neutral_message("Modification annulée.")
        except Exception as e:
            self.app_state.set_error_message(str(e))

    def update_user_password_flow(self) -> str | None:
        try:
            new_password = self.get_valid_password(
                "Nouveau mot de passe (laisser vide pour ne pas changer) :",
                allow_empty=True,
            )

            if not new_password:
                raise UserCancelledInput("Aucune modification réalisée.")

            return new_password

        except UserCancelledInput:
            self.app_state.set_neutral_message("Modification annulée.")
        except Exception as e:
            self.app_state.set_error_message(str(e))

    def delete_user_flow(self, username: str) -> int | None:
        self._clear_screen()
        self.app_state.display_error_or_success_message()
        confirm = Validations.confirm_action(
            f"Êtes-vous sûr de vouloir supprimer l'utilisateur '{username}' ?"
        )

        return confirm

    def add_user_role_flow(self, actual_roles_list, roles_list) -> int | None:
        self._clear_screen()
        try:
            self.console.print("Rôles de l'utilisateur :")
            for role in actual_roles_list:
                self.console.print(f" - {role}")

            role_id = self._choose_role(roles_list)
            return int(role_id)

        except UserCancelledInput:
            self.app_state.set_neutral_message("Ajout de rôle annulé.")
        except Exception as e:
            self.app_state.set_error_message(str(e))

    def remove_user_role_flow(self, actual_roles_list) -> str | None:
        self._clear_screen()
        try:
            self.console.print("Rôles de l'utilisateur :")
            for role in actual_roles_list:
                self.console.print(f" - {role}")

            role_name = self.get_valid_input(
                "Nom du rôle à supprimer :", list_to_compare=actual_roles_list
            )

            return role_name

        except UserCancelledInput:
            self.app_state.set_neutral_message("Suppression de rôle annulée.")
        except Exception as e:
            self.app_state.set_error_message(str(e))

    def modify_menu(self, user_id: int, username: str, ctx: click.Context) -> None:
        while True:
            self._clear_screen()
            self.console.print(
                f"\n[bold yellow]-- Modification de l'utilisateur : '{username}' --[/bold yellow]"
            )
            self.console.print("1. Modifier les informations")
            self.console.print("2. Modifier le mot de passe")
            self.console.print("3. Ajouter un rôle")
            self.console.print("4. Supprimer un rôle")
            self.console.print("5. Retour")
            self.print_quit_option()

            self.app_state.display_error_or_success_message()
            choice = self.ask_choice()

            try:
                if choice == 0:
                    self.handle_quit()
                elif choice == 1:
                    ctx.invoke(update_user_infos_cmd, user_id=user_id)
                    break
                elif choice == 2:
                    ctx.invoke(update_user_password_cmd, user_id=user_id)
                    break
                elif choice == 3:
                    ctx.invoke(add_user_role_cmd, user_id=user_id)
                    break
                elif choice == 4:
                    ctx.invoke(remove_user_role_cmd, user_id=user_id)
                    break
                elif choice == 5:
                    break
                else:
                    self.app_state.set_error_message("Choix invalide")
                    self.app_state.testprint()

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
    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    result = view.create_user_flow()
    if result is None:
        return

    data, role_id = result

    try:
        new_user = ctrl.create_user(data)
        ctrl.add_role(new_user["id"], int(role_id))

        view.app_state.set_success_message("L'utilisateur a été créé avec succès.")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="list-users")
@click.pass_context
def list_users_cmd(ctx: click.Context) -> None:
    # On réutilise la vue attachée au contexte si dispo, sinon on en crée une
    view: UserView = (
        ctx.obj.get("user_view")
        if ctx and ctx.obj and "user_view" in ctx.obj
        else UserView()
    )

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    rows = ctrl.get_all_users()
    view.list_users(rows, selector=False)


@click.command(name="update-user")
@click.option("--id", "user_id", type=int, help="ID de l'utilisateur à modifier")
@click.pass_context
def update_user_cmd(ctx: click.Context, user_id: int | None) -> None:
    """Ouvre un menu de modification pour l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    username = ctrl.get_user_name(user_id)
    view.modify_menu(user_id, username, ctx)


@click.command(name="update-user-infos")
@click.option("--id", "user_id", type=int, help="ID de l'utilisateur à modifier")
@click.pass_context
def update_user_infos_cmd(ctx: click.Context, user_id: int | None) -> None:
    """Modifie les infos non sensibles de l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    user_dict = ctrl.get_user(user_id)
    result = view.update_user_infos_flow(user_dict)

    if result is None:
        return

    uid, payload = result

    # revalidation côté ctrl, source de vérité
    try:
        _ = ctrl.get_user(int(uid))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    try:
        ctrl.update_user(uid, payload)
        if view.app_state:
            view.app_state.set_success_message(
                "L'utilisateur a été mis à jour avec succès."
            )
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="update-user-password")
@click.option(
    "--id",
    "user_id",
    type=int,
    help="ID de l'utilisateur dont le mot de passe doit être modifié",
)
@click.pass_context
def update_user_password_cmd(ctx: click.Context, user_id: int | None) -> None:
    """Modifie uniquement le mot de passe de l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    new_pwd = view.update_user_password_flow()
    if new_pwd is None:
        return

    # revalidation côté ctrl, source de vérité
    try:
        _ = ctrl.get_user(int(user_id))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    try:
        ctrl.update_user(user_id, {"password": new_pwd})
        if view.app_state:
            view.app_state.set_success_message(
                "Le mot de passe de l'utilisateur a été mis à jour avec succès."
            )
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="delete-user")
@click.pass_context
def delete_user_cmd(ctx: click.Context, user_id: int | None) -> None:
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    try:
        user = ctrl.get_user(int(user_id))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    confirmed = view.delete_user_flow(user["username"])

    if not confirmed:
        raise UserCancelledInput("Suppression annulée par l'utilisateur.")

    try:
        ctrl.delete_user(user["id"])
        view.app_state.set_success_message("L'utilisateur a été supprimé avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="add-user-role")
@click.option(
    "--id",
    "user_id",
    type=int,
    help="ID de l'utilisateur auquel ajouter un rôle",
)
@click.option(
    "--role",
    "role_id",
    type=int,
    help="ID du rôle à ajouter à l'utilisateur",
)
@click.pass_context
def add_user_role_cmd(
    ctx: click.Context, user_id: int | None, role_id: int | None
) -> None:
    """Ajoute un rôle à l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    role_ctrl: RoleController = ctx.obj.get("role_controller") or RoleController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    # Sélection du rôle si pas de rôle transmis
    if not role_id:
        roles = role_ctrl.list_roles()
        actual_roles = ctrl.get_user_roles(user_id)
        role_id = view.add_user_role_flow(actual_roles, roles)
        if not role_id:
            return

    # revalidation côté ctrl, source de vérité
    try:
        _ = ctrl.get_user(int(user_id))
        _ = role_ctrl.get_role(int(role_id))
    except Exception as e:
        view.app_state.set_error_message(str(e))
        return

    try:
        ctrl.add_role(user_id, role_id)
        if view.app_state:
            view.app_state.set_success_message(
                "Le rôle a été ajouté à l'utilisateur avec succès."
            )
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="remove-user-role")
@click.option(
    "--id",
    "user_id",
    type=int,
    help="ID de l'utilisateur dont on veut retirer un rôle",
)
@click.option(
    "--role",
    "role_name",
    type=str,
    help="Nom du rôle à retirer de l'utilisateur",
)
@click.pass_context
def remove_user_role_cmd(
    ctx: click.Context, user_id: int | None, role_name: str | None
) -> None:
    """Retire un rôle de l'utilisateur spécifié."""
    ctx.ensure_object(dict)
    console = ctx.obj.get("console")

    view: UserView = ctx.obj.get("user_view") or UserView(console=console)

    ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    role_ctrl: RoleController = ctx.obj.get("role_controller") or RoleController(
        session=SessionLocal()
    )

    # Sélection de l'utilisateur si pas d'id transmis
    if not user_id:
        rows = ctrl.get_all_users()
        user_id = view.list_users(rows, selector=True)
        if not user_id:
            return

    # Sélection du rôle si pas de rôle transmis
    if not role_name:
        actual_roles = ctrl.get_user_roles(user_id)
        role_name = view.remove_user_role_flow(actual_roles)
        if not role_name:
            return

    try:
        # revalidation côté ctrl, source de vérité
        _ = ctrl.get_user(int(user_id))
        role = role_ctrl.get_role_by_name(role_name)

        confirmed = Validations.confirm_action(
            f"Êtes-vous sûr de vouloir supprimer le rôle '{role_name}' de l'utilisateur ?"
        )

        if not confirmed:
            return

        ctrl.remove_role(user_id, role["id"])
        if view.app_state:
            view.app_state.set_success_message(
                "Le rôle a été retiré de l'utilisateur avec succès."
            )

    except Exception as e:
        view.app_state.set_error_message(str(e))
        return
