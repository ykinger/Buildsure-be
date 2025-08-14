"""
Base model with common fields and functionality
"""
from datetime import datetime
from typing import Dict, Any
from app import db


class BaseModel(db.Model):
    """
    Base model class with common fields and methods.
    All models should inherit from this class.
    """
    
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def save(self) -> 'BaseModel':
        """Save the current instance to the database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self) -> None:
        """Delete the current instance from the database."""
        db.session.delete(self)
        db.session.commit()
    
    @classmethod
    def create(cls, **kwargs) -> 'BaseModel':
        """Create a new instance and save it to the database."""
        instance = cls(**kwargs)
        return instance.save()
