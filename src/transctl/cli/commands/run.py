from transctl.core.translation_coordinator import TranslationCoordinator

import click


@click.command('run', help='Run the translation process.')
@click.option("-g", "--glossary", help="Path to glossary file (JSON).", default="")
@click.pass_context
def run(ctx: click.Context, glossary: str) -> None:
    if ctx.invoked_subcommand is None:
        coordinator: TranslationCoordinator = TranslationCoordinator()

        if glossary:
            coordinator.translate_from_config(glossary)
        else:
            coordinator.translate_from_config()

        return
