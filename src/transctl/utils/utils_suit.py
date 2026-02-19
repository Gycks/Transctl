import hashlib
import re
from typing import Any, Iterator, Tuple, Union


PathPart = Union[str, int]
Path = Tuple[PathPart, ...]


def normalize_text(text: str) -> str:
    """
    Normalize text by replacing newlines, stripping, and collapsing whitespace.

    Args:
        text (str): The input text to normalize.

    Returns:
        str: The normalized text.
    """
    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.strip()
    text = re.sub(r"[ \t]+", " ", text)
    return text


def compute_hash(value_: str) -> str:
    """
    Computes the SHA-256 hash of the given input.

    Args:
        value_ (str): The input value_ to hash.

    Returns:
        str: The hexadecimal representation of the hash.
    """

    return hashlib.sha256(value_.encode("utf-8")).hexdigest()


def sanitize_path(path: str, tag: str, value_: str) -> str:
    """
    Sanitizes a given path by replacing the path pattern's tag the corresponding new tag.

    Args:
        path (str): The path to sanitize.
        tag (str): The path pattern's tag.
        value_ (str): The value to replace the path pattern's tag with.

    Returns:
        The sanitized path.
    """

    return path.replace(tag, value_)


def set_at_path(obj: Any, path: Path, new_value: Any) -> None:
    """
    Navigates a nested JSON-like structure using a tuple path
    (keys and/or list indices) and replaces the value at that
    location with new_value.
    """
    cur = obj
    for part in path[:-1]:
        cur = cur[part]
    cur[path[-1]] = new_value


def iter_strings(obj: Any, path: Path = ()) -> Iterator[tuple[Path, str]]:
    """
    Recursively traverses a nested JSON-like structure (dicts/lists)
    and yields (path, string_value) for every string found.
    The path is a tuple of keys/indices describing where the string
    is located within the original structure.

    Args:
        obj: (Any): The JSON-like object to traverse (can be dict, list, or str).
        path (Optional[`Path`]): A tuple representing the location of a value inside a nested
                                JSON-like structure.

    Returns:
        An iterator of tuples, where each tuple contains:
        - `Path`: A tuple representing the location of a string value within the original structure.
        - `str`: The string value found at that location.
    """

    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_strings(v, path + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, path + (i,))
    elif isinstance(obj, str):
        yield (path, obj)
