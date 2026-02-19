from transctl.core.translation_coordinator import TranslationCoordinator

import click


@click.command('run', help='Run the translation process.')
@click.pass_context
def run(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        coordinator: TranslationCoordinator = TranslationCoordinator()
        coordinator.translate_from_config()
