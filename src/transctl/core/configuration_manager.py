import os
from pathlib import Path
from typing import Any

import transctl.core.constants.app as app_constants
from transctl.models.app_config import AppConfig


class ConfigurationManager:
    def __init__(self, cold_start: bool = False) -> None:
        self._base_path: Path = Path(__file__).parent
        self._work_dir: Path = self._base_path.parent.joinpath(f".{app_constants.APP_NAME}")
        self._config_path: Path = self._base_path.joinpath(f".{app_constants.APP_NAME}.toml")
        self.configuration: AppConfig | None = None

        os.makedirs(self._work_dir, exist_ok=True)

        if not cold_start:
            self._load_configuration()

    def _load_configuration(self) -> None:
        if self.configuration is not None:
            return

        if not self._config_path.exists():
            raise FileNotFoundError("Configuration file not.")

        self.configuration = AppConfig.from_file(str(self._config_path))

    def get_working_directory(self) -> Path:
        return self._work_dir

    def does_config_exist(self) -> bool:
        return self._config_path.exists()

    def save_config(self, config: Any) -> None:
        if not self._config_path.parent.exists():
            self._config_path.parent.mkdir(parents=True)

        with open(self._config_path, "w") as fs:
            fs.write(config)

    def get_store_path(self) -> Path:
        return self._work_dir.joinpath("store.sqlite")

    @property
    def config_path(self) -> Path:
        return self._config_path
