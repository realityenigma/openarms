"""Database models for OpenArms"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from armswideopen.db.database import Base
import enum


class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    models = relationship("Model", back_populates="author")
    datasets = relationship("Dataset", back_populates="author")


class ModelType(str, enum.Enum):
    """Model type enumeration"""
    CLASSIFICATION = "classification"
    GENERATION = "generation"
    TRANSLATION = "translation"
    QUESTION_ANSWERING = "question-answering"
    SUMMARIZATION = "summarization"
    OTHER = "other"


class Model(Base):
    """Model registry model"""
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(255), unique=True, index=True, nullable=False)  # e.g., "username/model-name"
    name = Column(String(255), nullable=False)
    description = Column(Text)
    model_type = Column(Enum(ModelType), default=ModelType.OTHER)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Storage info
    git_lfs_repo = Column(String(512))  # Git LFS repository URL
    latest_revision = Column(String(40))  # Latest commit SHA
    
    # Metadata
    tags = Column(String(1000))  # CSV of tags
    downloads = Column(Integer, default=0)
    is_private = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="models")
    files = relationship("ModelFile", back_populates="model", cascade="all, delete-orphan")


class ModelFile(Base):
    """Model file metadata"""
    __tablename__ = "model_files"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    file_size = Column(Integer)  # in bytes
    file_hash = Column(String(64))  # SHA256 hash
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    model = relationship("Model", back_populates="files")


class Dataset(Base):
    """Dataset registry model"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Storage info
    git_lfs_repo = Column(String(512))
    latest_revision = Column(String(40))
    
    # Metadata
    tags = Column(String(1000))
    downloads = Column(Integer, default=0)
    is_private = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="datasets")
