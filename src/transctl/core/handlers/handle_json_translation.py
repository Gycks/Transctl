import re
from pathlib import Path
from typing import Any, Optional

from transctl.console_formater import ConsoleFormatter
from transctl.core.configuration_manager import ConfigurationManager
from transctl.core.handlers.base_translation_handler import BaseTranslationHandler
from transctl.core.translation_run_manifest import TranslationRunManifest
from transctl.models.app_config import AppConfig
from transctl.utils.i_o import load_json, write_json
from transctl.utils.utils_suit import (
    compute_hash,
    iter_strings,
    normalize_text,
    sanitize_path,
    set_at_path,
)

from sqlalchemy.orm import Session


class JsonTranslationTranslationHandler(BaseTranslationHandler):

    def __init__(self, cfg: ConfigurationManager, config: AppConfig, manifest: TranslationRunManifest) -> None:
        super().__init__(config, cfg)
        self.extension = ".json"
        self.manifest: TranslationRunManifest = manifest
        self.patterns: list[re.Pattern[str]] = [self.placeholder_regex, self.email_regex, self.url_regex]

    def translate_file(self, file_path: Path, output_path: Path, glossary: Path | None = None,
                       output_path_tag: str | None = None) -> list[str]:

        self.logger.info(ConsoleFormatter.info(f"Processing path: {file_path}"))
        result_write_paths: list[str] = []

        if file_path.suffix != self.extension:
            raise ValueError(f"File {file_path} does not have the expected extension {self.extension}")

        glossary_content: dict[str, str] | None = None
        if glossary:
            glossary_content = load_json(glossary)

        file_content: dict[Any, Any] = load_json(file_path)
        file_content_iter: list[Any] = list(iter_strings(load_json(file_path)))

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

                translations: dict[Any, Any] = {}
                for key, value in file_content_iter:
                    protected_value: str = self.engine.protect_text(value, self.patterns)
                    if self.engine.is_placeholder_only(protected_value):
                        translations[key] = value
                        continue

                    text_hash: str = compute_hash(normalize_text(protected_value))
                    cache: Optional[str] = self.store.lookup(session, target, text_hash)

                    if not cache:
                        try:
                            translation: str = str(
                                self.translator.translate(self.source_language, target, protected_value, glossary_content)
                            )  # Enforce string as we only send a single string for translation

                            translation = self.engine.unprotect_text(translation)
                            self.store.upsert(session, target, text_hash, translation)
                            cache = translation

                        except Exception as e:
                            print(f"Error translating text: {value}. Error: {e}")
                            continue

                    translations[key] = cache

                file_content_copy: dict[Any, Any] = file_content.copy()
                for key, _ in file_content_iter:
                    set_at_path(file_content_copy, key, translations[key])

                write_json(str(out_path.parent), out_path.name, file_content_copy)
                result_write_paths.append(str(out_path))

            session.commit()
        self.prune_store()
        return result_write_paths
