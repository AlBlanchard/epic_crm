import click
from ..controllers.user_controller import UserController
from ..controllers.contract_controller import ContractController
from ..controllers.client_controller import ClientController
from ..views.contract_view import ContractView
from ..views.client_view import ClientView
from ..database import SessionLocal
from ..auth.permission import Permission
from ..auth.permission_config import Crud
from ..errors.exceptions import UserCancelledInput
from decimal import Decimal


@click.command(name="create-contract")
@click.option("--clientid", "client_id", type=int, help="ID du client à modifier")
@click.pass_context
def create_contract_cmd(ctx: click.Context, client_id: int) -> None:
    view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )
    ctrl: ContractController = ctx.obj.get("contract_controller") or ContractController(
        session=SessionLocal()
    )

    user_ctrl: UserController = ctx.obj.get("user_controller") or UserController(
        session=SessionLocal()
    )

    client_ctrl: ClientController = ctx.obj.get(
        "client_controller"
    ) or ClientController(session=SessionLocal())

    client_view: ClientView = ctx.obj.get("client_view") or ClientView()

    me = user_ctrl._get_current_user()

    if not Permission.create_permission(me, "contract"):
        raise PermissionError("Accès refusé.")

    # Sélection du client à qui sera attaché le contrat
    if not client_id:
        rows = client_ctrl.list_clients()
        selected_id = client_view.list_clients(rows, selector=True)
        if selected_id is None:
            return
        client_id = selected_id

    result = view.create_contract_flow(client_id)
    if result is None:
        return

    data = result

    try:
        ctrl.create_contract(data)
        view.app_state.set_success_message("Le contrat a été créé avec succès.")
    except Exception as e:
        if view.app_state:
            view.app_state.set_error_message(str(e))


@click.command(name="list-contracts")
@click.pass_context
def list_contracts_cmd(ctx: click.Context) -> None:
    view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )

    ctrl: ContractController = ctx.obj.get("contract_controller") or ContractController(
        session=SessionLocal()
    )

    rows = ctrl.list_contracts()
    view.list_contracts(rows)


@click.command(name="sign-contract")
@click.option("--id", "contract_id", type=int, help="ID du contrat à signer")
@click.pass_context
def sign_contract_cmd(ctx: click.Context, contract_id: int) -> None:
    view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )

    ctrl: ContractController = ctx.obj.get("contract_controller") or ContractController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()

    # Vérification des permissions afin de lister les contrats qui peuvent être modifiés
    if not contract_id:
        # Peut il tout update ? On liste tous les contrats
        if Permission.update_permission(me, "contract"):
            rows = ctrl.list_unsigned_contracts()
        # Peut il seulement update ses propres contrats ? On liste ses propres contrats
        elif Permission.update_own_permission(me, "contract"):
            rows = ctrl.list_unsigned_contracts(sales_contact_id=me.id)
        else:
            raise PermissionError("Accès refusé.")

        # Liste pour selectionner le contrat à modifier
        selected_id = view.list_contracts(rows, selector=True)
        if selected_id is None:
            return
        contract_id = selected_id

    # Vérifie encore les permissions dans le cas où l'id est directement fourni
    # Ou même par source de vérité
    owner = ctrl.get_contract_owner(contract_id)
    if not Permission.update_permission(me, "contract", owner_id=owner.id):
        raise PermissionError(f"Accès refusé.")

    if ctrl.is_contract_signed(contract_id):
        raise PermissionError("Le contrat est déjà signé.")

    is_signed = view.sign_contract_flow()
    if is_signed is None:
        raise UserCancelledInput("Action annulée par l'utilisateur.")

    payload: dict = {"is_signed": is_signed}

    try:
        ctrl.update_contract(contract_id, payload)
        view.app_state.set_success_message("Le contrat a été mis à jour avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="update-contract-amount")
@click.option("--id", "contract_id", type=int, help="ID du contrat à mettre à jour")
@click.option(
    "--payment",
    "payment_amount",
    type=Decimal,
    help="Montant du paiement à ajouter au contrat",
)
@click.pass_context
def update_contract_amount_cmd(
    ctx: click.Context, contract_id: int, payment_amount: Decimal | None = None
) -> None:
    view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )

    ctrl: ContractController = ctx.obj.get("contract_controller") or ContractController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.update_permission(me, "contract", contract_id):
        raise PermissionError("Accès refusé.")

    if not contract_id:
        if Permission.update_permission(me, "contract"):
            rows = ctrl.list_contracts()
        elif Permission.update_own_permission(me, "contract"):
            rows = ctrl.list_my_contracts()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_contracts(rows, selector=True)
        if selected_id is None:
            return
        contract_id = selected_id

    amount_total, amount_due = ctrl.get_contract_amounts(contract_id)

    if not payment_amount:
        payment_amount = view.add_payment_flow(amount_total, amount_due)

    new_amount_due = amount_due - payment_amount

    if new_amount_due < 0:
        raise ValueError("Le montant total ne peut pas être dépassé.")

    payload = {"amount_due": new_amount_due}

    try:
        ctrl.update_contract(contract_id, payload)
        view.app_state.set_success_message(
            "Le montant du contrat a été mis à jour avec succès."
        )
    except Exception as e:
        view.app_state.set_error_message(str(e))


@click.command(name="delete-contract")
@click.option("--id", "contract_id", type=int, help="ID du contrat à supprimer")
@click.pass_context
def delete_contract_cmd(ctx: click.Context, contract_id: int) -> None:
    view: ContractView = (
        ctx.obj.get("contract_view")
        if ctx and ctx.obj and "contract_view" in ctx.obj
        else ContractView()
    )

    ctrl: ContractController = ctx.obj.get("contract_controller") or ContractController(
        session=SessionLocal()
    )

    me = ctrl._get_current_user()
    if not Permission.delete_permission(me, "contract", contract_id):
        raise PermissionError("Accès refusé.")

    if not contract_id:
        if Permission.delete_permission(me, "contract"):
            rows = ctrl.list_contracts()
        elif Permission.delete_own_permission(me, "contract"):
            rows = ctrl.list_my_contracts()
        else:
            raise PermissionError("Accès refusé.")

        selected_id = view.list_contracts(rows, selector=True)
        if selected_id is None:
            return
        contract_id = selected_id

    try:
        ctrl.delete_contract(contract_id)
        view.app_state.set_success_message("Le contrat a été supprimé avec succès.")
    except Exception as e:
        view.app_state.set_error_message(str(e))
