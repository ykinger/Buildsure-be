from typing import Optional
from datetime import datetime
from app.database import CustomBase
from sqlmodel import Field, Relationship
from sqlalchemy import Column, DateTime, func

class User(CustomBase, table=True):
    __tablename__ = 'user'
    id: Optional[str] = Field(default=None, primary_key=True)
    organization_id: str = Field(foreign_key="organization.id")
    name: str
    email: str
    created_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    )
