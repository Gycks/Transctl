from typing import List, Dict

from src.core.constants.supported_languages import SUPPORTED_LANGUAGES_DEEPL
from src.core.translators.base_translator import BaseTranslator
from src.models.engine_config import DeepLEngine

import deepl
from deepl import TextResult, GlossaryInfo


class DeepLTranslator(BaseTranslator):
    def __init__(self, config: DeepLEngine):
        super().__init__(SUPPORTED_LANGUAGES_DEEPL, config.protection_tag)
        self._translator: deepl.Translator = deepl.Translator(config.api_key)

    def translate(self, source: str, target: str, text: str | List[str], glossary: Dict[str, str] | None = None) -> str | List[str]:
        source_code: str | None = self.supported_languages.get(source, None)
        target_code: str | None = self.supported_languages.get(target, None)

        if source_code is None:
            raise ValueError(f"Language {source} is not supported.")

        if target_code is None:
            raise ValueError(f"Language {target} is not supported.")

        glos: GlossaryInfo | None = None
        if glossary is not None:
            glos = self._translator.create_glossary(
                name=f"glos-{source_code}-{target_code}",
                source_lang=source_code,
                target_lang=target_code,
                entries=glossary
            )

        result: TextResult | list[TextResult]
        try:
            result = self._translator.translate_text(
                text,
                source_lang=source_code,
                target_lang=target_code,
                tag_handling="xml",
                ignore_tags=self.tag,
                glossary=glos
            )
        except deepl.DeepLException as e:
            raise RuntimeError(f"Translation failed: {e}")
        finally:
            if glos is not None:
                self._translator.delete_glossary(glos)

        if isinstance(result, list):
            return [res.text for res in result]

        return result.text
