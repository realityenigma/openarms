import hashlib

from fastapi.testclient import TestClient

from armswideopen.db.database import Base, engine
from armswideopen.main import app
from armswideopen.services.storage import storage_service


client = TestClient(app)


def reset_state(tmp_path):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    storage_service.base_path = tmp_path / "storage"
    storage_service.base_path.mkdir(parents=True, exist_ok=True)


def test_end_to_end_hub_flow(tmp_path):
    reset_state(tmp_path)

    register_resp = client.post(
        "/api/v1/users/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
            "full_name": "Alice",
        },
    )
    assert register_resp.status_code == 201

    login_resp = client.post(
        "/api/v1/users/login",
        json={"username": "alice", "password": "password123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_model_resp = client.post(
        "/api/v1/models",
        headers=headers,
        json={
            "model_id": "alice/e2e-model",
            "name": "e2e-model",
            "description": "E2E Model",
            "model_type": "other",
            "tags": "e2e,test",
            "is_private": False,
        },
    )
    assert create_model_resp.status_code == 201

    wrong_owner_model_resp = client.post(
        "/api/v1/models",
        headers=headers,
        json={
            "model_id": "bob/not-allowed-model",
            "name": "not-allowed-model",
            "description": "wrong owner",
            "model_type": "other",
            "tags": "e2e,test",
            "is_private": False,
        },
    )
    assert wrong_owner_model_resp.status_code == 403

    create_dataset_resp = client.post(
        "/api/v1/datasets",
        headers=headers,
        json={
            "dataset_id": "alice/e2e-dataset",
            "name": "e2e-dataset",
            "description": "E2E Dataset",
            "tags": "e2e,test",
            "is_private": False,
        },
    )
    assert create_dataset_resp.status_code == 201

    wrong_owner_dataset_resp = client.post(
        "/api/v1/datasets",
        headers=headers,
        json={
            "dataset_id": "bob/not-allowed-dataset",
            "name": "not-allowed-dataset",
            "description": "wrong owner",
            "tags": "e2e,test",
            "is_private": False,
        },
    )
    assert wrong_owner_dataset_resp.status_code == 403

    dataset_detail_resp = client.get("/api/v1/datasets/alice/e2e-dataset")
    assert dataset_detail_resp.status_code == 200
    assert dataset_detail_resp.json()["dataset_id"] == "alice/e2e-dataset"

    dataset_upload_resp = client.post(
        "/api/v1/datasets/files",
        params={"dataset_id": "alice/e2e-dataset"},
        headers=headers,
        files={"file": ("data.csv", b"text,label\nhello,1\nworld,0\n")},
    )
    assert dataset_upload_resp.status_code == 200

    dataset_files_resp = client.get("/api/v1/datasets/files", params={"dataset_id": "alice/e2e-dataset"})
    assert dataset_files_resp.status_code == 200
    dataset_file_names = [item["filename"] for item in dataset_files_resp.json()["files"]]
    assert "data.csv" in dataset_file_names

    dataset_preview_resp = client.get(
        "/api/v1/datasets/preview",
        params={"dataset_id": "alice/e2e-dataset", "filename": "data.csv"},
    )
    assert dataset_preview_resp.status_code == 200
    assert dataset_preview_resp.json()["format"] == "csv"

    upload_resp = client.post(
        "/api/v1/models/files",
        params={"model_id": "alice/e2e-model"},
        headers=headers,
        files={"file": ("model.bin", b"model-bytes")},
    )
    assert upload_resp.status_code == 200

    list_files_resp = client.get("/api/v1/models/alice/e2e-model/files")
    assert list_files_resp.status_code == 200
    file_names = [item["filename"] for item in list_files_resp.json()["files"]]
    assert "model.bin" in file_names

    hf_info_resp = client.get("/api/models/alice/e2e-model")
    assert hf_info_resp.status_code == 200
    assert hf_info_resp.json()["id"] == "alice/e2e-model"

    resolve_resp = client.get("/alice/e2e-model/resolve/main/model.bin")
    assert resolve_resp.status_code == 200
    assert resolve_resp.content == b"model-bytes"

    lfs_data = b"lfs-e2e-content"
    lfs_oid = hashlib.sha256(lfs_data).hexdigest()

    lfs_batch_upload = client.post(
        "/alice/e2e-model.git/info/lfs/objects/batch",
        headers=headers,
        json={
            "operation": "upload",
            "transfers": ["basic"],
            "objects": [{"oid": lfs_oid, "size": len(lfs_data)}],
        },
    )
    assert lfs_batch_upload.status_code == 200
    actions = lfs_batch_upload.json()["objects"][0]["actions"]

    lfs_put = client.put(actions["upload"]["href"], headers=headers, content=lfs_data)
    assert lfs_put.status_code == 200

    lfs_verify = client.post(actions["verify"]["href"], headers=headers, json={"oid": lfs_oid, "size": len(lfs_data)})
    assert lfs_verify.status_code == 200

    lfs_batch_download = client.post(
        "/alice/e2e-model.git/info/lfs/objects/batch",
        json={
            "operation": "download",
            "transfers": ["basic"],
            "objects": [{"oid": lfs_oid, "size": len(lfs_data)}],
        },
    )
    assert lfs_batch_download.status_code == 200
    dl_href = lfs_batch_download.json()["objects"][0]["actions"]["download"]["href"]

    lfs_get = client.get(dl_href)
    assert lfs_get.status_code == 200
    assert lfs_get.content == lfs_data
