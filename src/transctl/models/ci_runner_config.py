from enum import Enum

from pydantic import BaseModel


class CIPlatform(str, Enum):
    GITHUB_ACTIONS = "GITHUB_ACTIONS"
    GITLAB_CI = "GITLAB_CI"


class GitLabContext(BaseModel):
    token: str
    api_v4: str
    project_id: str
    mr_iid: str
    mr_source_branch: str
    default_branch: str
