"""
Convo Model and Schemas
Defines the database model and Pydantic schemas for conversations.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app import db

class Convo(db.Model):
    __tablename__ = 'convo'
    __table_args__ = {'schema': 'buildsure'}

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(db.String(36), nullable=False)
    project_id = db.Column(db.String(36), db.ForeignKey('buildsure.projects.id'), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class ConvoBase(BaseModel):
    org_id: str
    project_id: str
    content: str | None = None

class ConvoCreate(ConvoBase):
    pass

class ConvoResponse(ConvoBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
