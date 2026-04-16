from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "fetch_github_repo.py"


def load_module():
    spec = importlib.util.spec_from_file_location("fetch_github_repo", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FetchGithubRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()

    def test_parse_repo_supports_root_repo_url(self) -> None:
        owner, repo = self.module.parse_repo("https://github.com/luongnv89/claude-howto")

        self.assertEqual(owner, "luongnv89")
        self.assertEqual(repo, "claude-howto")

    def test_parse_repo_supports_deep_blob_url(self) -> None:
        owner, repo = self.module.parse_repo(
            "https://github.com/luongnv89/claude-howto/blob/main/README.md"
        )

        self.assertEqual(owner, "luongnv89")
        self.assertEqual(repo, "claude-howto")

    def test_parse_repo_supports_ssh_url(self) -> None:
        owner, repo = self.module.parse_repo("git@github.com:luongnv89/claude-howto.git")

        self.assertEqual(owner, "luongnv89")
        self.assertEqual(repo, "claude-howto")

    def test_is_broken_repo_detects_git_dir_without_worktree(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            (repo_dir / ".git").mkdir(parents=True)

            self.assertTrue(self.module.is_broken_repo(repo_dir))

    def test_is_broken_repo_detects_lock_file(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            git_dir = repo_dir / ".git"
            git_dir.mkdir(parents=True)
            (git_dir / "index.lock").write_text("", encoding="utf-8")
            (repo_dir / "README.md").write_text("hello", encoding="utf-8")

            self.assertTrue(self.module.is_broken_repo(repo_dir))

    def test_is_broken_repo_accepts_repo_with_visible_content(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            (repo_dir / ".git").mkdir(parents=True)
            (repo_dir / "README.md").write_text("ok", encoding="utf-8")

            self.assertFalse(self.module.is_broken_repo(repo_dir))

    def test_repair_repo_dry_run_returns_timestamped_target(self) -> None:
        with TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "repo"
            repo_dir.mkdir()

            repaired = self.module.repair_repo(repo_dir, dry_run=True)

            self.assertEqual(repaired.parent, repo_dir.parent)
            self.assertTrue(repaired.name.startswith("repo.broken-"))
            self.assertTrue(repo_dir.exists())

    def test_replace_directory_overwrites_existing_target(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            target = root / "target"
            source.mkdir()
            target.mkdir()
            (source / "fresh.txt").write_text("fresh", encoding="utf-8")
            (target / "stale.txt").write_text("stale", encoding="utf-8")

            self.module.replace_directory(source, target)

            self.assertTrue((target / "fresh.txt").exists())
            self.assertFalse((target / "stale.txt").exists())
            self.assertFalse(source.exists())

    def test_install_archive_snapshot_extracts_repo(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "repo.zip"
            repo_dir = root / "repo"

            with ZipFile(archive, "w") as zip_file:
                zip_file.writestr("owner-repo-sha/README.md", "hello")
                zip_file.writestr("owner-repo-sha/src/app.py", "print('hi')")

            self.module.install_archive_snapshot(archive, repo_dir)

            self.assertTrue((repo_dir / "README.md").exists())
            self.assertTrue((repo_dir / "src" / "app.py").exists())

    def test_sync_repository_dry_run_prefers_gh_clone(self) -> None:
        with TemporaryDirectory() as tmp:
            target_root = Path(tmp) / "repos"

            with patch.object(self.module, "command_exists", side_effect=lambda name: name in {"gh", "git"}):
                with patch.object(self.module, "get_github_token", return_value=("token", "gh")):
                    with patch.object(self.module, "try_gh_clone") as gh_clone:
                        with patch.object(self.module, "try_git_clone") as git_clone:
                            result = self.module.sync_repository(
                                "https://github.com/luongnv89/claude-howto",
                                target_root=target_root,
                                repair_broken=False,
                                dry_run=True,
                            )

            self.assertEqual(result.status, "would-clone")
            self.assertEqual(result.sync_method, "gh-clone")
            self.assertEqual(result.local_copy_type, "git-repo")
            gh_clone.assert_called_once()
            git_clone.assert_not_called()

    def test_sync_repository_dry_run_falls_back_to_archive(self) -> None:
        with TemporaryDirectory() as tmp:
            target_root = Path(tmp) / "repos"

            with patch.object(self.module, "command_exists", return_value=False):
                with patch.object(self.module, "get_github_token", return_value=("token", "gh")):
                    with patch.object(self.module, "download_archive_zip") as download_archive:
                        with patch.object(self.module, "install_archive_snapshot") as install_archive:
                            result = self.module.sync_repository(
                                "https://github.com/luongnv89/claude-howto",
                                target_root=target_root,
                                repair_broken=False,
                                dry_run=True,
                            )

            self.assertEqual(result.status, "would-download-archive")
            self.assertEqual(result.sync_method, "github-archive")
            self.assertEqual(result.local_copy_type, "source-snapshot")
            self.assertTrue(result.archive_path.endswith("luongnv89__claude-howto.zip"))
            download_archive.assert_called_once()
            install_archive.assert_called_once()


if __name__ == "__main__":
    unittest.main()
