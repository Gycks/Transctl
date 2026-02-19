import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

from transctl.core.configuration_manager import ConfigurationManager
from transctl.core.constants.supported_languages import SUPPORTED_LANGUAGES
from transctl.core.factory.translator_factory import TranslatorFactory
from transctl.core.translation_run_manifest import TranslationRunManifest
from transctl.core.translators.base_translator import BaseTranslator
from transctl.models.app_config import AppConfig
from transctl.models.engine_config import EngineConfig
from transctl.models.policies import PrunePolicy
from transctl.models.tm_store import TMStore

from sqlalchemy.orm import Session


class BaseTranslationHandler(ABC):
    def __init__(self, config: AppConfig, cfg: ConfigurationManager) -> None:
        self.engine: EngineConfig = config.engine
        self.manifest: TranslationRunManifest | None = None
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.extension: str = ""
        self.languages: list[str] = config.targets
        self.translator: BaseTranslator = TranslatorFactory.get_translator(config.engine)

        if config.source not in SUPPORTED_LANGUAGES:
            raise ValueError(f'Source language {config.source} is not supported.')

        self.source_language = config.source
        self.store: TMStore = TMStore(db_path=str(cfg.get_store_path()))
        self._pruning_policy: PrunePolicy = PrunePolicy()

        self.placeholder_regex: re.Pattern[str] = re.compile(r"\{\{.*?\}\}")
        self.email_regex: re.Pattern[str] = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
        self.url_regex: re.Pattern[str] = re.compile(r"\bhttps?://[^\s<>()]+", re.IGNORECASE)

    @abstractmethod
    def translate_file(self, file_path: Path, output_path: Path, glossary: Path | None = None, output_path_tag: str | None = None) -> list[str]:
        pass

    def prune_store(self) -> None:
        with Session(self.store.engine) as session:
            self.store.prune(session, self._pruning_policy)
