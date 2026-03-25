"""Compatibility endpoints for a subset of Hugging Face Hub client behavior."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from armswideopen.db import Dataset, Model, get_db
from armswideopen.services.storage import storage_service

router = APIRouter(tags=["hf-compat"])


def _get_public_model(repo_id: str, db: Session) -> Model:
    model = db.query(Model).filter(Model.model_id == repo_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    if model.is_private:
        raise HTTPException(status_code=403, detail="Access denied")
    return model


def _is_valid_revision(model: Model, revision: str) -> bool:
    if revision in ("main", "master"):
        return True
    if not model.latest_revision:
        return False
    return revision == model.latest_revision


def _build_siblings(model: Model) -> list[dict[str, Any]]:
    return [
        {
            "rfilename": item.filename,
            "size": item.file_size or 0,
        }
        for item in model.files
    ]


def _get_public_dataset(repo_id: str, db: Session) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.dataset_id == repo_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.is_private:
        raise HTTPException(status_code=403, detail="Access denied")
    return dataset


def _is_valid_dataset_revision(dataset: Dataset, revision: str) -> bool:
    if revision in ("main", "master"):
        return True
    if not dataset.latest_revision:
        return False
    return revision == dataset.latest_revision


def _build_dataset_siblings(dataset: Dataset) -> list[dict[str, Any]]:
    return [
        {"rfilename": item["filename"], "size": item["file_size"] or 0}
        for item in storage_service.list_repo_files(dataset.dataset_id)
    ]


def _hf_resolve_headers(revision: Optional[str], file_hash: Optional[str], file_size: Optional[int]) -> dict[str, str]:
    headers: dict[str, str] = {}
    if revision:
        headers["X-Repo-Commit"] = revision
    if file_hash:
        headers["ETag"] = f"\"{file_hash}\""
    if file_size is not None:
        headers["Content-Length"] = str(file_size)
    return headers


@router.get("/api/models")
def hf_list_models(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """HF-style model listing endpoint."""
    query = db.query(Model).filter(Model.is_private.is_(False))
    if search:
        query = query.filter(Model.model_id.contains(search) | Model.name.contains(search))

    models = query.order_by(Model.updated_at.desc()).limit(limit).all()
    return [
        {
            "_id": f"armswideopen:{model.id}",
            "id": model.model_id,
            "modelId": model.model_id,
            "sha": model.latest_revision,
            "lastModified": model.updated_at.isoformat(),
            "private": model.is_private,
            "downloads": model.downloads,
            "tags": [tag.strip() for tag in (model.tags or "").split(",") if tag.strip()],
            "siblings": _build_siblings(model),
        }
        for model in models
    ]


@router.get("/api/datasets")
def hf_list_datasets(
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """HF-style dataset listing endpoint."""
    query = db.query(Dataset).filter(Dataset.is_private.is_(False))
    if search:
        query = query.filter(Dataset.dataset_id.contains(search) | Dataset.name.contains(search))

    datasets = query.order_by(Dataset.updated_at.desc()).limit(limit).all()
    return [
        {
            "_id": f"openarms-dataset:{dataset.id}",
            "id": dataset.dataset_id,
            "datasetId": dataset.dataset_id,
            "sha": dataset.latest_revision,
            "lastModified": dataset.updated_at.isoformat(),
            "private": dataset.is_private,
            "downloads": dataset.downloads,
            "tags": [tag.strip() for tag in (dataset.tags or "").split(",") if tag.strip()],
            "siblings": _build_dataset_siblings(dataset),
        }
        for dataset in datasets
    ]


@router.get("/api/datasets/{repo_id:path}/revision/{revision}")
def hf_dataset_revision_info(repo_id: str, revision: str, db: Session = Depends(get_db)):
    """HF-style dataset info for a specific revision reference."""
    dataset = _get_public_dataset(repo_id, db)
    if not _is_valid_dataset_revision(dataset, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    return {
        "_id": f"openarms-dataset:{dataset.id}",
        "id": dataset.dataset_id,
        "sha": dataset.latest_revision,
        "lastModified": dataset.updated_at.isoformat(),
        "siblings": _build_dataset_siblings(dataset),
        "cardData": {"description": dataset.description or ""},
    }


@router.get("/api/datasets/{repo_id:path}/refs")
def hf_dataset_refs(repo_id: str, db: Session = Depends(get_db)):
    """HF-style refs endpoint for datasets."""
    dataset = _get_public_dataset(repo_id, db)
    return {
        "branches": [{"name": "main", "targetCommit": dataset.latest_revision}],
        "converts": [],
        "tags": [],
    }


@router.get("/api/datasets/{repo_id:path}/tree/{revision}/{path:path}")
def hf_dataset_tree(repo_id: str, revision: str, path: str, db: Session = Depends(get_db)):
    """HF-style tree listing endpoint for a dataset revision."""
    dataset = _get_public_dataset(repo_id, db)
    if not _is_valid_dataset_revision(dataset, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    prefix = path.strip("/")
    if prefix:
        prefix = f"{prefix}/"

    entries = []
    for item in storage_service.list_repo_files(dataset.dataset_id):
        filename = item["filename"]
        if not filename.startswith(prefix):
            continue
        relative = filename[len(prefix):]
        if "/" in relative:
            continue
        entries.append(
            {
                "type": "file",
                "oid": "",
                "size": item["file_size"] or 0,
                "path": filename,
            }
        )
    return entries


@router.get("/api/datasets/{repo_id:path}")
def hf_dataset_info(repo_id: str, db: Session = Depends(get_db)):
    """HF-style dataset info endpoint used by datasets clients."""
    dataset = _get_public_dataset(repo_id, db)
    return {
        "_id": f"openarms-dataset:{dataset.id}",
        "id": dataset.dataset_id,
        "author": dataset.dataset_id.split("/", 1)[0] if "/" in dataset.dataset_id else dataset.dataset_id,
        "sha": dataset.latest_revision,
        "lastModified": dataset.updated_at.isoformat(),
        "private": dataset.is_private,
        "tags": [tag.strip() for tag in (dataset.tags or "").split(",") if tag.strip()],
        "downloads": dataset.downloads,
        "siblings": _build_dataset_siblings(dataset),
        "cardData": {"description": dataset.description or ""},
    }


@router.get("/datasets/{repo_id:path}/resolve/{revision}/{filename:path}")
def hf_resolve_dataset_file(
    repo_id: str,
    revision: str,
    filename: str,
    db: Session = Depends(get_db),
):
    """HF-style resolve endpoint for dataset file download."""
    dataset = _get_public_dataset(repo_id, db)
    if not _is_valid_dataset_revision(dataset, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    try:
        file_path = storage_service.read_repo_file(repo_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    return FileResponse(path=str(Path(file_path)), filename=Path(file_path).name)


@router.head("/datasets/{repo_id:path}/resolve/{revision}/{filename:path}")
def hf_resolve_dataset_file_head(
    repo_id: str,
    revision: str,
    filename: str,
    db: Session = Depends(get_db),
):
    """HF-style HEAD support for dataset file resolution."""
    dataset = _get_public_dataset(repo_id, db)
    if not _is_valid_dataset_revision(dataset, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    try:
        file_path = storage_service.read_repo_file(repo_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    return FileResponse(path=str(Path(file_path)), filename=Path(file_path).name)


@router.get("/api/models/{repo_id:path}/revision/{revision}")
def hf_model_revision_info(repo_id: str, revision: str, db: Session = Depends(get_db)):
    """HF-style model info for a specific revision reference."""
    model = _get_public_model(repo_id, db)
    if not _is_valid_revision(model, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    return {
        "_id": f"armswideopen:{model.id}",
        "id": model.model_id,
        "sha": model.latest_revision,
        "lastModified": model.updated_at.isoformat(),
        "siblings": _build_siblings(model),
        "cardData": {"description": model.description or ""},
    }


@router.get("/api/models/{repo_id:path}/refs")
def hf_model_refs(repo_id: str, db: Session = Depends(get_db)):
    """HF-style refs endpoint with basic branch metadata."""
    model = _get_public_model(repo_id, db)
    return {
        "branches": [{"name": "main", "targetCommit": model.latest_revision}],
        "converts": [],
        "tags": [],
    }


@router.get("/api/models/{repo_id:path}/tree/{revision}/{path:path}")
def hf_model_tree(repo_id: str, revision: str, path: str, db: Session = Depends(get_db)):
    """HF-style tree listing endpoint for a model revision."""
    model = _get_public_model(repo_id, db)
    if not _is_valid_revision(model, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    prefix = path.strip("/")
    if prefix:
        prefix = f"{prefix}/"

    entries = []
    for item in model.files:
        if not item.filename.startswith(prefix):
            continue
        relative = item.filename[len(prefix):]
        if "/" in relative:
            continue
        entries.append(
            {
                "type": "file",
                "oid": item.file_hash or "",
                "size": item.file_size or 0,
                "path": item.filename,
            }
        )
    return entries


@router.get("/api/models/{repo_id:path}")
def hf_model_info(repo_id: str, db: Session = Depends(get_db)):
    """HF-style model info endpoint used by huggingface_hub."""
    model = _get_public_model(repo_id, db)
    return {
        "_id": f"armswideopen:{model.id}",
        "id": model.model_id,
        "author": model.model_id.split("/", 1)[0] if "/" in model.model_id else model.model_id,
        "sha": model.latest_revision,
        "lastModified": model.updated_at.isoformat(),
        "private": model.is_private,
        "tags": [tag.strip() for tag in (model.tags or "").split(",") if tag.strip()],
        "downloads": model.downloads,
        "siblings": _build_siblings(model),
        "cardData": {"description": model.description or ""},
    }


@router.get("/{repo_id:path}/resolve/{revision}/{filename:path}")
def hf_resolve_file(
    repo_id: str,
    revision: str,
    filename: str,
    db: Session = Depends(get_db),
):
    """HF-style resolve endpoint for file download."""
    model = _get_public_model(repo_id, db)
    if not _is_valid_revision(model, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    file_meta = next((item for item in model.files if item.filename == filename), None)
    if not file_meta:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    try:
        file_path = storage_service.read_model_file(repo_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    headers = _hf_resolve_headers(model.latest_revision, file_meta.file_hash, file_meta.file_size)
    return FileResponse(path=str(Path(file_path)), filename=Path(file_path).name, headers=headers)


@router.head("/{repo_id:path}/resolve/{revision}/{filename:path}")
def hf_resolve_file_head(
    repo_id: str,
    revision: str,
    filename: str,
    db: Session = Depends(get_db),
):
    """HF-style HEAD support for model file resolution."""
    model = _get_public_model(repo_id, db)
    if not _is_valid_revision(model, revision):
        raise HTTPException(status_code=404, detail="Revision not found")

    file_meta = next((item for item in model.files if item.filename == filename), None)
    if not file_meta:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    try:
        file_path = storage_service.read_model_file(repo_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    headers = _hf_resolve_headers(model.latest_revision, file_meta.file_hash, file_meta.file_size)
    return FileResponse(path=str(Path(file_path)), filename=Path(file_path).name, headers=headers)
