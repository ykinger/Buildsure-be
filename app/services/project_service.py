"""
Project Service
Business logic for project creation and management.
"""
from app import db
from app.models.project import Project
from typing import Dict

class ProjectService:
    @staticmethod
    def create_project(org_id: str, payload: Dict) -> Project:
        project = Project(
            name=payload.get('name'),
            description=payload.get('description'),
            due_date=payload.get('dueDate'),
            organization_id=org_id,
            status='not_started'
        )
        db.session.add(project)
        db.session.commit()
        return project

    @staticmethod
    def get_projects_by_org(org_id: str):
        return Project.query.filter_by(organization_id=org_id).all()
