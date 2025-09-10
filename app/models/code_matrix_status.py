"""
CodeMatrixStatus Model
Defines the database model and Pydantic schemas for code matrix status.
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.hybrid import hybrid_property
from app import db

class CodeMatrixStatus(db.Model):
    __tablename__ = 'code_matrix_status'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = db.Column(db.String(36), nullable=False)
    project_id = db.Column(db.String(36), db.ForeignKey('projects.id'), nullable=False)
    _code_matrix_questions = db.Column('code_matrix_questions', db.Text, nullable=True)
    _clarifying_questions = db.Column('clarifying_questions', db.Text, nullable=True)
    curr_section = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'))
    updated_at = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'), onupdate=db.text('CURRENT_TIMESTAMP'))

    @hybrid_property
    def code_matrix_questions(self) -> Optional[List[str]]:
        """Get code_matrix_questions as a list."""
        if self._code_matrix_questions:
            try:
                return json.loads(self._code_matrix_questions)
            except (json.JSONDecodeError, TypeError):
                return []
        return None

    @code_matrix_questions.setter
    def code_matrix_questions(self, value: Optional[List[str]]):
        """Set code_matrix_questions from a list."""
        if value is not None:
            self._code_matrix_questions = json.dumps(value)
        else:
            self._code_matrix_questions = None

    @hybrid_property
    def clarifying_questions(self) -> Optional[List[str]]:
        """Get clarifying_questions as a list."""
        if self._clarifying_questions:
            try:
                return json.loads(self._clarifying_questions)
            except (json.JSONDecodeError, TypeError):
                return []
        return None

    @clarifying_questions.setter
    def clarifying_questions(self, value: Optional[List[str]]):
        """Set clarifying_questions from a list."""
        if value is not None:
            self._clarifying_questions = json.dumps(value)
        else:
            self._clarifying_questions = None

class CodeMatrixStatusBase(BaseModel):
    org_id: str
    project_id: str
    code_matrix_questions: list[str] | None = None
    clarifying_questions: list[str] | None = None
    curr_section: str | None = None

class CodeMatrixStatusCreate(CodeMatrixStatusBase):
    pass

class CodeMatrixStatusResponse(CodeMatrixStatusBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
