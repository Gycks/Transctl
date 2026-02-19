
from .build import build_cache
from .purge import purge_cache

import click


@click.group("cache", invoke_without_command=True, help="Manage the cache manifest used for translation change detection.")
@click.pass_context
def g_manifest(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        click.echo(ctx.command.get_help(ctx))
        return


g_manifest.add_command(build_cache)
g_manifest.add_command(purge_cache)
