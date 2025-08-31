"""
Project Model
Defines the database model and Pydantic schemas for projects.
"""
import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict
from app import db

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    organization_id = db.Column(db.String(36), nullable=False)
    status = db.Column(db.String(32), nullable=False, default='not_started')
    created_by = db.Column(db.String(36), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    due_date: date | None = None
    organization_id: str
    status: str = 'not_started'

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str
    created_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
