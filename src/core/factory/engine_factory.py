import os

from src.models.engine_config import *


class EngineFactory:
    def __init__(self):
        """
        Factory class responsible for creating instances of translation engines based on the provided configuration.
        """

        self.API_KEY_ENV: dict[str, str] = {
            "deepl": "DEEPL_API_KEY",
            "azure": "AZURE_TRANSLATE_API_KEY"
        }

    @staticmethod
    def get_engine(engine_config: any) -> EngineConfig:
        """
        Creates an instance of a translation engine based on the provided configuration.

        Args:
            engine_config (any): The raw engine configuration.

        Returns:
            An instance of EngineConfig corresponding for the specified provider.
        """

        if not isinstance(engine_config, dict):
            raise TypeError("Invalid engine configuration.")

        provider: str | None = engine_config.get("provider", None)
        if not provider or provider is None:
            raise ValueError("No provider found in the engine configuration.")

        env_name: str = EngineFactory().API_KEY_ENV.get(provider)
        api_key: str = os.getenv(env_name) if env_name else None
        if env_name and not api_key:
            raise ValueError(
                f"Missing API key. Set {env_name} in your environment."
            )

        engine_config_copy: dict[str, any] = engine_config.copy()
        engine_config_copy["api_key"] = api_key
        match provider:
            case Engine.DeepL:
                return DeepLEngine.model_validate(engine_config_copy)

            case Engine.Azure:
                return AzureTranslateEngine.model_validate(engine_config_copy)

            case _:
                raise ValueError(f"Invalid provider: {provider}.")
