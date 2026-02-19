import json
import os
import random
import urllib.parse
import urllib.request
from typing import Any, Optional

from transctl.ci_runners.base_runner import BaseRunner
from transctl.console_formater import ConsoleFormatter
from transctl.core.constants.app import APP_NAME
from transctl.models.ci_runner_config import GitLabContext
from transctl.utils.git_helpers import (commit_all, git_has_changes, gitlab_authed_origin_url,
                                        push_head_to_branch, set_origin_url)


class GitLabRunner(BaseRunner):
    def __init__(self) -> None:
        super().__init__()

        self.context: GitLabContext = GitLabContext(
            token=self.get_env_variable("GL_TOKEN"),
            api_v4=self.get_env_variable("CI_API_V4_URL").strip("/"),
            project_id=self.get_env_variable("CI_PROJECT_ID"),
            mr_iid=self.get_env_variable("CI_MERGE_REQUEST_IID"),
            mr_source_branch=self.get_env_variable("CI_MERGE_REQUEST_SOURCE_BRANCH_NAME"),
            default_branch=self.get_env_variable("CI_DEFAULT_BRANCH")
        )

    def _construct_api(self, method: str, path: str,
                       query: Optional[dict[str, str]] = None, json_body: Optional[dict[str, Any]] = None) -> Any:

        url = f"{self.context.api_v4}{path}"
        if query:
            url = f"{url}?{urllib.parse.urlencode(query)}"

        data: Optional[bytes] = None
        headers = {
            "PRIVATE-TOKEN": self.context.token,
            "Accept": "application/json",
        }
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url=url, method=method, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                if not raw:
                    return None
                return json.loads(raw)

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise Exception(f"GitLab API error {e.code} {e.reason} for {method} {url}\n{body}")

    def _find_open_mr_by_source_branch(self, source_branch: str) -> Any:
        mrs = self._construct_api(
            "GET",
            f"/projects/{self.context.project_id}/merge_requests",
            query={"state": "opened", "source_branch": source_branch},
        )
        if isinstance(mrs, list) and mrs:
            return mrs[0]

        return None

    def _create_mr(self, source_branch: str, target_branch: str, title: str, description: str = "") -> Any:
        return self._construct_api(
            "POST",
            f"/projects/{self.context.project_id}/merge_requests",
            json_body={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description,
                # You can add: "remove_source_branch": True, "squash": True, etc.
            },
        )

    def run(self, commit_message: str, do_not_open_new_pull_request: bool = False) -> None:
        self.logger.info(ConsoleFormatter.info("Starting GitLab CI runner..."))

        if not git_has_changes():
            self.logger.info(ConsoleFormatter.success("No changes detected. Nothing to commit."))
            return

        target_branch: str
        if do_not_open_new_pull_request:
            target_branch = self.context.mr_source_branch

            self.logger.warning(
                ConsoleFormatter.warning(f"Running with option 'no-pull-request'. Will push to current branch: {target_branch}"))
        else:
            short_sha: str = (os.getenv("CI_COMMIT_SHORT_SHA") or os.getenv("CI_COMMIT_SHA", "")[:8] or "unknown")
            target_branch = f"transctl/ci/{short_sha}"

            self.logger.warning(ConsoleFormatter.warning(
                f"Running with option 'pull-request'. Will push to new branch: {target_branch}"))

        committed = commit_all(commit_message=commit_message)
        if not committed:
            self.logger.warning(ConsoleFormatter.warning("No changes staged for commit. Skipping commit and push."))
            return

        authed_origin: str = gitlab_authed_origin_url(self.context.token)
        set_origin_url(authed_origin)
        push_head_to_branch(target_branch)

        if not do_not_open_new_pull_request:
            if not self._find_open_mr_by_source_branch(target_branch):
                self._create_mr(
                    source_branch=target_branch,
                    target_branch=self.context.default_branch,
                    title=f"Update {APP_NAME.upper()} artifacts -- {random.random():.4f}",
                    description=f"This MR was automatically created by {APP_NAME.upper()}.",
                )

        self.logger.info(ConsoleFormatter.success("GitLab CI runner finished successfully."))
