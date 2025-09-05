"""
Project Controller
Handles API endpoints for project operations.
"""
from typing import Dict, Any, List
from flask import Blueprint, request, jsonify, current_app, Response
from app.models.project import Project
from app.services.project_service import ProjectService

project_bp = Blueprint('project_bp', __name__)


@project_bp.route('/api/v1/organizations/<org_id>/projects', methods=['POST'])
def create_project(org_id: str) -> Response:
    payload: Dict[str, Any] = request.get_json()
    if not payload or not payload.get('name'):
        return jsonify({'error': 'Missing required field: name'}), 400
    
    # Use pre-initialized service from app context
    project_service: ProjectService = current_app.extensions['project_service']
    
    project: Project = project_service.create_project(org_id, payload)
    
    return jsonify({
        'id': project.id,
        'name': project.name,
        'description': project.description,
        'dueDate': str(project.due_date) if project.due_date else None,
        'organizationId': project.organization_id,
        'status': project.status,
        'currTask': project.curr_task,
        'createdAt': project.created_at.isoformat() if project.created_at else None,
        'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
        'createdBy': project.created_by
    }), 201


@project_bp.route('/api/v1/organizations/<org_id>/projects', methods=['GET'])
def get_projects(org_id: str) -> Response:
    # Use pre-initialized service from app context
    project_service: ProjectService = current_app.extensions['project_service']
    
    projects: List[Project] = project_service.get_projects_by_org(org_id)
    
    result: List[Dict[str, Any]] = []
    for project in projects:
        result.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'organizationId': project.organization_id,
            'status': project.status,
            'currTask': project.curr_task,
            'createdAt': project.created_at.isoformat() if project.created_at else None,
            'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
            'createdBy': project.created_by,
            'dueDate': str(project.due_date) if project.due_date else None
        })
    return jsonify(result), 200


@project_bp.route('/api/v1/organizations/<org_id>/projects/<project_id>', methods=['GET'])
def get_project(org_id: str, project_id: str) -> Response:
    """
    Get details of a single project.
    
    Args:
        org_id: Organization ID
        project_id: Project ID
        
    Returns:
        JSON response with project details
    """
    try:
        # Use pre-initialized service from app context
        project_service: ProjectService = current_app.extensions['project_service']
        
        # Get the project
        project: Project = project_service.get_project(org_id, project_id)
        
        return jsonify({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'dueDate': str(project.due_date) if project.due_date else None,
            'organizationId': project.organization_id,
            'status': project.status,
            'currTask': project.curr_task,
            'createdAt': project.created_at.isoformat() if project.created_at else None,
            'updatedAt': project.updated_at.isoformat() if project.updated_at else None,
            'createdBy': project.created_by
        }), 200
        
    except ValueError as e:
        current_app.logger.warning(f"Project not found: {e}")
        return jsonify({
            "error": "Project not found",
            "details": str(e)
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error getting project: {e}")
        return jsonify({
            "error": "Failed to get project",
            "details": str(e)
        }), 500


@project_bp.route('/api/v1/organizations/<org_id>/projects/<project_id>/start', methods=['POST'])
def start_project_analysis(org_id: str, project_id: str) -> Response:
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
        project_service: ProjectService = current_app.extensions['project_service']
        
        # Start project analysis
        analysis_result: Dict[str, Any] = project_service.start_project_analysis(org_id, project_id)
        
        return jsonify(analysis_result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error starting project analysis: {e}")
        return jsonify({
            "error": "Failed to start project analysis",
            "details": str(e)
        }), 500


@project_bp.route('/api/v1/organizations/<org_id>/projects/<project_id>/code-matrix/query', methods=['POST'])
def query_code_matrix(org_id: str, project_id: str) -> Response:
    """
    Query AI service with code matrix data.
    
    Args:
        org_id: Organization ID
        project_id: Project ID
        
    Returns:
        JSON response with AI analysis result
    """
    try:
        # Use pre-initialized service from app context
        project_service: ProjectService = current_app.extensions['project_service']
        
        # Query code matrix
        query_result: Dict[str, Any] = project_service.query_code_matrix(org_id, project_id)
        
        return jsonify(query_result), 200
        
    except ValueError as e:
        current_app.logger.warning(f"Code matrix status not found: {e}")
        return jsonify({
            "error": "Code matrix status not found",
            "details": str(e)
        }), 404
    except Exception as e:
        current_app.logger.error(f"Error querying code matrix: {e}")
        return jsonify({
            "error": "Failed to query code matrix",
            "details": str(e)
        }), 500
