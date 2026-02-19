import logging
import os
from abc import ABC, abstractmethod


class BaseRunner(ABC):
    def __init__(self) -> None:
        self.logger: logging.Logger = logging.getLogger(__name__)

    @abstractmethod
    def run(self, commit_message: str, changed_files: list[str], do_not_open_new_pull_request: bool = False) -> None:
        pass

    @staticmethod
    def get_env_variable(name: str) -> str:
        value: str | None

        try:
            value = os.getenv(name)
        except Exception as e:
            raise Exception(f"Error while getting environment variable {name}: {e}")

        if value is None:
            raise Exception(f"Environment variable {name} is missing.")

        return value
