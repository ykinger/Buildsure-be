# BuildSure API v2.0 - Swagger Documentation

## Overview

The BuildSure API is a FastAPI-based backend system for project management with complete CRUD operations for organizations, users, projects, and sections. This API provides a modern, type-safe, and well-documented interface for managing project workflows.

## Base Information

- **Version**: 2.0.0
- **Base URL**: `http://localhost:8000` (Development)
- **Production URL**: `https://api.buildsure.com`
- **Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Authentication

Currently, the API does not require authentication. This may be added in future versions.

## Data Models

### Organization
- **id**: UUID (Primary Key)
- **name**: String (Required, max 255 chars)
- **description**: String (Optional)
- **created_at**: DateTime (Auto-generated)
- **updated_at**: DateTime (Auto-updated)

### User
- **id**: UUID (Primary Key)
- **org_id**: UUID (Foreign Key to Organization, Required)
- **name**: String (Required, max 255 chars)
- **email**: String (Required, unique, email format, max 255 chars)
- **created_at**: DateTime (Auto-generated)
- **updated_at**: DateTime (Auto-updated)

### Project
- **id**: UUID (Primary Key)
- **org_id**: UUID (Foreign Key to Organization, Required)
- **user_id**: UUID (Foreign Key to User, Required)
- **name**: String (Required, max 255 chars)
- **description**: String (Optional)
- **status**: Enum (not_started, in_progress, completed, on_hold)
- **current_section**: Integer (Default: 0)
- **total_sections**: Integer (Default: 0)
- **completed_sections**: Integer (Default: 0)
- **created_at**: DateTime (Auto-generated)
- **updated_at**: DateTime (Auto-updated)

### Section
- **id**: UUID (Primary Key)
- **project_id**: UUID (Foreign Key to Project, Required)
- **section_number**: Integer (Required, min: 1)
- **status**: Enum (pending, in_progress, completed)
- **user_input**: JSON Object (Optional)
- **draft_output**: JSON Object (Optional)
- **final_output**: JSON Object (Optional)
- **created_at**: DateTime (Auto-generated)
- **updated_at**: DateTime (Auto-updated)

## API Endpoints

### Health Endpoints

#### GET `/`
- **Summary**: Root endpoint
- **Description**: Welcome message and API information
- **Response**: 200 OK
```json
{
  "message": "Welcome to BuildSure API v2.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

#### GET `/api/v1/health`
- **Summary**: Health check
- **Description**: Check API health and database connectivity
- **Response**: 200 OK
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}
```

### Organization Endpoints

#### GET `/api/v1/organizations/`
- **Summary**: List organizations
- **Description**: Get paginated list of organizations
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
- **Response**: 200 OK - Paginated list of organizations

#### POST `/api/v1/organizations/`
- **Summary**: Create organization
- **Description**: Create a new organization
- **Request Body**:
```json
{
  "name": "Acme Corporation",
  "description": "A leading technology company"
}
```
- **Responses**:
  - 201 Created - Organization created successfully
  - 400 Bad Request - Invalid input data

#### GET `/api/v1/organizations/{organization_id}`
- **Summary**: Get organization
- **Description**: Get organization by ID
- **Path Parameters**:
  - `organization_id`: UUID (required)
- **Responses**:
  - 200 OK - Organization details
  - 404 Not Found - Organization not found

#### PUT `/api/v1/organizations/{organization_id}`
- **Summary**: Update organization
- **Description**: Update organization by ID
- **Path Parameters**:
  - `organization_id`: UUID (required)
- **Request Body**:
```json
{
  "name": "Updated Corporation",
  "description": "Updated description"
}
```
- **Responses**:
  - 200 OK - Organization updated successfully
  - 404 Not Found - Organization not found

#### DELETE `/api/v1/organizations/{organization_id}`
- **Summary**: Delete organization
- **Description**: Delete organization by ID (cascades to users and projects)
- **Path Parameters**:
  - `organization_id`: UUID (required)
- **Responses**:
  - 204 No Content - Organization deleted successfully
  - 404 Not Found - Organization not found

### User Endpoints

#### GET `/api/v1/users/`
- **Summary**: List users
- **Description**: Get paginated list of users with optional organization filtering
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
  - `org_id`: UUID (optional) - Filter by organization ID
- **Response**: 200 OK - Paginated list of users

