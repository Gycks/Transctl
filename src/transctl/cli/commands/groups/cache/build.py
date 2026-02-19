from transctl.core.configuration_manager import ConfigurationManager
from transctl.core.translation_run_manifest import TranslationRunManifest

import click


@click.command("build", short_help="Build the cache manifest.")
@click.option("--force", is_flag=True, help="Force rebuild of the cache manifest.")
@click.pass_context
def build_cache(ctx: click.Context, force: bool) -> None:
    if ctx.invoked_subcommand is None:
        cfg: ConfigurationManager = ConfigurationManager()
        manifest: TranslationRunManifest = TranslationRunManifest(cfg)
        manifest.rebuild_from_config(force=force)
        return