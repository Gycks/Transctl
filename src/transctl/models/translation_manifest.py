from pydantic import BaseModel


class TREntry(BaseModel):
    outputs: dict[str, str] = {}


class TranslationManifest(BaseModel):
    version: int = 1
    sources: dict[str, TREntry] = {}
