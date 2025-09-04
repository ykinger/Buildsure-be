"""
CodeMatrixStatus Model
Defines the database model and Pydantic schemas for code matrix status.
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app import db

class CodeMatrixStatus(db.Model):
    __tablename__ = 'code_matrix_status'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(db.String(36), nullable=False)
    project_id = db.Column(db.String(36), db.ForeignKey('buildsure.projects.id'), nullable=False)
    code_matrix_questions = db.Column(db.Text, nullable=True)
    clarifying_questions = db.Column(db.Text, nullable=True)
    curr_section = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

class CodeMatrixStatusBase(BaseModel):
    org_id: str
    project_id: str
    code_matrix_questions: str | None = None
    clarifying_questions: str | None = None
    curr_section: str | None = None

class CodeMatrixStatusCreate(CodeMatrixStatusBase):
    pass

class CodeMatrixStatusResponse(CodeMatrixStatusBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
