from abc import ABC, abstractmethod
from pathlib import Path
import re
import logging

from src.core.constants.supported_languages import SUPPORTED_LANGUAGES
from src.core.translators.base_translator import BaseTranslator
from src.models.engine_config import EngineConfig
from src.models.app_config import AppConfig
from src.models.tm_store import TMStore
from src.core.factory.translator_factory import TranslatorFactory
from src.core.configuration_manager import ConfigurationManager
from src.models.policies import PrunePolicy
from src.core.translation_run_manifest import TranslationRunManifest

from sqlalchemy.orm import Session


class BaseTranslationHandler(ABC):
    def __init__(self, config: AppConfig, cfg: ConfigurationManager):
        self.engine: EngineConfig = config.engine
        self.manifest: TranslationRunManifest | None = None
        self.logger: logging = logging.getLogger(__name__)
        self.extension: str = ""
        self.languages: list[str] = config.targets
        self.translator: BaseTranslator = TranslatorFactory.get_translator(config.engine)

        if config.source not in SUPPORTED_LANGUAGES:
            raise ValueError(f'Source language {config.source} is not supported.')

        self.source_language = config.source
        self.store: TMStore = TMStore(db_path=str(cfg.get_store_path()))
        self._pruning_policy: PrunePolicy = PrunePolicy()

        self.placeholder_regex: re.Pattern = re.compile(r"\{\{.*?\}\}")
        self.email_regex: re.Pattern = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
        self.url_regex: re.Pattern = re.compile(r"\bhttps?://[^\s<>()]+", re.IGNORECASE)

    @abstractmethod
    def translate_file(self, file_path: Path, output_path: Path, glossary: Path | None = None, output_path_tag: str | None = None):
        pass

    def prune_store(self):
        with Session(self.store.engine) as session:
            self.store.prune(session, self._pruning_policy)