#### POST `/api/v1/users/`
- **Summary**: Create user
- **Description**: Create a new user
- **Request Body**:
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "org_id": "123e4567-e89b-12d3-a456-426614174000"
}
```
- **Responses**:
  - 201 Created - User created successfully
  - 400 Bad Request - Organization not found or email already exists

#### GET `/api/v1/users/{user_id}`
- **Summary**: Get user
- **Description**: Get user by ID
- **Path Parameters**:
  - `user_id`: UUID (required)
- **Responses**:
  - 200 OK - User details
  - 404 Not Found - User not found

#### PUT `/api/v1/users/{user_id}`
- **Summary**: Update user
- **Description**: Update user by ID
- **Path Parameters**:
  - `user_id`: UUID (required)
- **Request Body**:
```json
{
  "name": "John Smith",
  "email": "john.smith@example.com",
  "org_id": "123e4567-e89b-12d3-a456-426614174000"
}
```
- **Responses**:
  - 200 OK - User updated successfully
  - 400 Bad Request - Organization not found or email already exists
  - 404 Not Found - User not found

#### DELETE `/api/v1/users/{user_id}`
- **Summary**: Delete user
- **Description**: Delete user by ID (cascades to projects)
- **Path Parameters**:
  - `user_id`: UUID (required)
- **Responses**:
  - 204 No Content - User deleted successfully
  - 404 Not Found - User not found

#### GET `/api/v1/users/organizations/{org_id}/users`
- **Summary**: List users by organization
- **Description**: Get paginated list of users for a specific organization
- **Path Parameters**:
  - `org_id`: UUID (required)
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
- **Responses**:
  - 200 OK - List of users in organization
  - 404 Not Found - Organization not found

### Project Endpoints

#### GET `/api/v1/projects/`
- **Summary**: List projects
- **Description**: Get paginated list of projects with optional filtering
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
  - `org_id`: UUID (optional) - Filter by organization ID
  - `user_id`: UUID (optional) - Filter by user ID
- **Response**: 200 OK - Paginated list of projects

#### POST `/api/v1/projects/`
- **Summary**: Create project
- **Description**: Create a new project
- **Request Body**:
```json
{
  "name": "Website Redesign",
  "description": "Complete redesign of company website",
  "status": "not_started",
  "total_sections": 5,
  "org_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": "123e4567-e89b-12d3-a456-426614174001"
}
```
- **Responses**:
  - 201 Created - Project created successfully
  - 400 Bad Request - Organization or user not found, or user doesn't belong to organization

#### GET `/api/v1/projects/{project_id}`
- **Summary**: Get project
- **Description**: Get project by ID
- **Path Parameters**:
  - `project_id`: UUID (required)
- **Responses**:
  - 200 OK - Project details
  - 404 Not Found - Project not found

#### PUT `/api/v1/projects/{project_id}`
- **Summary**: Update project
- **Description**: Update project by ID
- **Path Parameters**:
  - `project_id`: UUID (required)
- **Request Body**:
```json
{
  "name": "Updated Website Redesign",
  "status": "in_progress",
  "current_section": 2,
  "completed_sections": 1
}
```
- **Responses**:
  - 200 OK - Project updated successfully
  - 400 Bad Request - Organization or user not found, or user doesn't belong to organization
  - 404 Not Found - Project not found

#### DELETE `/api/v1/projects/{project_id}`
- **Summary**: Delete project
- **Description**: Delete project by ID (cascades to sections)
- **Path Parameters**:
  - `project_id`: UUID (required)
- **Responses**:
  - 204 No Content - Project deleted successfully
  - 404 Not Found - Project not found

#### GET `/api/v1/projects/organizations/{org_id}/projects`
- **Summary**: List projects by organization
- **Description**: Get paginated list of projects for a specific organization
- **Path Parameters**:
  - `org_id`: UUID (required)
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
- **Responses**:
  - 200 OK - List of projects in organization
  - 404 Not Found - Organization not found

#### GET `/api/v1/projects/users/{user_id}/projects`
- **Summary**: List projects by user
- **Description**: Get paginated list of projects for a specific user
- **Path Parameters**:
  - `user_id`: UUID (required)
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
- **Responses**:
  - 200 OK - List of projects for user
  - 404 Not Found - User not found

### Section Endpoints

#### GET `/api/v1/sections/`
- **Summary**: List sections
- **Description**: Get paginated list of sections with optional project filtering
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
  - `project_id`: UUID (optional) - Filter by project ID
- **Response**: 200 OK - Paginated list of sections

#### POST `/api/v1/sections/`
- **Summary**: Create section
- **Description**: Create a new section
- **Request Body**:
```json
{
  "section_number": 1,
  "status": "in_progress",
  "project_id": "123e4567-e89b-12d3-a456-426614174002",
  "user_input": {
    "requirements": "Build a login system",
    "specifications": "Use OAuth 2.0"
  }
}
```
- **Responses**:
  - 201 Created - Section created successfully
  - 400 Bad Request - Project not found or section number already exists

#### GET `/api/v1/sections/{section_id}`
- **Summary**: Get section
- **Description**: Get section by ID
- **Path Parameters**:
  - `section_id`: UUID (required)
- **Responses**:
  - 200 OK - Section details
  - 404 Not Found - Section not found

#### PUT `/api/v1/sections/{section_id}`
- **Summary**: Update section
- **Description**: Update section by ID
- **Path Parameters**:
  - `section_id`: UUID (required)
- **Request Body**:
```json
{
  "status": "completed",
  "draft_output": {
    "code": "// Login component code",
    "documentation": "Login system documentation"
  },
  "final_output": {
    "deliverable": "Complete login system",
    "files": ["login.js", "auth.js"]
  }
}
```
- **Responses**:
  - 200 OK - Section updated successfully
  - 400 Bad Request - Project not found or section number already exists
  - 404 Not Found - Section not found

#### DELETE `/api/v1/sections/{section_id}`
- **Summary**: Delete section
- **Description**: Delete section by ID
- **Path Parameters**:
  - `section_id`: UUID (required)
- **Responses**:
  - 204 No Content - Section deleted successfully
  - 404 Not Found - Section not found

#### GET `/api/v1/sections/projects/{project_id}/sections`
- **Summary**: List sections by project
- **Description**: Get paginated list of sections for a specific project
- **Path Parameters**:
  - `project_id`: UUID (required)
- **Query Parameters**:
  - `page`: Integer (min: 1, default: 1) - Page number
  - `size`: Integer (min: 1, max: 100, default: 10) - Page size
- **Responses**:
  - 200 OK - List of sections in project
  - 404 Not Found - Project not found

## Response Formats

### Success Responses

All successful responses follow consistent patterns:

#### Single Item Response
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Example Name",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:00:00Z"
}
```

