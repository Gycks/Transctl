from typing import Type, Callable, Union
from pathlib import Path

from src.models.app_config import AppConfig
from src.core.configuration_manager import ConfigurationManager
from src.core.handlers.base_translation_handler import BaseTranslationHandler
from src.core.handlers.handle_json_translation import JsonTranslationTranslationHandler
from src.core.handlers.handle_html_translation import HtmlTranslationTranslationHandler
from src.models.translation_resource import TranslationResourceType, TranslationResource
from src.core.translation_run_manifest import TranslationRunManifest


THandlerCtor = Callable[[Union[JsonTranslationTranslationHandler, HtmlTranslationTranslationHandler]], BaseTranslationHandler]


class TranslationCoordinator:
    def __init__(self):
        self._config_manager: ConfigurationManager = ConfigurationManager()

        self._handler_mapping: dict[TranslationResourceType, Type[THandlerCtor]] = {
            TranslationResourceType.JSON: JsonTranslationTranslationHandler,
            TranslationResourceType.HTML: HtmlTranslationTranslationHandler,
        }

        self._tr_manifest: TranslationRunManifest = TranslationRunManifest(self._config_manager)

    def translate_from_config(self, glossary: str | None = None):
        config: AppConfig = self._config_manager.configuration
        glossary_path: Path | None = Path(glossary) if glossary else None

        resources: list[TranslationResource]
        if config.resources is None:
            return

        for type_, resources in config.resources.items():
            handler: BaseTranslationHandler = self._handler_mapping[type_](self._config_manager, config, self._tr_manifest)

            resource: TranslationResource
            for resource in resources:
                for input_path, output_path in resource.bucket:
                    handler.translate_file(input_path, output_path, glossary_path, resource.tag)

        self._tr_manifest.rebuild_from_config()
