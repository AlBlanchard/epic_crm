import click

from ..controllers.base import AbstractController
from ..views.user_view import UserView
from ..auth.permission import Permission
from ..auth.auth import Authentication
from ..utils.validations import Validations
from ..errors.exceptions import UserCancelledInput
from ..controllers.user_controller import UserController
from ..controllers.role_controller import RoleController
from ..utils.audit_decorators import audit_command


class UserMenuController(AbstractController):
    def _setup_services(self) -> None:
        self.view = UserView()
        self.user_ctrl = UserController()
        self.role_ctrl = RoleController()

    def show_user_list(self, user_id: int | None = None, selector: bool = False):
        """Affiche la liste des utilisateurs."""
        me = self.user_ctrl._get_current_user()
        if not Permission.read_permission(me, "user"):
            if not Permission.read_permission(me, "user", owner_id=user_id):
                raise PermissionError("Accès refusé.")

        rows = self.user_ctrl.get_all_users(
            filters={"id": user_id} if user_id else None
        )
        return self.view.list_users(rows, selector)

    @audit_command(
        category="user", action="update_password", event_level_on_success="warning"
    )
    def show_update_password(self, user_id: int | None = None):
        """Affiche le formulaire de mise à jour du mot de passe."""
        me = self.user_ctrl._get_current_user()
        if user_id:
            # Refuse si l'id n'est pas le miens
            if not Permission.update_permission(
                me, "user", owner_id=user_id, own_only=True
            ):
                # Si l'id n'est pas le miens, refuse si je ne suis pas admin
                if not Permission.is_admin(me):
                    raise PermissionError("Accès refusé.")

        # Sélection de l'utilisateur si pas d'id transmis, ADMIN ONLY
        if not user_id:
            if not Permission.is_admin(me):
                raise PermissionError("Accès refusé.")

            rows = self.user_ctrl.get_all_users()
            user_id = self.view.list_users(rows, selector=True)
            if not user_id:
                return

        # Dans le cas où l'admin modifie le mdp de quelqu'un d'autre, pas besoin de l'ancien mdp
        # Cependant s'il souhaite modifier son propre MDP, il doit fournir l'ancien mot de passe
        if me.id == int(user_id):
            self.view._clear_screen()
            self.view._print_back_choice()
            password = click.prompt("Ancien mot de passe", hide_input=True)
            try:
                if not Authentication.verify_password(password, me.password_hash):
                    raise ValueError("Mot de passe incorrect.")
            except Exception as e:
                self.view.app_state.set_error_message(str(e))
                return

        UserView._clear_screen()
        new_pwd = self.view.update_user_password_flow()
        if new_pwd is None:
            return

        # revalidation côté ctrl, source de vérité
        try:
            _ = self.user_ctrl.get_user(int(user_id))
        except Exception as e:
            self.view.app_state.set_error_message(str(e))
            return

        try:
            self.user_ctrl.update_user(user_id, {"password": new_pwd})
            if self.view.app_state:
                self.view.app_state.set_success_message(
                    "Le mot de passe de l'utilisateur a été mis à jour avec succès."
                )
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    @audit_command(category="user", action="create", event_level_on_success="info")
    def show_create_user(self) -> None:
        """Affiche le formulaire de création d'un utilisateur."""
        me = self.user_ctrl._get_current_user()
        if not Permission.create_permission(me, "user"):
            raise PermissionError("Accès refusé.")

        employees_nbr = self.user_ctrl.get_all_employees_nbr()
        result = self.view.create_user_flow(employees_nbr)
        if result is None:
            return

        data, role_id = result

        try:
            new_user = self.user_ctrl.create_user(data)
            self.user_ctrl.add_role(new_user["id"], int(role_id), create_new_user=True)

            self.view.app_state.set_success_message(
                "L'utilisateur a été créé avec succès."
            )
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    @audit_command(category="user", action="update", event_level_on_success="info")
    def show_update_user_infos(self, user_id: int) -> None:
        if not user_id:
            rows = self.user_ctrl.get_all_users()
            selected_id = self.view.list_users(rows, selector=True)
            if not selected_id:
                return
            user_id = selected_id

        me = self.user_ctrl._get_current_user()
        if not Permission.update_permission(me, "user"):
            raise PermissionError("Accès refusé.")

        user_dict = self.user_ctrl.get_user(user_id)
        result = self.view.update_user_infos_flow(user_dict)

        if result is None:
            return

        uid, payload = result

        try:
            self.user_ctrl.update_user(uid, payload)
            if self.view.app_state:
                self.view.app_state.set_success_message(
                    "L'utilisateur a été mis à jour avec succès."
                )
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    @audit_command(category="user", action="delete", event_level_on_success="warning")
    def show_delete_user(self, user_id: int | None = None) -> None:
        """Affiche le formulaire de suppression d'un utilisateur."""
        # Sélection de l'utilisateur si pas d'id transmis
        if not user_id:
            rows = self.user_ctrl.get_all_users()
            user_id = self.view.list_users(rows, selector=True)
            if not user_id:
                return

        me = self.user_ctrl._get_current_user()
        if not Permission.delete_permission(me, "user"):
            raise PermissionError("Accès refusé.")

        try:
            user = self.user_ctrl.get_user(int(user_id))
        except Exception as e:
            self.view.app_state.set_error_message(str(e))
            return

        confirmed = self.view.delete_user_flow(user["username"])

        if not confirmed:
            self.view.app_state.set_neutral_message("Action annulée par l'utilisateur.")
            return

        try:
            self.user_ctrl.delete_user(user["id"])
            self.view.app_state.set_success_message(
                "L'utilisateur a été supprimé avec succès."
            )
        except Exception as e:
            self.view.app_state.set_error_message(str(e))

    @audit_command(category="user", action="update", event_level_on_success="info")
    def show_add_user_role(
        self, user_id: int | None = None, role_id: int | None = None
    ):
        # Sélection de l'utilisateur si pas d'id transmis
        if not user_id:
            rows = self.user_ctrl.get_all_users()
            user_id = self.view.list_users(rows, selector=True)
            if not user_id:
                return

        # Sélection du rôle si pas de rôle transmis
        if not role_id:
            roles = self.role_ctrl.list_roles()
            actual_roles = self.user_ctrl.get_user_roles(user_id)
            role_id = self.view.add_user_role_flow(actual_roles, roles)
            if not role_id:
                return

        # revalidation côté ctrl, source de vérité
        try:
            _ = self.user_ctrl.get_user(int(user_id))
            _ = self.role_ctrl.get_role(int(role_id))
        except Exception as e:
            self.view.app_state.set_error_message(str(e))
            return

        try:
            self.user_ctrl.add_role(user_id, role_id)
            if self.view.app_state:
                self.view.app_state.set_success_message(
                    "Le rôle a été ajouté à l'utilisateur avec succès."
                )
        except Exception as e:
            if self.view.app_state:
                self.view.app_state.set_error_message(str(e))

    @audit_command(category="user", action="update", event_level_on_success="info")
    def show_remove_user_role(
        self, user_id: int | None = None, role_name: str | None = None
    ) -> None:
        # Sélection de l'utilisateur si pas d'id transmis
        if not user_id:
            rows = self.user_ctrl.get_all_users()
            user_id = self.view.list_users(rows, selector=True)
            if not user_id:
                return

        # Sélection du rôle si pas de rôle transmis
        if not role_name:
            actual_roles = self.user_ctrl.get_user_roles(user_id)
            role_name = self.view.remove_user_role_flow(actual_roles)
            if not role_name:
                return

        try:
            # revalidation côté ctrl, source de vérité
            _ = self.user_ctrl.get_user(int(user_id))
            role = self.role_ctrl.get_role_by_name(role_name)

            confirmed = Validations.confirm_action(
                f"Êtes-vous sûr de vouloir supprimer le rôle '{role_name}' de l'utilisateur ?"
            )

            if not confirmed:
                return

            self.user_ctrl.remove_role(user_id, role["id"])
            if self.view.app_state:
                self.view.app_state.set_success_message(
                    "Le rôle a été retiré de l'utilisateur avec succès."
                )

        except Exception as e:
            self.view.app_state.set_error_message(str(e))
            return
