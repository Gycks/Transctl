import os

from transctl.ci_runners.base_runner import BaseRunner
from transctl.ci_runners.gitlab_runner import GitLabRunner
from transctl.models.ci_runner_config import CIPlatform


class CIRunnerFactory:
    runner_mappings = {
        CIPlatform.GITLAB_CI: GitLabRunner
    }

    @staticmethod
    def detect_ci_platform() -> CIPlatform:
        for platform in CIPlatform:
            if os.getenv(platform.value) == "true":
                return platform

        raise ValueError("Invalid CI Platform.")

    @staticmethod
    def get_runner() -> BaseRunner:
        platform: CIPlatform = CIRunnerFactory.detect_ci_platform()
        return CIRunnerFactory.runner_mappings[platform]()
