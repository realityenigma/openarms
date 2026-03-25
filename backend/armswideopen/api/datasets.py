"""Datasets API routes"""
import csv
import json
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from armswideopen.db import get_db, Dataset, User
from armswideopen.schemas.dataset import DatasetCreate, DatasetUpdate, DatasetResponse, DatasetListResponse
from armswideopen.api.auth import get_current_user
from armswideopen.services.storage import storage_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


def _validate_repo_owner(repo_id: str, username: str) -> None:
    if "/" not in repo_id:
        raise HTTPException(status_code=422, detail="Repository ID must be in the format username/repo-name")
    owner, name = repo_id.split("/", 1)
    if not owner or not name:
        raise HTTPException(status_code=422, detail="Repository ID must be in the format username/repo-name")
    if owner != username:
        raise HTTPException(status_code=403, detail=f"Repository owner must match authenticated user: {username}")


@router.get("", response_model=DatasetListResponse)
def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    """List all public datasets with pagination"""
    query = db.query(Dataset).filter(Dataset.is_private == False)
    
    if search:
        query = query.filter(Dataset.dataset_id.contains(search) | Dataset.name.contains(search))
    
    total = query.count()
    datasets = query.offset(skip).limit(limit).all()
    
    return DatasetListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        datasets=[DatasetResponse.model_validate(d) for d in datasets],
    )


@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_data: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new dataset"""
    _validate_repo_owner(dataset_data.dataset_id, current_user.username)

    existing = db.query(Dataset).filter(Dataset.dataset_id == dataset_data.dataset_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Dataset ID already exists")
    
    dataset = Dataset(
        dataset_id=dataset_data.dataset_id,
        name=dataset_data.name,
        description=dataset_data.description,
        tags=dataset_data.tags,
        is_private=dataset_data.is_private,
        author_id=current_user.id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    return DatasetResponse.model_validate(dataset)


@router.post("/files", response_model=DatasetResponse)
async def upload_dataset_file_by_query(
    dataset_id: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload file using query param dataset_id to avoid path parsing ambiguity."""
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this dataset")

    with NamedTemporaryFile(delete=False) as temp:
        temp_path = Path(temp.name)
        content = await file.read()
        temp.write(content)

    try:
        storage_service.save_repo_file(dataset_id, file.filename, temp_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    return DatasetResponse.model_validate(dataset)


@router.get("/files")
def list_dataset_files_by_query(dataset_id: str = Query(...), db: Session = Depends(get_db)):
    """List files for a dataset using query param (safe for slash-containing IDs)."""
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    files = storage_service.list_repo_files(dataset_id)
    return {
        "dataset_id": dataset.dataset_id,
        "files": [
            {
                "filename": item["filename"],
                "file_size": item["file_size"],
                "created_at": datetime.fromtimestamp(item["created_at"]).isoformat(),
            }
            for item in files
        ],
    }


@router.get("/preview")
def preview_dataset_file(dataset_id: str = Query(...), filename: str = Query(...), db: Session = Depends(get_db)):
    """Preview structured rows from a dataset file."""
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.is_private:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        file_path = storage_service.read_repo_file(dataset_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    suffix = file_path.suffix.lower()
    max_rows = 50
    max_bytes = 1024 * 1024

    if file_path.stat().st_size > max_bytes:
        raise HTTPException(status_code=422, detail="File too large for preview (max 1MB)")

    if suffix == ".csv":
        with file_path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.DictReader(infile)
            rows = []
            for row in reader:
                rows.append(row)
                if len(rows) >= max_rows:
                    break
            return {
                "dataset_id": dataset_id,
                "filename": filename,
                "format": "csv",
                "columns": reader.fieldnames or [],
                "rows": rows,
                "truncated": len(rows) >= max_rows,
            }

    if suffix in {".jsonl", ".ndjson"}:
        rows = []
        columns = set()
        with file_path.open("r", encoding="utf-8") as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if isinstance(obj, dict):
                    columns.update(obj.keys())
                rows.append(obj)
                if len(rows) >= max_rows:
                    break
        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "format": "jsonl",
            "columns": sorted(columns),
            "rows": rows,
            "truncated": len(rows) >= max_rows,
        }

    if suffix == ".json":
        with file_path.open("r", encoding="utf-8") as infile:
            obj = json.load(infile)

        if isinstance(obj, list):
            rows = obj[:max_rows]
            columns = sorted({k for item in rows if isinstance(item, dict) for k in item.keys()})
            return {
                "dataset_id": dataset_id,
                "filename": filename,
                "format": "json",
                "columns": columns,
                "rows": rows,
                "truncated": len(obj) > max_rows,
            }

        if isinstance(obj, dict):
            return {
                "dataset_id": dataset_id,
                "filename": filename,
                "format": "json",
                "columns": sorted(obj.keys()),
                "rows": [obj],
                "truncated": False,
            }

    if suffix in {".txt", ".md"}:
        lines = []
        with file_path.open("r", encoding="utf-8") as infile:
            for idx, line in enumerate(infile):
                lines.append({"line": idx + 1, "text": line.rstrip("\n")})
                if len(lines) >= max_rows:
                    break
        return {
            "dataset_id": dataset_id,
            "filename": filename,
            "format": "text",
            "columns": ["line", "text"],
            "rows": lines,
            "truncated": len(lines) >= max_rows,
        }

    raise HTTPException(status_code=422, detail="Unsupported preview format. Use CSV, JSON, JSONL, TXT, or MD.")


@router.get("/{dataset_id:path}", response_model=DatasetResponse)
def get_dataset(dataset_id: str, db: Session = Depends(get_db)):
    """Get dataset details by ID"""
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.is_private:
        raise HTTPException(status_code=403, detail="Access denied")

    dataset.downloads += 1
    db.commit()

    return DatasetResponse.model_validate(dataset)


@router.put("/{dataset_id:path}", response_model=DatasetResponse)
def update_dataset(
    dataset_id: str,
    dataset_data: DatasetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a dataset"""
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this dataset")

    for field, value in dataset_data.model_dump(exclude_unset=True).items():
        setattr(dataset, field, value)

    db.commit()
    db.refresh(dataset)

    return DatasetResponse.model_validate(dataset)


@router.delete("/{dataset_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a dataset"""
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    if dataset.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this dataset")

    db.delete(dataset)
    db.commit()
