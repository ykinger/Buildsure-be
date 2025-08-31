"""
Project Controller
Handles API endpoints for project operations.
"""
from flask import Blueprint, request, jsonify, current_app

project_bp = Blueprint('project_bp', __name__)


@project_bp.route('/api/v1/organizations/<org_id>/projects', methods=['POST'])
def create_project(org_id):
    payload = request.get_json()
    if not payload or not payload.get('name'):
        return jsonify({'error': 'Missing required field: name'}), 400
    
    # Use pre-initialized service from app context
    project_service = current_app.extensions['project_service']
    
    project = project_service.create_project(org_id, payload)
    
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'dueDate': str(project.due_date) if project.due_date else None,
        'organizationId': project.organization_id,
        'status': project.status,
        'createdAt': project.created_at.isoformat() if project.created_at else None,
        'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
        'createdBy': project.created_by
    }), 201


@project_bp.route('/api/v1/organizations/<org_id>/projects', methods=['GET'])
def get_projects(org_id):
    # Use pre-initialized service from app context
    project_service = current_app.extensions['project_service']
    
    projects = project_service.get_projects_by_org(org_id)
    
    result = []
    for project in projects:
        result.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'organizationId': project.organization_id,
            'status': project.status,
            'createdAt': project.created_at.isoformat() if project.created_at else None,
            'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
            'createdBy': project.created_by,
            'dueDate': str(project.due_date) if project.due_date else None
        })
    return jsonify(result), 200


@project_bp.route('/api/v1/organizations/<org_id>/projects/<project_id>/start', methods=['POST'])
def start_project_analysis(org_id, project_id):
    """
    Start AI analysis for a project.
    
    Args:
        org_id: Organization ID
        project_id: Project ID
        
    Returns:
        JSON response with AI analysis (question or decision)
    """
    try:
        # Use pre-initialized service from app context
        project_service = current_app.extensions['project_service']
        
        # Start project analysis
        analysis_result = project_service.start_project_analysis(org_id, project_id)
        
        return jsonify(analysis_result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error starting project analysis: {e}")
        return jsonify({
            "error": "Failed to start project analysis",
            "details": str(e)
        }), 500
