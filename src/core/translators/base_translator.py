from abc import ABC, abstractmethod
from typing import List, Dict


class BaseTranslator(ABC):
    def __init__(self, supported_languages: Dict[str, str], tag: str):
        self.supported_languages: Dict[str, str] = supported_languages
        self.tag: str = tag

    @abstractmethod
    def translate(self, source: str, target: str, text: str | List[str], glossary: Dict[str, str] | None = None) -> str | List[str]:
        pass
