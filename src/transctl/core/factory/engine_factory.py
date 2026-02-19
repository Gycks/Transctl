import os
from typing import Any

from transctl.models.engine_config import AzureTranslateEngine, DeepLEngine, Engine, EngineConfig


class EngineFactory:
    """
    Factory class responsible for creating instances of translation engines based on the provided configuration.
    """

    API_KEY_ENV: dict[str, str] = {
        "deepl": "DEEPL_API_KEY",
        "azure": "AZURE_TRANSLATE_API_KEY"
    }

    @staticmethod
    def get_engine(engine_config: dict[Any, Any]) -> EngineConfig:
        """
        Creates an instance of a translation engine based on the provided configuration.

        Args:
            engine_config (any): The raw engine configuration.

        Returns:
            An instance of EngineConfig corresponding for the specified provider.
        """

        if not isinstance(engine_config, dict):
            raise TypeError("Invalid engine configuration.")

        provider: str = engine_config.get("provider", "")
        if not provider or provider is None:
            raise ValueError("No provider found in the engine configuration.")

        env_name: str = EngineFactory.API_KEY_ENV.get(provider, "")
        api_key: str | None = os.getenv(env_name) if env_name else None
        if env_name and not api_key:
            raise ValueError(
                f"Missing API key. Set {env_name} in your environment."
            )

        engine_config_copy: dict[str, Any] = engine_config.copy()
        engine_config_copy["api_key"] = api_key
        match provider:
            case Engine.DeepL:
                return DeepLEngine.model_validate(engine_config_copy)

            case Engine.Azure:
                return AzureTranslateEngine.model_validate(engine_config_copy)

            case _:
                raise ValueError("Invalid provider.")
