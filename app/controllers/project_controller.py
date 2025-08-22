"""
Project Controller
Handles API endpoints for project operations.
"""
from flask import Blueprint, request, jsonify
from app.services.project_service import ProjectService

project_bp = Blueprint('project_bp', __name__)

@project_bp.route('/api/v1/organizations/<org_id>/projects', methods=['POST'])
def create_project(org_id):
    payload = request.get_json()
    if not payload or not payload.get('name'):
        return jsonify({'error': 'Missing required field: name'}), 400
    project = ProjectService.create_project(org_id, payload)
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'dueDate': str(project.due_date),
        'organizationId': project.organization_id,
        'status': project.status
    }), 201
