import re
from pathlib import Path
from typing import Any, Optional

from transctl.console_formater import ConsoleFormatter
from transctl.core.configuration_manager import ConfigurationManager
from transctl.core.handlers.base_translation_handler import BaseTranslationHandler
from transctl.core.translation_run_manifest import TranslationRunManifest
from transctl.models.app_config import AppConfig
from transctl.utils.i_o import load_json, read_html, write_file
from transctl.utils.utils_suit import compute_hash, normalize_text, sanitize_path

from bs4 import BeautifulSoup
from bs4.element import Comment, Doctype, NavigableString, PageElement
from sqlalchemy.orm import Session


class HtmlTranslationTranslationHandler(BaseTranslationHandler):
    def __init__(self, cfg: ConfigurationManager, config: AppConfig, manifest: TranslationRunManifest) -> None:
        super().__init__(config, cfg)
        self.extension = ".html"
        self.manifest: TranslationRunManifest = manifest
        self._ignore: list[str] = ["style", "script", "head", "title", "meta", "link", "noscript"]
        self.patterns: list[re.Pattern[str]] = [self.placeholder_regex, self.email_regex, self.url_regex]

    def _is_translatable_text(self, node: NavigableString) -> bool:
        if isinstance(node, Doctype):
            return False

        if isinstance(node, Comment):
            return False

        if not node.strip():
            return False

        for p in node.parents:
            if getattr(p, "name", None) in self._ignore:
                return False

        return True

    def translate_file(self, file_path: Path, output_path: Path, glossary: Path | None = None,
                       output_path_tag: str | None = None) -> list[str]:

        self.logger.info(ConsoleFormatter.info(f"Processing path: {file_path}"))
        result_write_paths: list[str] = []

        if file_path.suffix != self.extension:
            raise ValueError(f"File {file_path} does not have the expected extension {self.extension}")

        glossary_content: dict[str, str] | None = None
        if glossary:
            glossary_content = load_json(glossary)

        file_content: str = read_html(file_path)
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
                    self.logger.info(ConsoleFormatter.success(f"[{self.source_language} - {target}] Localization done."))
                    continue

                self.manifest.update_required = True
                soup: Any = BeautifulSoup(file_content, "html.parser")

                nodes: list[PageElement] = []
                texts: list[str] = []

                for n in soup.descendants:
                    if isinstance(n, NavigableString) and self._is_translatable_text(n):
                        nodes.append(n)
                        texts.append(str(n))

                texts = [self.engine.protect_text(x, self.patterns) for x in texts]
                translations: list[str] = []

                for text in texts:
                    if self.engine.is_placeholder_only(text):
                        translations.append(self.engine.unprotect_text(text))
                        continue

                    text_hash: str = compute_hash(normalize_text(text))
                    cache: Optional[str] = self.store.lookup(session, target, text_hash)

                    if not cache:
                        try:
                            translation: str = str(
                                self.translator.translate(self.source_language, target, text, glossary_content)
                            )  # Enforce string as we only send a single string for translation

                            translation = self.engine.unprotect_text(translation)
                            self.store.upsert(session, target, text_hash, translation)
                            cache = translation

                        except Exception as e:
                            print(f"Error translating text: {self.engine.unprotect_text(text)}. Error: {e}")
                            continue

                    translations.append(cache)

                for node, tr in zip(nodes, translations):
                    node.replace_with(tr)

                out_html = str(soup)
                write_file(str(out_path.parent), out_path.name, out_html)
                result_write_paths.append(str(out_path))

                self.logger.info(ConsoleFormatter.success(f"[{self.source_language} - {target}] Localization done."))
            session.commit()

        self.prune_store()
        return result_write_paths
