"""Schemas for dataset-related APIs"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class DatasetBase(BaseModel):
    """Base dataset schema"""
    name: str
    description: Optional[str] = None
    tags: Optional[str] = None
    is_private: bool = False


class DatasetCreate(DatasetBase):
    """Schema for creating a dataset"""
    dataset_id: str


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset"""
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    is_private: Optional[bool] = None


class DatasetResponse(DatasetBase):
    """Schema for dataset response"""
    id: int
    dataset_id: str
    author_id: int
    downloads: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DatasetListResponse(BaseModel):
    """Schema for dataset list response"""
    total: int
    page: int
    page_size: int
    datasets: list[DatasetResponse]
