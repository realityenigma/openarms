import hashlib

from fastapi.testclient import TestClient

from armswideopen.api.users import create_access_token
from armswideopen.db import Model, User
from armswideopen.db.database import Base, SessionLocal, engine
from armswideopen.main import app
from armswideopen.services.storage import storage_service


client = TestClient(app)


def reset_state(tmp_path):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    storage_service.base_path = tmp_path / "storage"
    storage_service.base_path.mkdir(parents=True, exist_ok=True)


def create_model(private: bool = False):
    db = SessionLocal()
    try:
        user = User(
            username="alice",
            email="alice@example.com",
            hashed_password="not-used",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        model = Model(
            model_id="alice/demo-model",
            name="demo-model",
            description="Demo",
            author_id=user.id,
            is_private=private,
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        token = create_access_token({"sub": user.username})
        return model.model_id, token
    finally:
        db.close()


def test_lfs_batch_upload_and_download_roundtrip(tmp_path):
    reset_state(tmp_path)
    repo_id, token = create_model(private=False)

    data = b"hello-lfs-world"
    oid = hashlib.sha256(data).hexdigest()

    headers = {"Authorization": f"Bearer {token}"}
    batch_upload = client.post(
        f"/{repo_id}.git/info/lfs/objects/batch",
        json={"operation": "upload", "transfers": ["basic"], "objects": [{"oid": oid, "size": len(data)}]},
        headers=headers,
    )
    assert batch_upload.status_code == 200
    obj = batch_upload.json()["objects"][0]
    upload_href = obj["actions"]["upload"]["href"]
    verify_href = obj["actions"]["verify"]["href"]

    put_resp = client.put(upload_href, content=data, headers=headers)
    assert put_resp.status_code == 200

    verify_resp = client.post(verify_href, json={"oid": oid, "size": len(data)}, headers=headers)
    assert verify_resp.status_code == 200
    assert verify_resp.json()["verified"] is True

    batch_download = client.post(
        f"/{repo_id}.git/info/lfs/objects/batch",
        json={"operation": "download", "transfers": ["basic"], "objects": [{"oid": oid, "size": len(data)}]},
    )
    assert batch_download.status_code == 200
    dl_href = batch_download.json()["objects"][0]["actions"]["download"]["href"]

    dl_resp = client.get(dl_href)
    assert dl_resp.status_code == 200
    assert dl_resp.content == data


def test_lfs_private_repo_requires_auth(tmp_path):
    reset_state(tmp_path)
    repo_id, _token = create_model(private=True)
    oid = "a" * 64

    resp = client.post(
        f"/{repo_id}.git/info/lfs/objects/batch",
        json={"operation": "download", "objects": [{"oid": oid, "size": 1}]},
    )
    assert resp.status_code == 401


def test_lfs_rejects_oid_mismatch(tmp_path):
    reset_state(tmp_path)
    repo_id, token = create_model(private=False)
    bad_oid = "b" * 64
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.put(f"/{repo_id}.git/info/lfs/objects/{bad_oid}", content=b"different", headers=headers)
    assert resp.status_code == 422


def test_lfs_batch_invalid_oid_reports_object_error(tmp_path):
    reset_state(tmp_path)
    repo_id, token = create_model(private=False)
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        f"/{repo_id}.git/info/lfs/objects/batch",
        json={"operation": "upload", "objects": [{"oid": "short", "size": 1}]},
        headers=headers,
    )
    assert resp.status_code == 200
    obj = resp.json()["objects"][0]
    assert obj["error"]["code"] == 422


def test_lfs_verify_rejects_wrong_size(tmp_path):
    reset_state(tmp_path)
    repo_id, token = create_model(private=False)
    data = b"verify-size"
    oid = hashlib.sha256(data).hexdigest()
    headers = {"Authorization": f"Bearer {token}"}

    put_resp = client.put(f"/{repo_id}.git/info/lfs/objects/{oid}", content=data, headers=headers)
    assert put_resp.status_code == 200

    verify_resp = client.post(
        f"/{repo_id}.git/info/lfs/objects/{oid}/verify",
        json={"oid": oid, "size": len(data) + 1},
        headers=headers,
    )
    assert verify_resp.status_code == 422


def test_lfs_verify_requires_writer_auth(tmp_path):
    reset_state(tmp_path)
    repo_id, _token = create_model(private=False)
    oid = "c" * 64
    resp = client.post(
        f"/{repo_id}.git/info/lfs/objects/{oid}/verify",
        json={"oid": oid, "size": 1},
    )
    assert resp.status_code == 401
