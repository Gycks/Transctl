from transctl.ci_runners.base_runner import BaseRunner
from transctl.ci_runners.ci_runner_factory import CIRunnerFactory
from transctl.core.translation_coordinator import TranslationCoordinator

import click


@click.command('ci', help='Run the translation process in CI mode.')
@click.option("-g", "--glossary", help="Path to glossary file (JSON).", default="")
@click.option("--no-pull-request", is_flag=True, help="Do not open a new pull request.")
@click.pass_context
def ci(ctx: click.Context, glossary: str, no_pull_request: bool) -> None:
    if ctx.invoked_subcommand is None:
        coordinator: TranslationCoordinator = TranslationCoordinator()
        changed_files: list[str]
        if glossary:
            changed_files = coordinator.translate_from_config(glossary)
        else:
            changed_files = coordinator.translate_from_config()

        runner: BaseRunner = CIRunnerFactory.get_runner()
        runner.run("Translations updated.", changed_files, no_pull_request)
        return
