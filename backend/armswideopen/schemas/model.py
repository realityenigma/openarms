"""Schemas for model-related APIs"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class ModelFileBase(BaseModel):
    """Base model file schema"""
    filename: str
    file_size: Optional[int] = None
    file_hash: Optional[str] = None


class ModelFileResponse(ModelFileBase):
    """Model file response schema"""
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ModelBase(BaseModel):
    """Base model schema"""
    model_config = ConfigDict(protected_namespaces=())

    name: str
    description: Optional[str] = None
    model_type: Optional[str] = "other"
    tags: Optional[str] = None
    is_private: bool = False


class ModelCreate(ModelBase):
    """Schema for creating a model"""
    model_id: str


class ModelUpdate(BaseModel):
    """Schema for updating a model"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    is_private: Optional[bool] = None


class ModelResponse(ModelBase):
    """Schema for model response"""
    id: int
    model_id: str
    author_id: int
    downloads: int
    latest_revision: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    files: List[ModelFileResponse] = []
    
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class ModelListResponse(BaseModel):
    """Schema for model list response"""
    total: int
    page: int
    page_size: int
    models: List[ModelResponse]
