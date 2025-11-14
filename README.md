# BuildSure Backend

A Flask-based backend application for BuildSure with clean architecture principles and PostgreSQL database integration.

## Architecture

This project follows a layered architecture pattern:

- **Presentation Layer** (`app/controllers/`) - HTTP request handling and response formatting
- **Business Logic Layer** (`app/services/`) - Core business logic and validation
- **Data Access Layer** (`app/repositories/`, `app/models/`) - Data persistence and retrieval
- **Infrastructure** (`app/config/`, `app/utils/`) - Configuration and shared utilities

## Features

- ✅ Clean Architecture with proper separation of concerns
- ✅ Type hints throughout the codebase
- ✅ PostgreSQL database integration
- ✅ **Google Gemini AI integration** for intelligent building assistance
- ✅ Health check endpoints with database and AI service monitoring
- ✅ Environment-based configuration
- ✅ Docker support
- ✅ CORS enabled for frontend integration
- ✅ **AI-powered building analysis and recommendations**
- ✅ **Interactive AI consultation chat sessions**
- ✅ **Project complexity and risk assessment**

## Prerequisites

- Python 3.11+ (recommended)
- PostgreSQL database (configured with provided credentials)
- **Google Gemini API key** (get one from [Google AI Studio](https://aistudio.google.com/app/apikey))

## Setup

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Buildsure-be
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   # or
   .venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration:
   # - Add your GEMINI_API_KEY
   # - Adjust other settings as needed
   ```

5. **Test Gemini integration (optional):**
   ```bash
   python test_gemini.py
   ```

6. **Initialize the database:**
   ```bash
   python init_db.py
   ```

7. **Run the application:**
   ```bash
   python run.py
   ```

The API will be available at `http://127.0.0.1:5000`

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

2. **Or build and run with Docker:**
   ```bash
   docker build -t buildsure-api .
   docker run -p 5000:5000 --env-file .env buildsure-api
   ```

### AWS ECS Deployment

The application includes a complete CI/CD pipeline for deploying to AWS ECS using GitHub Actions.

**Quick Start:**
1. Create AWS resources (ECR, ECS, RDS, etc.)
2. Configure GitHub Secrets
3. Push to `main` branch to trigger deployment

**Documentation:**
- 📋 [Deployment Checklist](docs/deployment-checklist.md) - Step-by-step setup guide
- 📖 [AWS Deployment Guide](docs/aws-deployment-guide.md) - Comprehensive deployment documentation
- 🔄 [GitHub Actions Workflows](../.github/workflows/README.md) - CI/CD pipeline details

**Features:**
- ✅ Automated deployments on push to main
- ✅ Docker image building and pushing to ECR
- ✅ Zero-downtime deployments with health checks
- ✅ CloudWatch logging and monitoring
- ✅ Manual deployment trigger support

## API Endpoints

### Health Check

- **GET** `/api/v1/health` - Comprehensive health status including database and AI service connectivity
- **GET** `/api/v1/health/simple` - Simple health check for load balancers

### AI-Powered Features

#### Building Analysis
- **POST** `/api/v1/ai/analyze/building-description` - Analyze building descriptions and extract key information

#### Project Recommendations
- **POST** `/api/v1/ai/recommendations/project` - Get AI-powered project recommendations

#### Project Assessment
- **POST** `/api/v1/ai/assess/complexity` - Assess project complexity using AI analysis
- **POST** `/api/v1/ai/assess/risks` - Generate comprehensive risk assessments

#### AI Chat Consultation
- **POST** `/api/v1/ai/chat/start` - Start an AI consultation chat session
- **POST** `/api/v1/ai/chat/message` - Send messages to chat session
- **GET** `/api/v1/ai/chat/history/<session_id>` - Get chat session history
- **DELETE** `/api/v1/ai/chat/end/<session_id>` - End chat session

#### AI Service Health
- **GET** `/api/v1/ai/health` - AI service health check

#### Example Response

```json
{
  "database": {
    "message": "Database connection is healthy",
    "status": "connected"
  },
  "environment": {
    "platform": "macOS-14.1-arm64-arm-64bit-Mach-O",
    "python_version": "3.13.3 (main, Apr  8 2025, 13:54:08) [Clang 16.0.0 (clang-1600.0.26.6)]"
  },
  "service": "BuildSure Backend API",
  "status": "healthy",
  "timestamp": "2025-08-14T02:41:41.405703",
  "version": "1.0.0"
}
```

### AI Analysis Example

```bash
# Analyze a building description
curl -X POST http://127.0.0.1:5000/api/v1/ai/analyze/building-description \
  -H "Content-Type: application/json" \
  -d '{
    "description": "A 3-story modern residential building with eco-friendly features, located in an urban area with a budget of $500,000"
  }'

# Start an AI consultation chat
curl -X POST http://127.0.0.1:5000/api/v1/ai/chat/start \
  -H "Content-Type: application/json" \
  -d '{
    "initial_context": "I need help planning a coastal residential project"
  }'

# Send a message to the chat session
curl -X POST http://127.0.0.1:5000/api/v1/ai/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "message": "What materials should I use to protect against salt water corrosion?"
  }'
```
```

## Project Structure

```
app/
├── __init__.py              # Application factory
├── config/
│   ├── __init__.py
│   └── settings.py          # Configuration classes
├── controllers/
│   ├── __init__.py
│   └── health_controller.py # Health check endpoints
├── services/
│   ├── __init__.py
│   └── health_service.py    # Health check business logic
├── repositories/
│   └── __init__.py          # Data access layer (future use)
├── models/
│   ├── __init__.py
│   └── base.py              # Base model with common fields
└── utils/
    └── __init__.py          # Utility functions
init_db.py                   # Database initialization script
run.py                       # Application entry point
requirements.txt             # Python dependencies
Dockerfile                   # Docker configuration
docker-compose.yml           # Docker Compose configuration
.env.example                 # Environment variables template
```

## Database Configuration

The application uses PostgreSQL with the following connection details:
- Host: plm1w6.h.filess.io
- Database: buildsure_passagesee
- User: buildsure_passagesee
- Port: 5433
- Password: [Configured in environment]

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Environment (development/production/testing) | development |
| `SECRET_KEY` | Flask secret key for sessions | auto-generated |
| `DB_HOST` | PostgreSQL host | plm1w6.h.filess.io |
| `DB_NAME` | Database name | buildsure_passagesee |
| `DB_USER` | Database user | buildsure_passagesee |
| `DB_PASSWORD` | Database password | [from credentials] |
| `DB_PORT` | Database port | 5433 |
| `GEMINI_API_KEY` | Google Gemini API key | required for AI features |
| `GEMINI_MODEL` | Gemini model name | gemini-pro |
| `GEMINI_TEMPERATURE` | AI response creativity (0-1) | 0.7 |
| `GEMINI_MAX_OUTPUT_TOKENS` | Maximum AI response length | 2048 |
| `GEMINI_TOP_P` | AI nucleus sampling parameter | 0.8 |
| `GEMINI_TOP_K` | AI top-k sampling parameter | 40 |
| `HOST` | Server host | 127.0.0.1 |
| `PORT` | Server port | 5000 |

## Development

### Adding New Features

1. **Controllers**: Add new endpoints in `app/controllers/`
2. **Services**: Implement business logic in `app/services/`
3. **Models**: Define data models in `app/models/`
4. **Repositories**: Add data access logic in `app/repositories/`

### Testing

The project includes comprehensive error handling and health monitoring. The health check endpoints can be used to verify system status.

## Contributing

1. Follow the established architecture patterns
2. Use type hints for all function parameters and return values
3. Maintain separation between layers
4. Add appropriate error handling
5. Update documentation as needed
