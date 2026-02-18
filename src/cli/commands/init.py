from typing import Any

from src.models.engine_config import AzureTranslateEngine, DeepLEngine, Engine
from src.core.constants.app import APP_NAME
from src.cli.utils import styled_prompt, parse_key_value_pairs, construct_engine_params
from src.core.configuration_manager import ConfigurationManager
from src.core.factory.engine_factory import EngineFactory

import click
import tomli_w


@click.command("init", short_help=f"Create the .{APP_NAME}.toml configuration file if it does not exist.")
@click.option("--force", is_flag=True,
              help="Overwrite the existing configuration file. Creates a new file if none exists.")
@click.option("-s", "--source", help="Source language code. (Default=en)", default="en")
@click.option("-t", "--targets", help="Target language code (coma-separated. Default=[])", default="")
@click.option("-e", "--engine", help="Translation engine.")
@click.option("--param", multiple=True,
              help="Engine parameter in KEY=VALUE form (e.g --param key=value). May be specified multiple times.")
@click.option("-y", "--no-interactive", is_flag=True, help="Run without interactive prompts")
def initialize(force: bool, source: str, targets: str, engine: tuple[str], param: str, no_interactive: bool):
    if not no_interactive:
        source = styled_prompt("Please enter the source locale (language code)", default="en")

        targets_list: list[str] = styled_prompt(
            "Please enter all target locales (comma-separated language codes)",
            default="",
            value_proc=lambda t: [t.strip() for t in t.split(",") if t.strip()]
        )

        engine = styled_prompt(
            "Choose your translation engine",
            type_=click.Choice([x.value.upper() for x in Engine], case_sensitive=False)
        ).lower()

        params_dict: dict[str, str] = {}
        match engine:
            case Engine.DeepL.value:
                params_dict = construct_engine_params(DeepLEngine)
            case Engine.Azure.value:
                params_dict = construct_engine_params(AzureTranslateEngine)
            case _:
                raise click.ClickException("Unable to construct engine.")

    else:
        params_dict: dict[str, str] = parse_key_value_pairs(param)
        targets_list: list[str] = [t.strip() for t in targets.split(",") if t.strip()]

    # ======================================================== #
    # Create the configuration file with the provided settings #
    # ======================================================== #
    cfg: ConfigurationManager = ConfigurationManager(cold_start=True)
    if cfg.does_config_exist() and not force:
        raise click.ClickException("Configuration file already exists. Use --force to overwrite.")

    click.secho("Overwriting existing configuration file...", fg="yellow")
    config: dict[str, Any] = dict()

    # Locale settings
    config["locale"] = {}
    config["locale"]["source"] = source
    config["locale"]["targets"] = targets_list

    # Engine settings
    config["engine"] = {}
    config["engine"]["provider"] = engine if engine else ""
    for key, value in params_dict.items():
        config["engine"][key] = value

    cfg.save_config(tomli_w.dumps(config))
    click.secho(f"Configuration file created at {cfg.config_path}", fg="green", bold=True)

    engine_factory: EngineFactory = EngineFactory()
    if engine in engine_factory.API_KEY_ENV:
        env_name: str = engine_factory.API_KEY_ENV[engine]
        click.secho(f"Make sure to set the API KEY for your engine. Try export {env_name}=", fg="yellow")
