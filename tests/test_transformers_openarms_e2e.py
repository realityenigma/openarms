import json
import os
import time
from uuid import uuid4

import pytest
import requests


def _wait_for_health(base_url: str, timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"OpenArms backend not healthy at {base_url} within {timeout_seconds}s")


@pytest.mark.integration
def test_transformers_can_pull_model_config_from_openarms():
    base_url = os.getenv("OPENARMS_ENDPOINT", "http://localhost:8000").rstrip("/")
    password = "password123"
    username = f"tfm_{uuid4().hex[:8]}"
    email = f"{username}@example.com"
    repo_id = f"{username}/tiny-config-e2e"

    _wait_for_health(base_url)

    register = requests.post(
        f"{base_url}/api/v1/users/register",
        json={"username": username, "email": email, "password": password, "full_name": "Transformers E2E"},
        timeout=10,
    )
    assert register.status_code == 201, register.text

    login = requests.post(
        f"{base_url}/api/v1/users/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_model = requests.post(
        f"{base_url}/api/v1/models",
        headers=headers,
        json={
            "model_id": repo_id,
            "name": "tiny-config-e2e",
            "description": "transformers openarms e2e",
            "model_type": "other",
            "tags": "e2e,transformers",
            "is_private": False,
        },
        timeout=10,
    )
    assert create_model.status_code == 201, create_model.text

    config_payload = {"model_type": "bert", "hidden_size": 32, "num_attention_heads": 2, "num_hidden_layers": 2}
    config_bytes = json.dumps(config_payload).encode("utf-8")

    upload = requests.post(
        f"{base_url}/api/v1/models/files",
        params={"model_id": repo_id},
        headers=headers,
        files={"file": ("config.json", config_bytes, "application/json")},
        timeout=15,
    )
    assert upload.status_code == 200, upload.text

    previous_endpoint = os.environ.get("HF_ENDPOINT")
    try:
        os.environ["HF_ENDPOINT"] = base_url
        from transformers import AutoConfig

        cfg = AutoConfig.from_pretrained(repo_id)
        assert cfg.model_type == "bert"
    finally:
        if previous_endpoint is None:
            os.environ.pop("HF_ENDPOINT", None)
        else:
            os.environ["HF_ENDPOINT"] = previous_endpoint
