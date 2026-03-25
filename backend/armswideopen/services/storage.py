"""Local storage and lightweight Git metadata service for model files."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from armswideopen.config import settings


class StorageService:
    """Handles model file persistence and repository revision metadata."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _repo_path(self, repo_id: str) -> Path:
        safe_repo_id = repo_id.replace("/", "__")
        repo_path = self.base_path / safe_repo_id
        repo_path.mkdir(parents=True, exist_ok=True)
        return repo_path

    def save_repo_file(self, repo_id: str, filename: str, source_file: Path) -> dict:
        repo_path = self._repo_path(repo_id)
        destination = repo_path / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_file, destination)

        sha256 = hashlib.sha256()
        with destination.open("rb") as infile:
            for chunk in iter(lambda: infile.read(1024 * 1024), b""):
                sha256.update(chunk)

        return {
            "path": str(destination),
            "size": destination.stat().st_size,
            "sha256": sha256.hexdigest(),
        }

    def save_model_file(self, model_id: str, filename: str, source_file: Path) -> dict:
        return self.save_repo_file(model_id, filename, source_file)

    def write_lfs_object(self, oid: str, source_file: Path) -> dict:
        """Persist an LFS object by oid."""
        if not oid or len(oid) < 4:
            raise ValueError("Invalid object id")
        if "/" in oid or ".." in oid:
            raise ValueError("Invalid object id")

        object_dir = self.base_path / "lfs" / oid[:2] / oid[2:4]
        object_dir.mkdir(parents=True, exist_ok=True)
        destination = object_dir / oid
        shutil.copyfile(source_file, destination)
        return {"path": str(destination), "size": destination.stat().st_size}

    def lfs_object_path(self, oid: str) -> Path:
        """Resolve the expected storage path for an LFS object."""
        if not oid or len(oid) < 4:
            raise FileNotFoundError(oid)
        if "/" in oid or ".." in oid:
            raise FileNotFoundError(oid)
        target = self.base_path / "lfs" / oid[:2] / oid[2:4] / oid
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(oid)
        return target

    def read_repo_file(self, repo_id: str, filename: str) -> Path:
        repo_path = self._repo_path(repo_id)
        target = repo_path / filename
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(filename)
        return target

    def read_model_file(self, model_id: str, filename: str) -> Path:
        return self.read_repo_file(model_id, filename)

    def list_repo_files(self, repo_id: str) -> list[dict]:
        repo_path = self._repo_path(repo_id)
        files = []
        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue
            rel = path.relative_to(repo_path).as_posix()
            stat = path.stat()
            files.append({"filename": rel, "file_size": stat.st_size, "created_at": stat.st_mtime})
        files.sort(key=lambda item: item["filename"])
        return files

    def current_revision(self, model_id: str) -> Optional[str]:
        repo_path = self._repo_path(model_id)
        git_dir = repo_path / ".git"
        if not git_dir.exists():
            return None
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() or None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def commit_file_change(self, model_id: str, filename: str, message: str) -> Optional[str]:
        repo_path = self._repo_path(model_id)

        if not (repo_path / ".git").exists():
            try:
                subprocess.run(["git", "-C", str(repo_path), "init"], check=True, capture_output=True)
                subprocess.run(
                    ["git", "-C", str(repo_path), "config", "user.email", "system@armswideopen.local"],
                    check=True,
                    capture_output=True,
                )
                subprocess.run(
                    ["git", "-C", str(repo_path), "config", "user.name", "OpenArms System"],
                    check=True,
                    capture_output=True,
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                return None

        try:
            subprocess.run(["git", "-C", str(repo_path), "add", filename], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(repo_path), "commit", "-m", message], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # No-op for unchanged files or commit problems; still return best-known revision.
            pass
        except FileNotFoundError:
            return None

        return self.current_revision(model_id)


storage_service = StorageService()
