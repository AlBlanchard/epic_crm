import click


class CliUtils:
    @staticmethod
    def invoke(ctx: click.Context, name: str, **kwargs):
        """Récupère une sous-commande enregistrée sur le group racine et l'invoque."""
        root = ctx.find_root()
        if isinstance(root.command, click.Group):
            cmd = root.command.get_command(ctx, name)
            if cmd is None:
                raise click.ClickException(f"Commande '{name}' introuvable.")
            return ctx.invoke(cmd, **kwargs)
        raise click.ClickException("Root command n'est pas un command group.")
