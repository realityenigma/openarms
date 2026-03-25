"""Python SDK compatibility layer for OpenArms."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


DEFAULT_ENDPOINT = os.getenv("ARMSWIDEOPEN_HUB_URL", "http://localhost:8000").rstrip("/")
AUTH_FILE = Path.home() / ".armswideopen" / "auth.json"


class HubError(RuntimeError):
    """Raised when the hub API returns an error."""


class AuthenticationError(HubError):
    """Raised when authentication is missing or invalid."""


def _ensure_auth_dir() -> None:
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_auth(token: str, username: str, endpoint: str) -> None:
    _ensure_auth_dir()
    AUTH_FILE.write_text(
        json.dumps(
            {
                "token": token,
                "username": username,
                "endpoint": endpoint.rstrip("/"),
            }
        )
    )


def clear_auth() -> None:
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()


def load_auth() -> Dict[str, str]:
    if not AUTH_FILE.exists():
        return {}
    try:
        return json.loads(AUTH_FILE.read_text())
    except json.JSONDecodeError:
        return {}


class HfApi:
    """Subset-compatible API client modeled after huggingface_hub.HfApi."""

    def __init__(self, endpoint: str = DEFAULT_ENDPOINT, token: Optional[str] = None):
        self.endpoint = endpoint.rstrip("/")
        stored = load_auth()
        self.token = token or stored.get("token")

    def _headers(self, token: Optional[str] = None) -> Dict[str, str]:
        auth_token = token or self.token
        headers: Dict[str, str] = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> requests.Response:
        url = f"{self.endpoint}{path}"
        response = requests.request(
            method,
            url,
            headers=self._headers(token),
            params=params,
            json=json_body,
            files=files,
            stream=stream,
            timeout=120,
        )
        if response.status_code >= 400:
            message = response.text
            try:
                payload = response.json()
                message = payload.get("detail", message)
            except Exception:
                pass
            if response.status_code in (401, 403):
                raise AuthenticationError(f"{response.status_code} {method} {path}: {message}")
            raise HubError(f"{response.status_code} {method} {path}: {message}")
        return response

    def login(self, username: str, password: str) -> str:
        response = self._request(
            "POST",
            "/api/v1/users/login",
            json_body={"username": username, "password": password},
        )
        token = response.json()["access_token"]
        self.token = token
        save_auth(token=token, username=username, endpoint=self.endpoint)
        return token

    def logout(self) -> None:
        self.token = None
        clear_auth()

    def whoami(self) -> Dict[str, Any]:
        auth = load_auth()
        username = auth.get("username")
        if not username:
            raise AuthenticationError("No stored username. Run login first.")
        return self._request("GET", f"/api/v1/users/{username}").json()

    def list_models(self, search: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {"limit": limit}
        if search:
            params["search"] = search
        return self._request("GET", "/api/models", params=params).json()

    def create_repo(
        self,
        repo_id: str,
        *,
        repo_type: str = "model",
        private: bool = False,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        if repo_type == "model":
            payload = {
                "model_id": repo_id,
                "name": name or repo_id.split("/")[-1],
                "description": description,
                "is_private": private,
                "model_type": "other",
                "tags": None,
            }
            return self._request("POST", "/api/v1/models", json_body=payload).json()

        if repo_type == "dataset":
            payload = {
                "dataset_id": repo_id,
                "name": name or repo_id.split("/")[-1],
                "description": description,
                "is_private": private,
                "tags": None,
            }
            return self._request("POST", "/api/v1/datasets", json_body=payload).json()

        raise HubError("Unsupported repo_type. Supported values: model, dataset.")

    def upload_file(
        self,
        *,
        path_or_fileobj: str,
        path_in_repo: str,
        repo_id: str,
        repo_type: str = "model",
    ) -> Dict[str, Any]:
        file_path = Path(path_or_fileobj)
        if not file_path.exists():
            raise HubError(f"File not found: {file_path}")
        with file_path.open("rb") as infile:
            files = {"file": (path_in_repo, infile)}
            if repo_type == "dataset":
                return self._request(
                    "POST",
                    "/api/v1/datasets/files",
                    params={"dataset_id": repo_id},
                    files=files,
                ).json()
            return self._request(
                "POST",
                "/api/v1/models/files",
                params={"model_id": repo_id},
                files=files,
            ).json()


def hf_hub_download(
    repo_id: str,
    filename: str,
    *,
    revision: str = "main",
    token: Optional[str] = None,
    local_dir: Optional[str] = None,
    endpoint: str = DEFAULT_ENDPOINT,
) -> str:
    """Download a file from the hub, similar to huggingface_hub.hf_hub_download."""
    api = HfApi(endpoint=endpoint, token=token)
    response = api._request("GET", f"/{repo_id}/resolve/{revision}/{filename}", stream=True)

    target_dir = Path(local_dir) if local_dir else (Path.home() / ".cache" / "armswideopen" / repo_id / revision)
    target_path = target_dir / filename
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open("wb") as outfile:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                outfile.write(chunk)
    return str(target_path)
