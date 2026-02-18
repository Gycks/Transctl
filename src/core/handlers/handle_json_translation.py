import re
from pathlib import Path
from typing import Optional

from src.core.handlers.base_translation_handler import BaseTranslationHandler
from src.models.app_config import AppConfig
from src.core.translation_run_manifest import TranslationRunManifest
from src.core.configuration_manager import ConfigurationManager
from src.console_formater import ConsoleFormatter
from src.utils.i_o import load_json, write_json
from src.utils.utils_suit import sanitize_path, iter_strings, set_at_path, compute_hash, normalize_text

from sqlalchemy.orm import Session


class JsonTranslationTranslationHandler(BaseTranslationHandler):

    def __init__(self, cfg: ConfigurationManager, config: AppConfig, manifest: TranslationRunManifest):
        super().__init__(config, cfg)
        self.extension = ".json"
        self.manifest = manifest
        self.patterns: list[re.Pattern] = [self.placeholder_regex, self.email_regex, self.url_regex]

    def translate_file(self, file_path: Path, output_path: Path, glossary: Path | None = None,
                       output_path_tag: str | None = None):

        self.logger.info(ConsoleFormatter.info(f"Processing path: {file_path}"))

        if file_path.suffix != self.extension:
            raise ValueError(f"File {file_path} does not have the expected extension {self.extension}")

        glossary_content: dict[str, str] | None = None
        if glossary:
            glossary_content: dict[str, str] = load_json(glossary)

        file_content: dict = load_json(file_path)
        file_content_iter: list = list(iter_strings(load_json(file_path)))

        self.manifest.bind_source(file_path)

        with Session(self.store.engine) as session:
            for target in self.languages:
                if target == self.source_language:
                    continue

                self.logger.info(ConsoleFormatter.info(f"[{self.source_language} - {target}] Localization in progress..."))

                out_path: Path = output_path
                if output_path_tag is not None:
                    out_path = Path(sanitize_path(str(out_path), output_path_tag, target))

                if self.manifest.is_output_valid(out_path):
                    self.logger.info(
                        ConsoleFormatter.success(f"[{self.source_language} - {target}] Localization done."))
                    continue

                self.manifest.update_required = True

                translations: dict = {}
                for key, value in file_content_iter:
                    protected_value: str = self.engine.protect_text(value, self.patterns)
                    if self.engine.is_placeholder_only(protected_value):
                        translations[key] = value
                        continue

                    text_hash: str = compute_hash(normalize_text(protected_value))
                    cache: Optional[str] = self.store.lookup(session, target, text_hash)

                    if not cache:
                        try:
                            cache = self.translator.translate(self.source_language, target, protected_value, glossary_content)
                            cache = self.engine.unprotect_text(cache)
                            self.store.upsert(session, target, text_hash, cache)

                        except Exception as e:
                            print(f"Error translating text: {value}. Error: {e}")
                            continue

                    translations[key] = cache

                file_content_copy: dict = file_content.copy()
                for key, _ in file_content_iter:
                    set_at_path(file_content_copy, key, translations[key])

                write_json(str(out_path.parent), out_path.name, file_content_copy)

            session.commit()
        self.prune_store()
