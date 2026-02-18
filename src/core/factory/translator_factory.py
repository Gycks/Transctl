from typing import Callable

from src.core.translators.base_translator import BaseTranslator
from src.core.translators.azure_translator import AzureTranslator
from src.core.translators.deepl_translator import DeepLTranslator
from src.models.engine_config import *


TranslatorCtor = Callable[[EngineConfig], BaseTranslator]


class TranslatorFactory:
    def __init__(self):
        self.translator_mapping: dict[EngineConfig, TranslatorCtor] = {
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

        return TranslatorFactory().translator_mapping[engine_config.provider](engine_config)
