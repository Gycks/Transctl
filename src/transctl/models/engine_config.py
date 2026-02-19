import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Annotated, Any, Literal, Self, Union

from transctl.utils.utils_suit import normalize_text

from pydantic import BaseModel, Field, ValidationError, model_validator


class Engine(str, Enum):
    DeepL = "deepl"
    Azure = "azure"
    Anthropic = "anthropic"
    OpenAI = "open-ai"


# ============================================== #
# ===== TRANSLATION ENGINES CONFIGURATIONS ===== #
# ============================================== #
class TranslatorBase(BaseModel, ABC):
    api_key: str = Field(title="API Key", json_schema_extra={"visible": False})
    protection_tag: str

    @model_validator(mode="before")
    @classmethod
    def disallow_base(cls, data: Any) -> Any:
        if cls is TranslatorBase:
            raise TypeError(
                "TranslatorBase is abstract and cannot be instantiated. "
            )
        return data

    @model_validator(mode="after")
    def _validate_api_key(self) -> Self:
        if not self.api_key:
            raise ValidationError("Engine API key is not set.")
        return self

    @abstractmethod
    def protect_text(self, text: str, patterns: list[re.Pattern[str]]) -> str:
        """
        Protects text for translation by wrapping matches of the given patterns in specified tags.

        Args:
            text (str): The input text to protect.
            patterns (list[re.Pattern[str]]): A list of compiled regular expression patterns to match-text that should be protected.

        Returns:
            str: The text with protected segments wrapped in tags.
        """
        pass

    @abstractmethod
    def unprotect_text(self, text: str) -> str:
        """
        Unprotects text by removing the protection tags.

        Args:
            text (str): The input text to unprotect.

        Returns:
            str: The text with protection tags removed.
        """
        pass

    @abstractmethod
    def is_placeholder_only(self, protected_text: str) -> bool:
        """
        Checks if the protected text contains only placeholders.

        Args:
            protected_text (str): The protected text to check.

        Returns:
            bool: True if the protected text contains only placeholders, False otherwise.
        """
        pass


# ====================================== #
# ===== DEEPL ENGINE CONFIGURATION ===== #
# ====================================== #
class DeepLEngine(TranslatorBase):
    provider: Literal[Engine.DeepL] = Field(title="Provider", json_schema_extra={"visible": False}, default=Engine.DeepL)
    protection_tag: str = Field(json_schema_extra={"visible": False}, default="keep")

    def protect_text(self, text: str, patterns: list[re.Pattern[str]]) -> str:
        def _sub(match: re.Match[str]) -> str:
            return f"<{self.protection_tag}>{match.group(0)}</{self.protection_tag}>"

        out = text
        for pattern in patterns:
            out = re.sub(pattern, _sub, out)

        return out

    def unprotect_text(self, text: str) -> str:
        return re.sub(
            rf"</?{re.escape(self.protection_tag)}>",
            "",
            text
        )

    def is_placeholder_only(self, protected_text: str) -> bool:
        remainder = re.sub(
            rf"<{re.escape(self.protection_tag)}>\s*.*?\s*</{re.escape(self.protection_tag)}>",
            "",
            protected_text,
            flags=re.DOTALL,
        )
        return normalize_text(remainder) == ""


# ====================================== #
# ===== AZURE ENGINE CONFIGURATION ===== #
# ====================================== #
class AzureTranslateEngine(TranslatorBase):
    provider: Literal[Engine.Azure] = Field(title="Provider", json_schema_extra={"visible": False}, default=Engine.Azure)
    region: str = Field(title="Region")
    protection_tag: str = Field(json_schema_extra={"visible": False}, default="notranslate")

    @model_validator(mode="after")
    def _validate_region(self) -> Self:
        if not self.region:
            raise ValidationError("Azure region is not set.")
        return self

    def protect_text(self, text: str, patterns: list[re.Pattern[str]]) -> str:
        def _sub(match: re.Match[str]) -> str:
            return f'<span class="{self.protection_tag}">{match.group(0)}</span>'

        out = text
        for pattern in patterns:
            out = re.sub(pattern, _sub, out)

        return out

    def unprotect_text(self, text: str) -> str:
        if not text:
            return text

        pattern = re.compile(
            rf'<span\s+class="{re.escape(self.protection_tag)}"\s*>(.*?)</span>',
            flags=re.IGNORECASE | re.DOTALL,
        )

        return pattern.sub(r"\1", text)

    def is_placeholder_only(self, protected_text: str) -> bool:
        remainder = re.sub(
            rf'<span[^>]*class="{re.escape(self.protection_tag)}"[^>]*>\s*.*?\s*</span>',
            "",
            protected_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        return normalize_text(remainder) == ""


# ======================================= #
# ===== CLAUDE ENGINE CONFIGURATION ===== #
# ======================================= #
class AnthropicEngine(TranslatorBase):
    provider: Literal[Engine.Anthropic] = Field(title="Provider", json_schema_extra={"visible": False}, default=Engine.Anthropic)
    protection_tag: str = Field(json_schema_extra={"visible": False}, default="notranslate")
    model: str = Field(title="Model")

    @model_validator(mode="after")
    def _validate_model(self) -> Self:
        if not self.model:
            raise ValidationError("No claude model specified.")

        return self

    def protect_text(self, text: str, patterns: list[re.Pattern[str]]) -> str:
        raise NotImplementedError

    def unprotect_text(self, text: str) -> str:
        raise NotImplementedError

    def is_placeholder_only(self, protected_text: str) -> bool:
        raise NotImplementedError


# ================================================== #
# ===== END TRANSLATION ENGINES CONFIGURATIONS ===== #
# ================================================== #


"""
EngineConfig

Configuration for the translation engine to use.
The selected engine is determined by the `provider` field.
"""
EngineConfig = Annotated[Union[
    DeepLEngine, AzureTranslateEngine,
    AnthropicEngine
], Field(discriminator="provider")]
