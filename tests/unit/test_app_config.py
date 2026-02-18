import os
import pytest

from src.core.errors.configuration_errors import ConfigurationError
import src.core.constants.app as app_constants
from src.models.app_config import AppConfig
from src.models.translation_resource import TranslationResourceType


def _write_cfg(tmp_path, name: str, toml_text: str) -> str:
    p = tmp_path / name
    p.write_text(toml_text.strip() + "\n", encoding="utf-8")
    return str(p)


def test_from_file_missing_file_raises_file_not_found(tmp_path):
    missing = tmp_path / f"missing.{app_constants.APP_NAME}.toml"
    with pytest.raises(FileNotFoundError, match="No Configuration found at"):
        AppConfig.from_file(str(missing))


def test_from_file_wrong_suffix_raises_configuration_error(tmp_path):
    path = _write_cfg(tmp_path, "config.not-the-right-suffix.toml", """
        [locale]
        source = "en"
        targets = ["fr"]

        [engine]
        provider = "deepl"
        
        [resources.html]
        dirs = [{ path = "" }]
    """)

    with pytest.raises(ConfigurationError, match=r"must end with"):
        AppConfig.from_file(path)


def test_from_file_success_with_layout_omitted(monkeypatch, tmp_path):

    os.environ["DEEPL_API_KEY"] = "test-key"
    path = _write_cfg(tmp_path, f"config.{app_constants.APP_NAME}.toml", """
        [locale]
        source = "en"
        targets = ["fr"]

        [engine]
        provider = "deepl"

        [resources.html]
        dirs = [
            { path = "content" },
        ]
    """)

    cfg = AppConfig.from_file(path)
    assert cfg.source == "en"
    assert cfg.targets == ["fr"]
    assert cfg.resources is not None
    assert TranslationResourceType("html") in cfg.resources
    assert len(cfg.resources[TranslationResourceType("html")]) == 0


def test_from_file_success_with_valid_layout(monkeypatch, tmp_path):
    os.environ["DEEPL_API_KEY"] = "test-key"
    path = _write_cfg(tmp_path, f"config.{app_constants.APP_NAME}.toml", """
        [locale]
        source = "en"
        targets = ["fr"]

        [engine]
        provider = "deepl"

        [resources.html]
        dirs = [
            { path = "content", layout = "by-language" },
        ]
    """)

    cfg = AppConfig.from_file(path)
    assert cfg.resources is not None
    assert len(cfg.resources[TranslationResourceType("html")]) == 0


def test_from_file_unknown_resource_type_raises_configuration_error(monkeypatch, tmp_path):
    os.environ["DEEPL_API_KEY"] = "test-key"
    path = _write_cfg(tmp_path, f"config.{app_constants.APP_NAME}.toml", """
        [locale]
        source = "en"
        targets = ["fr"]

        [engine]
        provider = "deepl"

        [resources.xml]
        dirs = [
            { path = "content" },
        ]
    """)

    with pytest.raises(ConfigurationError):
        AppConfig.from_file(path)


def test_from_file_invalid_layout_raises_configuration_error(monkeypatch, tmp_path):
    os.environ["DEEPL_API_KEY"] = "test-key"
    path = _write_cfg(tmp_path, f"config.{app_constants.APP_NAME}.toml", """
        [locale]
        source = "en"
        targets = ["fr"]

        [engine]
        provider = "deepl"

        [resources.html]
        dirs = [
            { path = "content", layout = "not-a-real-layout" },
        ]
    """)

    with pytest.raises(ConfigurationError):
        AppConfig.from_file(path)


def test_from_file_unknown_engine_provider_raises_configuration_error(monkeypatch, tmp_path):
    path = _write_cfg(tmp_path, f"config.{app_constants.APP_NAME}.toml", """
        [locale]
        source = "en"
        targets = ["fr"]

        [engine]
        provider = "bogus"

        [resources.html]
        dirs = [
            { path = "content" },
        ]
    """)

    with pytest.raises(ConfigurationError):
        AppConfig.from_file(path)