#### Paginated List Response
```json
{
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Example Name"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "pages": 1
}
```

### Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common error scenarios:
- **400 Bad Request**: Invalid input data, missing required fields, or business logic violations
- **404 Not Found**: Requested resource does not exist
- **500 Internal Server Error**: Unexpected server error

## Relationship Enforcement

The API enforces proper relationships between entities:

1. **Users must belong to an Organization**: When creating or updating a user, the `org_id` must reference an existing organization.

2. **Projects must have valid Organization and User**: When creating or updating a project, both `org_id` and `user_id` must be valid, and the user must belong to the specified organization.

3. **Sections must belong to a Project**: When creating or updating a section, the `project_id` must reference an existing project.

4. **Cascade Deletes**: 
   - Deleting an organization will delete all associated users and projects
   - Deleting a user will delete all associated projects
   - Deleting a project will delete all associated sections

## Status Enums

### Project Status
- `not_started`: Project has not been started
- `in_progress`: Project is currently being worked on
- `completed`: Project has been completed
- `on_hold`: Project is temporarily paused

### Section Status
- `pending`: Section is waiting to be started
- `in_progress`: Section is currently being worked on
- `completed`: Section has been completed

## JSON Fields

The Section model includes three JSON fields for flexible data storage:

- **user_input**: Stores user requirements, specifications, and input data
- **draft_output**: Stores preliminary results, code drafts, and work-in-progress
- **final_output**: Stores completed deliverables, final code, and finished work

These fields accept any valid JSON structure, allowing for flexible content storage based on project needs.

## Getting Started

1. **Start the server**: `python run.py`
2. **Access the API**: `http://localhost:8000`
3. **View documentation**: `http://localhost:8000/docs`
4. **Create an organization**: POST to `/api/v1/organizations/`
5. **Create a user**: POST to `/api/v1/users/`
6. **Create a project**: POST to `/api/v1/projects/`
7. **Create sections**: POST to `/api/v1/sections/`

## Development Tools

- **Interactive API Documentation**: Available at `/docs` (Swagger UI)
- **Alternative Documentation**: Available at `/redoc` (ReDoc)
- **VSCode Debug Configurations**: Two debug options available in `.vscode/launch.json`
- **Database Migrations**: Managed with Alembic
- **Type Safety**: Full Pydantic validation and FastAPI type hints

This API provides a robust foundation for project management applications with proper relationship enforcement, comprehensive validation, and excellent developer experience.
