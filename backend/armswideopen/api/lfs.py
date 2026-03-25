"""Git LFS protocol endpoints for model repositories."""
from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from armswideopen.api.auth import get_user_from_token
from armswideopen.db import Model, User, get_db
from armswideopen.services.storage import storage_service

router = APIRouter(tags=["lfs"])


def _require_model(repo_id: str, db: Session) -> Model:
    model = db.query(Model).filter(Model.model_id == repo_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def _assert_lfs_access(model: Model, db: Session, authorization: Optional[str], write: bool = False) -> Optional[User]:
    token = _extract_bearer_token(authorization)
    user = get_user_from_token(token, db) if token else None

    if model.is_private and user is None:
        raise HTTPException(status_code=401, detail="Authentication required")

    if write:
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        if model.author_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    return user


def _lfs_download_href(repo_id: str, oid: str) -> str:
    return f"/{repo_id}.git/info/lfs/objects/{oid}"


def _lfs_verify_href(repo_id: str, oid: str) -> str:
    return f"/{repo_id}.git/info/lfs/objects/{oid}/verify"


def _is_valid_oid(oid: str) -> bool:
    return len(oid) == 64 and all(ch in "0123456789abcdef" for ch in oid.lower())


@router.post("/{repo_id:path}.git/info/lfs/objects/batch")
def lfs_batch(
    repo_id: str,
    payload: dict[str, Any],
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Git LFS batch API endpoint."""
    model = _require_model(repo_id, db)

    operation = payload.get("operation")
    if operation not in ("download", "upload"):
        raise HTTPException(status_code=400, detail="Invalid operation")

    _assert_lfs_access(model, db, authorization, write=(operation == "upload"))

    objects = payload.get("objects", [])
    if not isinstance(objects, list):
        raise HTTPException(status_code=400, detail="Invalid objects payload")

    response_objects = []
    for obj in objects:
        oid = obj.get("oid")
        size = obj.get("size", 0)
        if not oid:
            continue
        if not _is_valid_oid(oid):
            response_objects.append(
                {
                    "oid": oid,
                    "size": size,
                    "error": {"code": 422, "message": "Invalid oid"},
                }
            )
            continue

        base = {
            "oid": oid,
            "size": size,
        }

        href = _lfs_download_href(repo_id, oid)
        if operation == "download":
            try:
                storage_service.lfs_object_path(oid)
                base["actions"] = {"download": {"href": href}}
            except FileNotFoundError:
                base["error"] = {"code": 404, "message": "Object not found"}
        else:
            base["actions"] = {
                "upload": {"href": href},
                "verify": {"href": _lfs_verify_href(repo_id, oid)},
            }
        response_objects.append(base)

    return {"transfer": "basic", "objects": response_objects}


@router.put("/{repo_id:path}.git/info/lfs/objects/{oid}")
async def lfs_upload_object(
    repo_id: str,
    oid: str,
    request: Request,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Upload an LFS object."""
    model = _require_model(repo_id, db)
    _assert_lfs_access(model, db, authorization, write=True)
    if not _is_valid_oid(oid):
        raise HTTPException(status_code=422, detail="Invalid oid")

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty upload body")
    computed_oid = hashlib.sha256(body).hexdigest()
    if computed_oid != oid:
        raise HTTPException(status_code=422, detail="OID mismatch")

    with NamedTemporaryFile(delete=False) as temp:
        temp_path = Path(temp.name)
        temp.write(body)
    try:
        storage_service.write_lfs_object(oid, temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return {"oid": oid, "uploaded": True}


@router.post("/{repo_id:path}.git/info/lfs/objects/{oid}/verify")
def lfs_verify_object(
    repo_id: str,
    oid: str,
    payload: dict[str, Any],
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Verify LFS object exists and metadata matches oid/size."""
    model = _require_model(repo_id, db)
    _assert_lfs_access(model, db, authorization, write=True)
    if not _is_valid_oid(oid):
        raise HTTPException(status_code=422, detail="Invalid oid")

    payload_oid = payload.get("oid")
    payload_size = payload.get("size")
    if payload_oid != oid:
        raise HTTPException(status_code=422, detail="OID mismatch")

    try:
        object_path = storage_service.lfs_object_path(oid)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Object not found") from exc

    actual_size = object_path.stat().st_size
    if payload_size is not None and payload_size != actual_size:
        raise HTTPException(status_code=422, detail="Size mismatch")

    return {"oid": oid, "size": actual_size, "verified": True}


@router.get("/{repo_id:path}.git/info/lfs/objects/{oid}")
def lfs_download_object(
    repo_id: str,
    oid: str,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    """Download an LFS object."""
    model = _require_model(repo_id, db)
    _assert_lfs_access(model, db, authorization, write=False)
    if not _is_valid_oid(oid):
        raise HTTPException(status_code=422, detail="Invalid oid")

    try:
        file_path = storage_service.lfs_object_path(oid)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Object not found") from exc

    return FileResponse(path=str(file_path), filename=oid)
