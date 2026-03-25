"""Models API routes"""
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from armswideopen.db import get_db, Model, User, ModelFile
from armswideopen.schemas.model import ModelCreate, ModelUpdate, ModelResponse, ModelListResponse
from armswideopen.api.auth import get_current_user
from armswideopen.services.storage import storage_service

router = APIRouter(prefix="/models", tags=["models"])


def _validate_repo_owner(repo_id: str, username: str) -> None:
    if "/" not in repo_id:
        raise HTTPException(status_code=422, detail="Repository ID must be in the format username/repo-name")
    owner, name = repo_id.split("/", 1)
    if not owner or not name:
        raise HTTPException(status_code=422, detail="Repository ID must be in the format username/repo-name")
    if owner != username:
        raise HTTPException(status_code=403, detail=f"Repository owner must match authenticated user: {username}")


@router.get("", response_model=ModelListResponse)
def list_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    tags: str = Query(None),
    db: Session = Depends(get_db),
):
    """List all public models with pagination and filtering"""
    query = db.query(Model).filter(Model.is_private == False)
    
    if search:
        query = query.filter(Model.model_id.contains(search) | Model.name.contains(search))
    
    if tags:
        query = query.filter(Model.tags.contains(tags))
    
    total = query.count()
    models = query.offset(skip).limit(limit).all()
    
    return ModelListResponse(
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        models=[ModelResponse.model_validate(m) for m in models],
    )


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new model"""
    _validate_repo_owner(model_data.model_id, current_user.username)

    existing = db.query(Model).filter(Model.model_id == model_data.model_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Model ID already exists")
    
    model = Model(
        model_id=model_data.model_id,
        name=model_data.name,
        description=model_data.description,
        model_type=model_data.model_type,
        tags=model_data.tags,
        is_private=model_data.is_private,
        author_id=current_user.id,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    
    return ModelResponse.model_validate(model)


@router.post("/{model_id:path}/files", response_model=ModelResponse)
async def upload_model_file(
    model_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a file for a model and track metadata."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this model")

    with NamedTemporaryFile(delete=False) as temp:
        temp_path = Path(temp.name)
        content = await file.read()
        temp.write(content)

    try:
        saved = storage_service.save_model_file(model_id, file.filename, temp_path)
        revision = storage_service.commit_file_change(
            model_id,
            file.filename,
            f"Add/update model file {file.filename}",
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    existing_file = (
        db.query(ModelFile)
        .filter(ModelFile.model_id == model.id, ModelFile.filename == file.filename)
        .first()
    )
    if existing_file:
        existing_file.file_size = saved["size"]
        existing_file.file_hash = saved["sha256"]
    else:
        db_file = ModelFile(
            model_id=model.id,
            filename=file.filename,
            file_size=saved["size"],
            file_hash=saved["sha256"],
        )
        db.add(db_file)

    model.latest_revision = revision
    db.commit()
    db.refresh(model)

    return ModelResponse.model_validate(model)


@router.get("/{model_id:path}/files")
def list_model_files(model_id: str, db: Session = Depends(get_db)):
    """List files for a model."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_id": model.model_id,
        "latest_revision": model.latest_revision,
        "files": [
            {
                "filename": file.filename,
                "file_size": file.file_size,
                "file_hash": file.file_hash,
                "created_at": file.created_at.isoformat(),
            }
            for file in model.files
        ],
    }


@router.get("/files")
def list_model_files_by_query(model_id: str = Query(...), db: Session = Depends(get_db)):
    """List files for a model using query param (safe for slash-containing IDs)."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    return {
        "model_id": model.model_id,
        "latest_revision": model.latest_revision,
        "files": [
            {
                "filename": file.filename,
                "file_size": file.file_size,
                "file_hash": file.file_hash,
                "created_at": file.created_at.isoformat(),
            }
            for file in model.files
        ],
    }


@router.post("/files", response_model=ModelResponse)
async def upload_model_file_by_query(
    model_id: str = Query(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload file using query param model_id to avoid path parsing ambiguity."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload to this model")

    with NamedTemporaryFile(delete=False) as temp:
        temp_path = Path(temp.name)
        content = await file.read()
        temp.write(content)

    try:
        saved = storage_service.save_model_file(model_id, file.filename, temp_path)
        revision = storage_service.commit_file_change(
            model_id,
            file.filename,
            f"Add/update model file {file.filename}",
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()

    existing_file = (
        db.query(ModelFile)
        .filter(ModelFile.model_id == model.id, ModelFile.filename == file.filename)
        .first()
    )
    if existing_file:
        existing_file.file_size = saved["size"]
        existing_file.file_hash = saved["sha256"]
    else:
        db_file = ModelFile(
            model_id=model.id,
            filename=file.filename,
            file_size=saved["size"],
            file_hash=saved["sha256"],
        )
        db.add(db_file)

    model.latest_revision = revision
    db.commit()
    db.refresh(model)

    return ModelResponse.model_validate(model)


@router.get("/{model_id:path}/files/{filename:path}")
def download_model_file(
    model_id: str,
    filename: str,
    db: Session = Depends(get_db),
):
    """Download a specific model file."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.is_private:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        file_path = storage_service.read_model_file(model_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    return FileResponse(path=str(file_path), filename=file_path.name)


@router.get("/file")
def download_model_file_by_query(
    model_id: str = Query(...),
    filename: str = Query(...),
    db: Session = Depends(get_db),
):
    """Download file using query params (safe for slash-containing IDs)."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.is_private:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        file_path = storage_service.read_model_file(model_id, filename)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}") from exc

    return FileResponse(path=str(file_path), filename=file_path.name)


@router.get("/{model_id:path}", response_model=ModelResponse)
def get_model(model_id: str, db: Session = Depends(get_db)):
    """Get model details by ID."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.is_private:
        raise HTTPException(status_code=403, detail="Access denied")

    model.downloads += 1
    db.commit()

    return ModelResponse.model_validate(model)


@router.put("/{model_id:path}", response_model=ModelResponse)
def update_model(
    model_id: str,
    model_data: ModelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a model."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this model")

    for field, value in model_data.model_dump(exclude_unset=True).items():
        setattr(model, field, value)

    db.commit()
    db.refresh(model)

    return ModelResponse.model_validate(model)


@router.delete("/{model_id:path}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a model."""
    model = db.query(Model).filter(Model.model_id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if model.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this model")

    db.delete(model)
    db.commit()
