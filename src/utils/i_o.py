from typing import Any
from pathlib import Path
import json
import os

import tomli_w


def read_html(file: str | Path) -> str:
    if not os.path.isfile(file):
        raise FileNotFoundError(file)

    base_name: str = os.path.basename(file)
    if not base_name.endswith(".html"):
        raise ValueError(f"File {file} is not a valid html file.")

    data: str
    with open(file, 'r', encoding='utf-8') as f:
        data = f.read()

    return data


def load_json(file: str | Path) -> dict[str, Any]:
    if not os.path.isfile(file):
        raise FileNotFoundError(file)

    base_name: str = os.path.basename(file)
    if not base_name.endswith(".json"):
        raise ValueError(f"File {file} is not a valid json file.")

    data: Any
    with open(file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Invalid File Format. Expected a JSON object at top level")

    return data


def write_json(output_dir: str, filename: str, data: dict):
    path: str = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_file(output_dir: str, filename: str, data: str):
    path: str = os.path.join(output_dir, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(data)


def write_toml(path: str, data):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(tomli_w.dumps(data))
