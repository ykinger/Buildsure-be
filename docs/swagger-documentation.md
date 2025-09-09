# BuildSure Backend API - Swagger Documentation

This document provides comprehensive Swagger/OpenAPI documentation for the BuildSure Backend API endpoints, specifically covering the Project Controller and Health Controller functionality.

## Overview

The BuildSure Backend API provides:
- **Project Management**: Create, retrieve, and manage building compliance projects
- **AI-Powered Analysis**: Query AI services for code matrix analysis and building code compliance
- **Health Monitoring**: System health checks for monitoring and diagnostics

## Documentation Location

The complete OpenAPI 3.0 specification is available at:
- **File**: `docs/openapi.yaml`
- **Format**: YAML (OpenAPI 3.0.0)

## API Endpoints Documented

### Project Controller (`/api/v1/organizations/{org_id}/projects`)

#### 1. Create Project
- **Method**: `POST`
- **Path**: `/api/v1/organizations/{org_id}/projects`
- **Description**: Creates a new building compliance project
- **Required Fields**: `name`
- **Optional Fields**: `description`, `dueDate`, `status`, `currTask`
- **Response**: Complete project object with generated ID and timestamps

#### 2. Get All Projects
- **Method**: `GET`
- **Path**: `/api/v1/organizations/{org_id}/projects`
- **Description**: Retrieves all projects for an organization
- **Response**: Array of project objects with current status and metadata

#### 3. Get Single Project
- **Method**: `GET`
- **Path**: `/api/v1/organizations/{org_id}/projects/{project_id}`
- **Description**: Retrieves detailed information about a specific project
- **Response**: Complete project object with all metadata

#### 4. Query Code Matrix
- **Method**: `POST`
- **Path**: `/api/v1/organizations/{org_id}/projects/{project_id}/code-matrix/query`
- **Description**: Initiates AI-powered analysis of project's code matrix data
- **Response**: AI analysis results with insights, recommendations, and building code references

### Health Controller

#### 1. Comprehensive Health Check
- **Method**: `GET`
- **Path**: `/health`
- **Description**: Detailed system health including database, AI service, and environment info
- **Response**: Complete health status with component-level details

#### 2. Simple Health Check
- **Method**: `GET`
- **Path**: `/health/simple`
- **Description**: Basic health check for load balancers and simple monitoring
- **Response**: Simple status and timestamp

## Schema Documentation

### Core Schemas

#### ProjectResponse
Complete project object returned by all project endpoints:
```yaml
properties:
  id: string (uuid)
  name: string
  description: string (nullable)
  dueDate: string (date, nullable)
  organizationId: string (uuid)
  status: enum [not_started, in_progress, completed, on_hold]
  currTask: string (nullable)
  createdAt: string (date-time, nullable)
  updatedAt: string (date-time, nullable)
  createdBy: string (nullable)
```

#### CreateProjectRequest
Request body for creating new projects:
```yaml
required: [name]
properties:
  name: string (1-255 chars)
  description: string (max 1000 chars, nullable)
  dueDate: string (date format, nullable)
  status: enum [not_started, in_progress, completed, on_hold]
  currTask: string (max 255 chars, nullable)
```

#### CodeMatrixQueryResponse
AI analysis response with insights and recommendations:
```yaml
properties:
  status: enum [completed, processing, failed]
  analysis_id: string
  insights: array of AIInsight objects
  processing_time_ms: integer
  timestamp: string (date-time)
  error: string (nullable)
```

#### HealthResponse
Comprehensive health check response:
```yaml
properties:
  status: enum [healthy, degraded, unhealthy]
  timestamp: string (date-time)
  service: string
  version: string
  environment: EnvironmentInfo object
  database: DatabaseHealth object
  ai_service: AIServiceHealth object
```

## Examples and Use Cases

### Creating a Project
```json
POST /api/v1/organizations/123e4567-e89b-12d3-a456-426614174000/projects
{
  "name": "Toronto Office Building Compliance",
  "description": "Compliance analysis for new office building in downtown Toronto",
  "dueDate": "2024-12-31",
  "status": "not_started"
}
```

### AI Code Matrix Analysis
```json
POST /api/v1/organizations/{org_id}/projects/{project_id}/code-matrix/query
Response:
{
  "status": "completed",
  "analysis_id": "analysis_789",
  "insights": [
    {
      "category": "structural",
      "recommendation": "Consider reinforced concrete for seismic requirements",
      "confidence": 0.92,
      "references": ["OBC 4.1.3.1", "OBC 4.1.8.3"],
      "priority": "high"
    }
  ],
  "processing_time_ms": 2340,
  "timestamp": "2024-01-15T12:30:45.000Z"
}
```

### Health Check Monitoring
```json
GET /health
Response:
{
  "status": "healthy",
  "timestamp": "2024-01-15T12:30:45.000Z",
  "service": "BuildSure Backend API",
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "message": "Database connection is healthy"
  },
  "ai_service": {
    "status": "healthy",
    "gemini_client_healthy": true,
    "active_chat_sessions": 3
  }
}
```

## Error Handling

All endpoints include comprehensive error handling with appropriate HTTP status codes:

- **400 Bad Request**: Missing required fields or invalid data
- **404 Not Found**: Resource not found (projects, organizations)
- **500 Internal Server Error**: Server-side errors with detailed messages

Error responses follow a consistent format:
```json
{
  "error": "Error message",
  "details": "Additional error details (optional)"
}
```

## Authentication

The API uses Bearer token authentication (JWT):
```yaml
securitySchemes:
  BearerAuth:
    type: http
    scheme: bearer
    bearerFormat: JWT
```

## Validation

The OpenAPI specification has been validated for:
- ✓ YAML syntax correctness
- ✓ Schema completeness
- ✓ Example consistency
- ✓ HTTP status code coverage
- ✓ Parameter validation rules

## Usage with Tools

### Swagger UI
You can use the `openapi.yaml` file with Swagger UI to generate interactive documentation:
1. Copy the contents of `docs/openapi.yaml`
2. Paste into [Swagger Editor](https://editor.swagger.io/)
3. Generate interactive documentation and client SDKs

### Postman
Import the OpenAPI specification into Postman:
1. Open Postman
2. Import → Link → Paste the raw GitHub URL to `openapi.yaml`
3. Generate collection with all endpoints and examples

### Code Generation
Use OpenAPI generators to create client libraries:
```bash
# Generate Python client
openapi-generator generate -i docs/openapi.yaml -g python -o ./client-python

# Generate TypeScript client
openapi-generator generate -i docs/openapi.yaml -g typescript-axios -o ./client-typescript
```

## Maintenance

This documentation is synchronized with the actual controller implementations:
- **Project Controller**: `app/controllers/project_controller.py`
- **Health Controller**: `app/controllers/health_controller.py`
- **Project Model**: `app/models/project.py`
- **Health Service**: `app/services/health_service.py`

When updating endpoints, ensure the OpenAPI specification is updated accordingly to maintain documentation accuracy.
