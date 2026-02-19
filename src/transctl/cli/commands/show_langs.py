
from transctl.core.constants.supported_languages import SUPPORTED_LANGUAGES

import click


@click.command('show-langs', help='Show supported locales (languages).')
@click.pass_context
def show_langs(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        langs: str = '\n'.join([f"* [{key}] : {val}" for key, val in SUPPORTED_LANGUAGES.items()])
        click.echo(langs)
        return
