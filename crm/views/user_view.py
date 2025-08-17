from ..database import SessionLocal
from ..controllers.role_controller import RoleController
from ..views.view import BaseView
from getpass import getpass
from ..errors.exceptions import UserCancelledInput
from ..utils.app_state import AppState
from typing import Optional, Iterable, Any, Dict
from ..utils.validations import Validations


class UserView(BaseView):

    def _setup_services(self) -> None:
        self.app_state = AppState()

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
