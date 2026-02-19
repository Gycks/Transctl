import os
import shlex
import subprocess
import urllib.parse
import urllib.request


def run_git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    # Text mode; capture for better errors
    proc = subprocess.run(
        ["git", *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and proc.returncode != 0:
        cmd = "git " + " ".join(shlex.quote(a) for a in args)
        raise Exception(f"Command failed ({proc.returncode}): {cmd}\n{proc.stderr.strip()}")
    return proc


def git_has_changes() -> bool:
    out = run_git("status", "--porcelain", check=True).stdout.strip()
    return bool(out)


def ensure_git_identity() -> None:
    # Avoid failing commits in CI due to missing identity
    name = os.getenv("GIT_AUTHOR_NAME", "transctl-ci")
    email = os.getenv("GIT_AUTHOR_EMAIL", "transctl-ci@example.invalid")
    run_git("config", "user.name", name, check=True)
    run_git("config", "user.email", email, check=True)


def commit_changes(commit_message: str, changed_files: list[str]) -> bool:
    for file in changed_files:
        run_git("add", file, check=True)

    # run_git("add", "-A", check=True)

    # If nothing staged, skip commit
    diff = run_git("diff", "--cached", "--name-only", check=True).stdout.strip()
    if not diff:
        return False
    ensure_git_identity()
    run_git("commit", "-m", commit_message, check=True)
    return True


def get_origin_url() -> str:
    return run_git("remote", "get-url", "origin", check=True).stdout.strip()


def set_origin_url(url: str) -> None:
    run_git("remote", "set-url", "origin", url, check=True)


def push_head_to_branch(branch: str) -> None:
    run_git("push", "origin", f"HEAD:refs/heads/{branch}", check=True)


def _gitlab_base_repo_url() -> str:
    """
    USE CI_REPOSITORY_URL (GitLab gives a correct repo URL in CI),
    otherwise build from CI_SERVER_HOST + CI_PROJECT_PATH.
    Returns a https://host/namespace/project.git URL WITHOUT credentials.
    """

    repo_url = os.getenv("CI_REPOSITORY_URL")
    if repo_url:
        # Example: https://gitlab-ci-token:xxxxx@gitlab.com/group/project.git
        parsed = urllib.parse.urlsplit(repo_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise Exception(f"Unsupported CI_REPOSITORY_URL: {repo_url}")

        # Strip any userinfo (everything before '@')
        netloc = parsed.netloc.split("@", 1)[-1]

        # Normalize path and remove any trailing slash
        path = parsed.path.rstrip("/")

        return urllib.parse.urlunsplit((parsed.scheme, netloc, path, "", ""))

    host = os.getenv("CI_SERVER_HOST")
    project_path = os.getenv("CI_PROJECT_PATH")
    if not host or not project_path:
        raise Exception("Missing CI_REPOSITORY_URL and also missing CI_SERVER_HOST/CI_PROJECT_PATH")

    project_path = project_path.strip("/")
    return f"https://{host}/{project_path}.git"


def gitlab_authed_origin_url(token: str) -> str:
    """
    Builds a correct authenticated origin URL for pushing.
    """
    base = _gitlab_base_repo_url()
    parsed = urllib.parse.urlsplit(base)

    username = os.getenv("GL_TOKEN_USERNAME", "oauth2")
    userinfo = f"{urllib.parse.quote(username, safe='')}:{urllib.parse.quote(token, safe='')}"
    netloc = f"{userinfo}@{parsed.netloc}"

    return urllib.parse.urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
