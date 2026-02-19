import logging
import sys
from importlib.metadata import version

from transctl.cli.commands import COMMANDS

import click


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)


__version__: str = version("transctl")
help_text: str = "Transctl is a command-line tool for managing and generating application translations."
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def show_version() -> None:
    click.echo(f"transctl,  v{__version__}")


@click.group(invoke_without_command=True, context_settings=CONTEXT_SETTINGS, help=help_text)
@click.option("-v", "--version", is_flag=True, help="Show version.")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    if version:
        show_version()
        sys.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


for command in COMMANDS:
    main.add_command(command)


if __name__ == "__main__":
    main()
