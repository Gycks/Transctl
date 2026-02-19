import logging
from importlib.metadata import version

from transctl.cli.commands import COMMANDS
from transctl.console_formater import ConsoleFormatter

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
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        return


for command in COMMANDS:
    main.add_command(command)


def cli() -> int:
    try:
        main(standalone_mode=False)
        return 0

    except click.ClickException as ce:
        click.echo("hello")
        logging.error(ConsoleFormatter.error(ce.format_message()))
        return ce.exit_code

    except SystemExit as se:
        return int(se.code or 0)

    except Exception as e:
        click.echo("hello")
        logging.error(ConsoleFormatter.error(str(e)))
        return 1


if __name__ == "__main__":
    raise SystemExit(cli())
