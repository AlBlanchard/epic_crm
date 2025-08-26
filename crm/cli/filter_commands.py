import click
from typing import Optional, Any, List, Tuple
from ..database import SessionLocal
from ..views.filter_view import FilterView
from ..views.menu_view import MenuView
from ..controllers.filter_controller import FilterController, AUTHORIZED_FILTERS

SUPPORTED_ENTITIES = ["clients", "contracts", "events"]


@click.command(name="filter")
@click.pass_context
@click.argument("entity", required=True, type=click.Choice(SUPPORTED_ENTITIES))
def filter_cmd(ctx: click.Context, entity: Optional[str] = None):
    """Filtre les entités (clients, contrats, événements) selon des critères simples."""
    if entity is None:
        click.echo("Veuillez spécifier une entité à filtrer.")
        return

    ctrl: FilterController = ctx.obj.get("filter_controller") or FilterController(
        session=SessionLocal()
    )

    view: FilterView = ctx.obj.get("filter_view") or FilterView(session=SessionLocal())

    field_dict = view.choose_filter(entity, AUTHORIZED_FILTERS)
    if field_dict is None:
        return
    filter = view.enter_filter_criteria(field_dict)
    if filter is None:
        return

    result = ctrl.list_filtered(entity, filter)
    view.list_filtered(entity, result)
