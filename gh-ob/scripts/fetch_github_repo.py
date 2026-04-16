#!/usr/bin/env python3
"""Synchronize a GitHub repository into a stable local folder."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import BadZipFile, ZipFile


DEFAULT_TARGET_ROOT = Path(r"D:\Obsidian\Github\Source-Repos")


@dataclass
class SyncAttempt:
    method: str
    outcome: str
    detail: str


@dataclass
class SyncResult:
    owner: str
    repo: str
    remote_url: str
    repo_dir: str
    status: str = "pending"
    sync_method: str | None = None
    local_copy_type: str | None = None
    repaired_to: str | None = None
    archive_path: str | None = None
    revision: str | None = None
    github_token_source: str | None = None
    attempts: list[SyncAttempt] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload["attempts"] = [asdict(attempt) for attempt in self.attempts]
        return payload


def parse_repo(repo_ref: str) -> tuple[str, str]:
    ref = repo_ref.strip()
    if ref.startswith("git@github.com:"):
        path = ref.split(":", 1)[1]
    else:
        parsed = urlparse(ref)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError(f"Unsupported GitHub URL: {repo_ref}")
        path = parsed.path

    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"Could not determine owner/repo from: {repo_ref}")

    owner = parts[0]
    repo = parts[1]
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_git_repo(repo_dir: Path) -> bool:
    return (repo_dir / ".git").exists()


def is_broken_repo(repo_dir: Path) -> bool:
    git_dir = repo_dir / ".git"
    if not git_dir.exists():
        return False

    lock_files = [
        git_dir / "index.lock",
        git_dir / "shallow.lock",
        git_dir / "packed-refs.lock",
    ]
    if any(path.exists() for path in lock_files):
        return True

    visible_entries = [path for path in repo_dir.iterdir() if path.name != ".git"]
    return not visible_entries


def repair_repo(repo_dir: Path, dry_run: bool = False) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    repaired_path = repo_dir.with_name(f"{repo_dir.name}.broken-{timestamp}")
    if dry_run:
        return repaired_path

    shutil.move(str(repo_dir), str(repaired_path))
    return repaired_path


def remove_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def replace_directory(source_dir: Path, target_dir: Path) -> None:
    remove_path(target_dir)
    try:
        shutil.move(str(source_dir), str(target_dir))
        return
    except (PermissionError, OSError):
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
        shutil.rmtree(source_dir, ignore_errors=True)


def create_temp_dir(parent: Path, prefix: str) -> Path:
    ensure_directory(parent)
    return Path(tempfile.mkdtemp(prefix=prefix, dir=str(parent)))


def temp_path(parent: Path, prefix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return parent / f"{prefix}{timestamp}"


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    capture_output: bool = True,
    dry_run: bool = False,
) -> subprocess.CompletedProcess[str] | None:
    if dry_run:
        return None

    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=False,
        capture_output=capture_output,
        text=True,
    )


def run_git(
    args: list[str],
    *,
    capture_output: bool = False,
    dry_run: bool = False,
) -> subprocess.CompletedProcess[str] | None:
    command = [
        "git",
        "-c",
        "protocol.version=2",
        "-c",
        "http.version=HTTP/1.1",
        *args,
    ]
    result = run_command(command, capture_output=capture_output, dry_run=dry_run)
    if result is not None and result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(detail)
    return result


def git_revision(repo_dir: Path) -> str | None:
    result = run_git(["-C", str(repo_dir), "rev-parse", "HEAD"], capture_output=True)
    if result is None or result.returncode != 0:
        return None
    revision = (result.stdout or "").strip()
    return revision or None


def current_branch(repo_dir: Path) -> str | None:
    result = run_git(
        ["-C", str(repo_dir), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
    )
    if result is None or result.returncode != 0:
        return None
    branch = (result.stdout or "").strip()
    return branch or None


def get_github_token() -> tuple[str | None, str | None]:
    for env_name in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(env_name)
        if value:
            return value, env_name

    if not command_exists("gh"):
        return None, None

    result = run_command(["gh", "auth", "token"], capture_output=True)
    if result is None or result.returncode != 0:
        return None, None

    token = (result.stdout or "").strip()
    if not token:
        return None, None
    return token, "gh"


def validate_zip_file(zip_path: Path) -> None:
    try:
        with ZipFile(zip_path) as archive:
            archive.infolist()
    except BadZipFile as exc:
        raise RuntimeError(f"Downloaded archive is invalid: {zip_path}") from exc


def download_archive_zip(
    owner: str,
    repo: str,
    destination: Path,
    *,
    token: str | None,
    dry_run: bool = False,
) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
    if dry_run:
        return

    headers = {"User-Agent": "gh-ob-fetch/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=60) as response, destination.open("wb") as file_handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            file_handle.write(chunk)

    validate_zip_file(destination)


def install_archive_snapshot(zip_path: Path, repo_dir: Path, *, dry_run: bool = False) -> None:
    if dry_run:
        return

    temp_extract_dir = create_temp_dir(repo_dir.parent, f"{repo_dir.name}.archive-")
    try:
        with ZipFile(zip_path) as archive:
            archive.extractall(temp_extract_dir)
        extracted_roots = [path for path in temp_extract_dir.iterdir() if path.is_dir()]
        if not extracted_roots:
            raise RuntimeError(f"No extracted directory found in {zip_path}")
        replace_directory(extracted_roots[0], repo_dir)
    finally:
        shutil.rmtree(temp_extract_dir, ignore_errors=True)


def try_gh_clone(owner: str, repo: str, temp_repo_dir: Path, *, dry_run: bool = False) -> None:
    command = [
        "gh",
        "repo",
        "clone",
        f"{owner}/{repo}",
        str(temp_repo_dir),
        "--no-upstream",
        "--",
        "--quiet",
        "--depth=1",
        "--filter=blob:none",
        "--single-branch",
        "-c",
        "protocol.version=2",
        "-c",
        "http.version=HTTP/1.1",
    ]
    result = run_command(command, dry_run=dry_run)
    if result is not None and result.returncode != 0:
        stderr = (result.stderr or "").strip()
        stdout = (result.stdout or "").strip()
        detail = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(detail)


def try_git_clone(remote_url: str, temp_repo_dir: Path, *, dry_run: bool = False) -> None:
    run_git(
        [
            "clone",
            "--quiet",
            "--depth=1",
            "--filter=blob:none",
            "--single-branch",
            remote_url,
            str(temp_repo_dir),
        ],
        dry_run=dry_run,
    )


def update_git_repo(repo_dir: Path, *, dry_run: bool = False) -> str | None:
    run_git(["-C", str(repo_dir), "fetch", "--all", "--tags", "--prune", "--quiet"], dry_run=dry_run)
    if dry_run:
        return None

    branch = current_branch(repo_dir)
    if branch and branch != "HEAD":
        run_git(["-C", str(repo_dir), "pull", "--ff-only", "--quiet"], dry_run=False)
    return git_revision(repo_dir)


def record_attempt(result: SyncResult, method: str, outcome: str, detail: str) -> None:
    result.attempts.append(SyncAttempt(method=method, outcome=outcome, detail=detail))


def sync_with_git_strategy(
    result: SyncResult,
    *,
    owner: str,
    repo: str,
    remote_url: str,
    repo_dir: Path,
    dry_run: bool,
) -> bool:
    strategies: list[str] = []
    if command_exists("gh"):
        strategies.append("gh-clone")
    if command_exists("git"):
        strategies.append("git-clone")

    for method in strategies:
        temp_dir = (
            temp_path(repo_dir.parent, f"{repo_dir.name}.{method}.")
            if dry_run
            else create_temp_dir(repo_dir.parent, f"{repo_dir.name}.{method}.")
        )
        try:
            if method == "gh-clone":
                try_gh_clone(owner, repo, temp_dir, dry_run=dry_run)
            else:
                try_git_clone(remote_url, temp_dir, dry_run=dry_run)
            record_attempt(result, method, "success", "Repository synchronized as a git clone")
            if dry_run:
                result.status = "would-clone"
                result.sync_method = method
                result.local_copy_type = "git-repo"
                return True

            replace_directory(temp_dir, repo_dir)
            result.status = "cloned"
            result.sync_method = method
            result.local_copy_type = "git-repo"
            result.revision = git_revision(repo_dir)
            return True
        except Exception as exc:
            record_attempt(result, method, "failed", str(exc))
            if not dry_run:
                shutil.rmtree(temp_dir, ignore_errors=True)

    return False


def sync_with_archive_strategy(
    result: SyncResult,
    *,
    owner: str,
    repo: str,
    repo_dir: Path,
    token: str | None,
    dry_run: bool,
) -> bool:
    archive_path = repo_dir.parent / f"{repo_dir.name}.zip"
    try:
        download_archive_zip(owner, repo, archive_path, token=token, dry_run=dry_run)
        install_archive_snapshot(archive_path, repo_dir, dry_run=dry_run)
        record_attempt(result, "github-archive", "success", "Repository synchronized as a source snapshot")
        result.archive_path = str(archive_path)
        result.status = "would-download-archive" if dry_run else "downloaded"
        result.sync_method = "github-archive"
        result.local_copy_type = "source-snapshot"
        return True
    except Exception as exc:
        record_attempt(result, "github-archive", "failed", str(exc))
        return False


def sync_repository(
    repo_ref: str,
    *,
    target_root: Path,
    repair_broken: bool,
    dry_run: bool,
) -> SyncResult:
    owner, repo = parse_repo(repo_ref)
    remote_url = f"https://github.com/{owner}/{repo}.git"
    repo_dir = target_root / f"{owner}__{repo}"
    result = SyncResult(
        owner=owner,
        repo=repo,
        remote_url=remote_url,
        repo_dir=str(repo_dir),
    )

    token, token_source = get_github_token()
    result.github_token_source = token_source
    if not dry_run:
        ensure_directory(target_root)

    if repo_dir.exists() and is_broken_repo(repo_dir):
        if not repair_broken:
            raise RuntimeError(
                f"Broken repository detected at {repo_dir}; rerun with --repair-broken to preserve it and retry"
            )
        repaired_path = repair_repo(repo_dir, dry_run=dry_run)
        result.repaired_to = str(repaired_path)
        record_attempt(result, "repair-broken", "success", f"Moved broken repo to {repaired_path}")

    if repo_dir.exists() and is_git_repo(repo_dir):
        try:
            revision = update_git_repo(repo_dir, dry_run=dry_run)
            record_attempt(result, "git-update", "success", "Updated existing git repository")
            result.status = "would-update" if dry_run else "updated"
            result.sync_method = "git-update"
            result.local_copy_type = "git-repo"
            result.revision = revision
            return result
        except Exception as exc:
            record_attempt(result, "git-update", "failed", str(exc))
            raise RuntimeError(f"Existing git repository update failed: {exc}") from exc

    if repo_dir.exists() and not is_git_repo(repo_dir):
        result.warnings.append(
            f"Existing snapshot at {repo_dir} will be replaced if archive fallback succeeds"
        )

    if sync_with_git_strategy(
        result,
        owner=owner,
        repo=repo,
        remote_url=remote_url,
        repo_dir=repo_dir,
        dry_run=dry_run,
    ):
        return result

    if sync_with_archive_strategy(
        result,
        owner=owner,
        repo=repo,
        repo_dir=repo_dir,
        token=token,
        dry_run=dry_run,
    ):
        return result

    attempt_summary = "; ".join(
        f"{attempt.method}:{attempt.detail}" for attempt in result.attempts if attempt.outcome == "failed"
    )
    raise RuntimeError(f"All sync strategies failed: {attempt_summary}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize a GitHub repository into a stable local folder."
    )
    parser.add_argument("repo", help="GitHub repository URL or SSH remote")
    parser.add_argument(
        "--target-root",
        default=str(DEFAULT_TARGET_ROOT),
        help=f"Base directory for synchronized repositories (default: {DEFAULT_TARGET_ROOT})",
    )
    parser.add_argument(
        "--repair-broken",
        action="store_true",
        help="Rename an interrupted/broken local repo directory before retrying sync.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the chosen sync plan without executing network or filesystem changes.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON describing the sync result.",
    )
    return parser.parse_args()


def emit_result(result: SyncResult, *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result.to_payload(), ensure_ascii=False, indent=2))
        return

    print(f"owner={result.owner}")
    print(f"repo={result.repo}")
    print(f"remote={result.remote_url}")
    print(f"target={result.repo_dir}")
    print(f"status={result.status}")
    if result.sync_method:
        print(f"sync_method={result.sync_method}")
    if result.local_copy_type:
        print(f"local_copy_type={result.local_copy_type}")
    if result.repaired_to:
        print(f"repaired_to={result.repaired_to}")
    if result.archive_path:
        print(f"archive_path={result.archive_path}")
    if result.revision:
        print(f"revision={result.revision}")
    if result.github_token_source:
        print(f"github_token_source={result.github_token_source}")
    for warning in result.warnings:
        print(f"warning={warning}")
    for attempt in result.attempts:
        print(f"attempt={attempt.method}:{attempt.outcome}:{attempt.detail}")


def main() -> int:
    args = parse_args()
    result = sync_repository(
        args.repo,
        target_root=Path(args.target_root),
        repair_broken=args.repair_broken,
        dry_run=args.dry_run,
    )
    emit_result(result, as_json=args.json)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI failure path
        print(f"error={exc}", file=sys.stderr)
        raise SystemExit(1)
