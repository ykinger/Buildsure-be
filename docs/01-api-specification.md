# 📋 BuildSure API Specification

## Overview
The BuildSure API is a RESTful service designed to support an Adaptive AI Wizard for Ontario Building Code form completion. It manages projects, form questions, and AI-driven clarifications.

## Base URL
`https://api.buildsure.com/v1` (or appropriate base URL for development/staging)

## Authentication
All endpoints require authentication. Use Bearer Token authentication:
```
Authorization: Bearer <token>
```

## Endpoints

### 1. Create a New Project
**POST /projects**

Creates a new form completion project.

#### Request Body
```json
{
  "project_name": "string (required)",
  "form_type": "string (optional, default: 'obc_compliance')",
  "metadata": {
    "building_address": "string (optional)",
    "client_name": "string (optional)"
  }
}
```

#### Response
**201 Created**
```json
{
  "project_id": "uuid",
  "project_name": "string",
  "status": "in_progress",
  "current_question": {
    "question_id": "string",
    "text": "string",
    "type": "multiple_choice|number",
    "options": ["array of strings", "or null for number type"]
  },
  "created_at": "timestamp"
}
```

### 2. Submit Answer for a Project
**POST /projects/{project_id}/answer**

Submits a user's answer to the current question and returns the next step.

#### Request Body
```json
{
  "question_id": "string (required, ID of the question being answered)",
  "answer": "string|number (required, user's response)"
}
```

#### Response Scenarios

**Case 1: Next Form Question (200 OK)**
```json
{
  "type": "form_question",
  "question": {
    "question_id": "string",
    "text": "string",
    "type": "multiple_choice|number",
    "options": ["array", "or null"]
  }
}
```

**Case 2: Clarifying Question (200 OK)**
```json
{
  "type": "clarifying_question",
  "question": "string (AI-generated clarifying question)",
  "context": "string (optional, reference to OBC sections)"
}
```

**Case 3: Form Completed (200 OK)**
```json
{
  "type": "completed_form",
  "form_data": {
    "project_id": "uuid",
    "answers": [
      {
        "question_id": "string",
        "question_text": "string",
        "answer": "string|number",
        "justification": "string (AI-generated reasoning)",
        "timestamp": "timestamp"
      }
    ],
    "completed_at": "timestamp"
  }
}
```

**Case 4: Advance with Clarification (200 OK)**
```json
{
  "type": "advance_with_clarification",
  "current_question_resolved": true,
  "next_question": {
    "type": "clarifying_question",
    "text": "string",
    "context": "string (optional)"
  }
}
```

### 3. Get Project Status
**GET /projects/{project_id}**

Retrieves the current state of a project.

#### Response
**200 OK**
```json
{
  "project_id": "uuid",
  "project_name": "string",
  "status": "in_progress|completed",
  "current_question": {
    "question_id": "string",
    "text": "string",
    "type": "multiple_choice|number",
    "options": ["array", "or null"]
  },
  "answered_questions": [
    {
      "question_id": "string",
      "question_text": "string",
      "answer": "string|number",
      "timestamp": "timestamp"
    }
  ],
  "progress": {
    "completed": "integer",
    "total": "integer",
    "percentage": "float"
  },
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

### 4. Get Completed Form
**GET /projects/{project_id}/form**

Retrieves the completed form data for a project.

#### Response
**200 OK**
```json
{
  "project_id": "uuid",
  "project_name": "string",
  "form_type": "string",
  "answers": [
    {
      "question_id": "string",
      "question_text": "string",
      "answer": "string|number",
      "justification": "string",
      "references": ["array of OBC sections"],
      "timestamp": "timestamp"
    }
  ],
  "completed_at": "timestamp",
  "metadata": {
    "building_address": "string (optional)",
    "client_name": "string (optional)"
  }
}
```

### 5. Reset Project
**POST /projects/{project_id}/reset**

Resets a project to its initial state or to a specific question.

#### Request Body
```json
{
  "target_question_id": "string (optional, reset to this question)"
}
```

#### Response
**200 OK**
```json
{
  "message": "Project reset successfully",
  "current_question": {
    "question_id": "string",
    "text": "string",
    "type": "multiple_choice|number",
    "options": ["array", "or null"]
  }
}
```

## Error Responses

### 400 Bad Request
```json
{
  "error": "invalid_request",
  "message": "Description of the error"
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Authentication required"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "Project not found"
}
```

### 422 Unprocessable Entity
```json
{
  "error": "validation_error",
  "message": "Answer validation failed",
  "details": {
    "field": "answer",
    "issue": "Expected number, got string"
  }
}
```

### 500 Internal Server Error
```json
{
  "error": "server_error",
  "message": "Internal server error"
}
```

## Key Terminology
- **Project**: A form completion instance for a specific building or compliance case.
- **Form Question**: Predefined questions from the Ontario Building Code compliance form.
- **Clarifying Question**: AI-generated questions to gather additional information for accurate form completion.
- **Answer**: User response to a form or clarifying question.

## Flow Examples

### Example 1: Normal Form Completion
1. POST /projects → Create project, get first question
2. POST /projects/{id}/answer → Submit answer, get next question
3. Repeat step 2 until form completed
4. GET /projects/{id}/form → Retrieve completed form

### Example 2: With Clarification
1. POST /projects → Create project, get first question
2. POST /projects/{id}/answer → Submit answer, get clarifying question
3. POST /projects/{id}/answer → Submit clarification, get next form question
4. Continue until completion

## Rate Limiting
- 100 requests per hour per user
- 10 concurrent projects per user

## Versioning
API version is included in the base URL (e.g., /v1). Breaking changes will result in a new version.
