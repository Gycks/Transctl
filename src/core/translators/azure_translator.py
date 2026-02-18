import re
import html

from src.core.constants.supported_languages import SUPPORTED_LANGUAGES_AZURE
from src.models.engine_config import AzureTranslateEngine
from src.core.translators.base_translator import BaseTranslator

from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.text import TextTranslationClient
from azure.ai.translation.text.models import TranslatedTextItem


class AzureTranslator(BaseTranslator):
    def __init__(self, config: AzureTranslateEngine):
        super().__init__(SUPPORTED_LANGUAGES_AZURE, config.protection_tag)

        self.supported_languages = SUPPORTED_LANGUAGES_AZURE
        self._config = config
        self._client: TextTranslationClient = TextTranslationClient(
            region=config.region,
            credential=AzureKeyCredential(config.api_key)
        )

    def _apply_dynamic_glossary(self, text: str, glossary: dict[str, str]) -> str:
        protected_span_re = re.compile(
            rf'<span[^>]*\bclass="{re.escape(self.tag)}"[^>]*>.*?</span>',
            flags=re.IGNORECASE | re.DOTALL,
        )

        chunks = protected_span_re.split(text)
        protected_chunks = protected_span_re.findall(text)

        word_re = re.compile(r"\w+|\W+", re.UNICODE)

        def replace_words(chunk: str) -> str:
            parts = word_re.findall(chunk)
            for i, tok in enumerate(parts):
                if re.fullmatch(r"\w+", tok, flags=re.UNICODE):
                    repl = glossary.get(tok)
                    if repl is not None:
                        parts[i] = f'<span class="{self.tag}">{html.escape(repl, quote=False)}</span>'
            return "".join(parts)

        # Rebuild.
        out = []
        for i, unprot in enumerate(chunks):
            out.append(replace_words(unprot))
            if i < len(protected_chunks):
                out.append(protected_chunks[i])

        return "".join(out)

    def translate(self, source: str, target: str, text: str | list[str], glossary: dict[str, str] | None = None) -> str | list[str]:
        source_code: str | None = self.supported_languages.get(source, None)
        target_code: str | None = self.supported_languages.get(target, None)

        if source_code is None:
            raise ValueError(f"Language {source} is not supported.")

        if target_code is None:
            raise ValueError(f"Language {target} is not supported.")

        is_list: bool = isinstance(text, list)
        if glossary is not None:
            if is_list:
                text = [self._apply_dynamic_glossary(t, glossary) for t in text]
            else:
                text = self._apply_dynamic_glossary(text, glossary)

        result: list[TranslatedTextItem] = self._client.translate(
            body=text if is_list else [text],
            to_language=[target_code],
            from_language=source_code,
            text_type="html"
        )

        response = [item.translations[0].text for item in result]
        return response if is_list else response[0]
