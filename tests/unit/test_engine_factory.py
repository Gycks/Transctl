from src.models.engine_config import (
    Engine,
    DeepLEngine,
    AzureTranslateEngine,
    AnthropicEngine,
)
from src.core.factory.engine_factory import EngineFactory

import pytest
from pydantic import ValidationError


# ------------------------------------------------------------------
# Invalid engine creation
# ------------------------------------------------------------------
def test_get_engine_rejects_non_dict():
    factory = EngineFactory()

    with pytest.raises(TypeError):
        factory.get_engine("not-a-dict")


def test_get_engine_missing_provider():
    factory = EngineFactory()

    with pytest.raises(ValueError):
        factory.get_engine({})


def test_get_engine_invalid_provider():
    factory = EngineFactory()

    with pytest.raises(ValueError):
        factory.get_engine({"provider": "not-real"})


def test_missing_deepl_api_key(monkeypatch):
    factory = EngineFactory()

    monkeypatch.delenv("DEEPL_API_KEY", raising=False)

    with pytest.raises(ValueError):
        factory.get_engine({"provider": Engine.DeepL})


def test_missing_azure_api_key(monkeypatch):
    factory = EngineFactory()

    monkeypatch.delenv("AZURE_TRANSLATE_API_KEY", raising=False)

    with pytest.raises(ValueError):
        factory.get_engine({"provider": Engine.Azure})


def test_missing_azure_region(monkeypatch):
    factory = EngineFactory()

    monkeypatch.setenv("AZURE_TRANSLATE_API_KEY", "test-api-key")

    with pytest.raises(ValidationError):
        factory.get_engine({"provider": Engine.Azure})


# ------------------------------------------------------------------
# Successful engine creation
# ------------------------------------------------------------------

def test_create_deepl_engine(monkeypatch):
    monkeypatch.setenv("DEEPL_API_KEY", "test-key")

    factory = EngineFactory()
    engine = factory.get_engine({"provider": Engine.DeepL})

    assert isinstance(engine, DeepLEngine)
    assert engine.api_key == "test-key"
    assert engine.provider == Engine.DeepL


def test_create_azure_engine(monkeypatch):
    monkeypatch.setenv("AZURE_TRANSLATE_API_KEY", "azure-key")

    factory = EngineFactory()
    engine = factory.get_engine({"provider": Engine.Azure, "region": "some-region"})

    assert isinstance(engine, AzureTranslateEngine)
    assert engine.api_key == "azure-key"
    assert engine.provider == Engine.Azure

# ------------------------------------------------------------------
# Ensure API key injection overrides input
# ------------------------------------------------------------------


def test_api_key_is_overwritten_by_env(monkeypatch):
    monkeypatch.setenv("DEEPL_API_KEY", "correct-key")

    factory = EngineFactory()

    engine = factory.get_engine({
        "provider": Engine.DeepL,
        "api_key": "wrong-key"
    })

    assert engine.api_key == "correct-key"
