from typing import Callable, TypeAlias

from transctl.core.translators.azure_translator import AzureTranslator
from transctl.core.translators.base_translator import BaseTranslator
from transctl.core.translators.deepl_translator import DeepLTranslator
from transctl.models.engine_config import Engine, EngineConfig


TranslatorCtor: TypeAlias = Callable[[EngineConfig], BaseTranslator]


class TranslatorFactory:
    translator_mapping = {
        Engine.DeepL: DeepLTranslator,
        Engine.Azure: AzureTranslator
    }

    @staticmethod
    def get_translator(engine_config: EngineConfig) -> BaseTranslator:
        """
        Creates an instance of a translator based on the provided engine configuration.

        Args:
            engine_config (EngineConfig): The engine configuration.

        Returns:
            An instance of BaseTranslator corresponding for the specified provider.
        """

        ctor: TranslatorCtor | None = TranslatorFactory.translator_mapping.get(engine_config.provider)
        if ctor is None:
            raise ValueError(f"Unsupported provider: {engine_config.provider}")
        return ctor(engine_config)
