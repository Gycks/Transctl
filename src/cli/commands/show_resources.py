import sys

from src.models.translation_resource import TranslationResourceType

import click


@click.command('show-resources', help='Show supported resource types.')
@click.pass_context
def show_resources(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        langs: str = '\n'.join([f"* {val.value.upper()}" for val in TranslationResourceType])
        click.echo(langs)
        sys.exit(0)
