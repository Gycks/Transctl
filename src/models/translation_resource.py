import os.path
import logging
from pathlib import Path
import glob
from typing_extensions import Self
from enum import Enum

from src.console_formater import ConsoleFormatter

from pydantic import BaseModel


TAG: str = "[source]"


class TranslationLayouts(str, Enum):
    BY_LANGUAGE = "by-language"
    ALONG_SIDED = "along-sided"


class TranslationResourceType(str, Enum):
    HTML = "html"
    JSON = "json"


class TranslationResource(BaseModel):
    """
    Represents a translation resource.

    Attributes:
        bucket (List(Tuple[Path, Path])): A list of tuples (input_path, output_path) to the translation resource.
        tag (str): The tag used in the output_path.
    """

    bucket: list[tuple[Path, Path]]
    tag: str = TAG

    @classmethod
    def from_obj(cls, resource: any, key: str | None = None) -> Self | None:
        """
        Creates a TranslationResource instance from a given resource configuration.

        Args:
            resource (any): The raw resource configuration.
            key (str | None): An optional key to specify to decode the source path in the resource configuration.

        Returns:
            An instance of TranslationResource with the parsed configuration or None if the configuration could not be parsed.
        """

        logger: logging.Logger = logging.getLogger(__name__)
        logger.info(ConsoleFormatter.info("Validating translation resources..."))

        if not isinstance(resource, dict):
            raise TypeError("Invalid resource configuration.")

        output_path: Path
        source_path: Path

        path: str | None = resource.get("path", None)
        layout: str | None = resource.get("layout", None)

        if path is None:
            raise ValueError(f"Key 'path' is missing. Translation resource: {resource}")

        if layout is not None and layout not in TranslationLayouts.__members__.values():
            raise ValueError(f"Invalid layout '{layout}'.")

        tag_indices: list[int] = []
        decoded_path: str = path
        if TAG in path:
            decoded_path = decoded_path.replace(TAG, key)
            start: int = 0
            while True:
                index = path.find(TAG, start)
                if index == -1:
                    break
                tag_indices.append(index)
                start = index + len(TAG)

        path_contents: list[str] = glob.glob(decoded_path, recursive=True)
        if len(path_contents) == 0:
            return None

        bucket: list[tuple[Path, Path]] = []
        for p in path_contents:
            if not os.path.isfile(p):
                continue

            source_path = Path(p)

            if len(tag_indices) > 0:
                for idx in tag_indices:
                    p = p[:idx] + TAG + p[idx + len(key):]

            output_path = Path(p)

            if layout == TranslationLayouts.BY_LANGUAGE.value:
                name: str = output_path.name
                output_path = output_path.parent.joinpath(name)

            if layout == TranslationLayouts.ALONG_SIDED.value or (layout is None and len(tag_indices) == 0):
                output_path = output_path.with_name(f"{TAG}_{output_path.name}")

            bucket.append((source_path, output_path))

        logger.info(ConsoleFormatter.success("Translation resources valid."))
        return cls(bucket=bucket)
