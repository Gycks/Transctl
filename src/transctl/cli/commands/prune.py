from transctl.core.configuration_manager import ConfigurationManager
from transctl.models.policies import PrunePolicy
from transctl.models.tm_store import TMStore

import click
from sqlalchemy.orm import Session


@click.command("prune", short_help="Prune the memory store.")
@click.pass_context
def prune_store(ctx: click.Context) -> None:
    if ctx.invoked_subcommand is None:
        db_path: str = str(ConfigurationManager(cold_start=True).get_store_path())
        store: TMStore = TMStore(db_path=db_path)

        with Session(store.engine) as session:
            store.prune(session, PrunePolicy())

        session.commit()
        return
