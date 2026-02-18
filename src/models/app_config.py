import os
import logging
from typing import Any, Optional
from typing_extensions import Self

import src.core.constants.app as app_constants
from src.console_formater import ConsoleFormatter
from src.models.engine_config import EngineConfig
from src.models.translation_resource import TranslationResource, TranslationResourceType
from src.core.factory.engine_factory import EngineFactory
from src.core.constants.supported_languages import SUPPORTED_LANGUAGES
from src.core.errors.configuration_errors import ConfigurationError

import tomli
from pydantic import BaseModel, ValidationError


logger: logging.Logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    """
    Represents the application's localization configuration loaded from a TOML file.

    Attributes
     source (str): The source locale (required).
     targets (Optional[list[str]]): List of target locales.
     engine (EngineConfig): The translation engine.
     resources (Optional[dict[TranslationResourceType, list[TranslationResource]]]): A mapping of translation resource types to lists of translation resources, defining where to find the content to be translated and how to structure the output.
    """

    source: str
    targets: list[str] = []
    engine: EngineConfig
    resources: Optional[dict[TranslationResourceType, list[TranslationResource]]] = None

    @classmethod
    def _parse_translation_resources(cls, data: any) -> dict[TranslationResourceType, list[TranslationResource]] | None:
        """
        Parses the translation resources from the configuration data.

        Args:
            data (any): The raw translation resources data from the configuration.

        Returns:
            Optional[dict[TranslationResourceType, list[TranslationResource]]]: A mapping of translation resource types to lists of translation resources.
        """

        if data is None:
            return None

        if not isinstance(data, dict):
            raise ConfigurationError("The 'resources' section in the configuration file has an invalid format.")

        resources: dict[TranslationResourceType, list[TranslationResource]] = {}
        valid_types: list[str] = [t for t in TranslationResourceType]
        for type_, content in data.items():
            type_ = type_.lower().strip()
            if type_ not in valid_types:
                raise ConfigurationError(f"Unknown resource type: '{type_}' found.")

            if not isinstance(content, dict):
                raise ConfigurationError("The 'resources' section in the configuration file has an invalid format.")

            resources[TranslationResourceType(type_)] = []
            dirs: list[str] | None = content.get("dirs", [])
            for dir_ in dirs:
                value: TranslationResource = TranslationResource.from_obj(dir_)
                if value is not None:
                    resources[TranslationResourceType(type_)].append(value)

        return resources

    @classmethod
    def _parse_config(cls, obj: dict) -> Self:
        """
        Create an AppConfig instance from a raw configuration mapping.

        Args:
            obj (dict): The raw configuration object.

        Returns
            AppConfig: An instance of AppConfig with the parsed configuration.
        """

        if not isinstance(obj, dict):
            raise TypeError(f"Unable to parse configuration.")

        locale_config: dict[str, str] = obj.get("locale")
        if locale_config is None:
            raise ConfigurationError("No locale configured.")

        source: str | None = locale_config.get("source", None)
        targets: list[str] | None = locale_config.get("targets", [])

        engine_config: Any = obj.get("engine", None)
        translation_resource_config: Any = obj.get("resources", None)

        engine: EngineConfig
        resources: dict[TranslationResourceType, list[TranslationResource]] | None

        if not source or source is None:
            raise ConfigurationError("No source locale specified.")

        if targets is not None:
            if not isinstance(targets, list):
                raise ConfigurationError(f"Expected value type 'list' for targets locale.")

            for target_locale in targets:
                if target_locale not in SUPPORTED_LANGUAGES:
                    raise ConfigurationError(f"Invalid target locale {target_locale}")

        if engine_config is None:
            raise ConfigurationError("No engine configured.")

        try:
            logger.info(ConsoleFormatter.info("Setting up the localization engine..."))
            engine = EngineFactory.get_engine(engine_config)
            logger.info(ConsoleFormatter.success("Localization engine setup success."))

            resources = cls._parse_translation_resources(translation_resource_config)
        except (ValidationError, ValueError, TypeError) as e:
            raise ConfigurationError(str(e)) from e

        return cls(
            source=source,
            targets=targets,
            engine=engine,
            resources=resources
        )

    @classmethod
    def from_file(cls, file: str) -> Self:
        """
        Loads the configuration from a TOML file and create an AppConfig instance.

        Args:
            file (str): Path to the configuration file.

        Returns
            AppConfig: An instance of AppConfig with the loaded configuration.
        """

        logger.info(ConsoleFormatter.info("Parsing Configuration..."))

        if not os.path.isfile(file):
            raise FileNotFoundError(f"No Configuration found at: {file}.")

        if not os.path.basename(file).endswith(f".{app_constants.APP_NAME}.toml"):
            raise ConfigurationError(f"Configuration file must end with '.{app_constants.APP_NAME}.toml'.")

        data: dict[str, Any]
        with open(file, "rb") as f:
            data = tomli.load(f)

        config: AppConfig = cls._parse_config(data)
        logger.info(ConsoleFormatter.success("Configuration successfully parsed."))
        return config
