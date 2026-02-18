from src.core.translation_run_manifest import TranslationRunManifest
from src.core.configuration_manager import ConfigurationManager

import click


@click.command("purge", short_help="Purge the cache manifest.")
@click.pass_context
def purge_cache(ctx: click.Context):
    if ctx.invoked_subcommand is None:
        cfg: ConfigurationManager = ConfigurationManager(cold_start=True)
        manifest: TranslationRunManifest = TranslationRunManifest(cfg)
        manifest.purge()
