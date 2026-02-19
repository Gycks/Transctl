from pathlib import Path
from typing import Callable

from transctl.core.configuration_manager import ConfigurationManager
from transctl.core.handlers.base_translation_handler import BaseTranslationHandler
from transctl.core.handlers.handle_html_translation import HtmlTranslationTranslationHandler
from transctl.core.handlers.handle_json_translation import JsonTranslationTranslationHandler
from transctl.core.translation_run_manifest import TranslationRunManifest
from transctl.models.app_config import AppConfig
from transctl.models.translation_resource import TranslationResource, TranslationResourceType


THandlerCtor = Callable[
    [
        ConfigurationManager,
        AppConfig,
        TranslationRunManifest
    ],
    BaseTranslationHandler]


class TranslationCoordinator:
    def __init__(self) -> None:
        self._config_manager: ConfigurationManager = ConfigurationManager()

        self._handler_mapping: dict[TranslationResourceType, THandlerCtor] = {
            TranslationResourceType.JSON: JsonTranslationTranslationHandler,
            TranslationResourceType.HTML: HtmlTranslationTranslationHandler,
        }

        self._tr_manifest: TranslationRunManifest = TranslationRunManifest(self._config_manager)

    def translate_from_config(self, glossary: str | None = None) -> list[str]:
        config: AppConfig | None = self._config_manager.configuration
        glossary_path: Path | None = Path(glossary) if glossary else None

        if config is None:
            raise ValueError("Configuration is not loaded.")

        resources: list[TranslationResource]
        if config.resources is None:
            return []

        response: list[str] = []
        for type_, resources in config.resources.items():
            handler: BaseTranslationHandler = self._handler_mapping[type_](self._config_manager, config, self._tr_manifest)

            resource: TranslationResource
            for resource in resources:
                for input_path, output_path in resource.bucket:
                    handler_re: list[str] = handler.translate_file(input_path, output_path, glossary_path, resource.tag)
                    response.extend(handler_re)

        self._tr_manifest.rebuild_from_config()
        return response
