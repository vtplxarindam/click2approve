# Click2Approve FastAPI Migration

This is a complete migration of the Click2Approve C# application to FastAPI (Python).

## Features

- **Authentication & Authorization**: JWT-based authentication with refresh tokens
- **File Management**: Upload, download, and manage documents
- **Approval Workflow**: Submit documents for approval and track status
- **Email Notifications**: Configurable email notifications for approval events
- **Audit Logging**: Complete audit trail of all actions
- **Database**: MySQL with SQLAlchemy ORM and Alembic migrations
- **Background Tasks**: Email sending via async patterns (Celery can be added)

## Architecture

The application follows FastAPI best practices:

- **Pydantic Models**: Request/response validation and serialization
- **Dependency Injection**: Services injected via FastAPI's dependency system
- **Async/Await**: Full async support throughout the application
- **SQLAlchemy 2.0**: Modern async ORM patterns
- **Proper Error Handling**: Custom exceptions with appropriate HTTP status codes

## Key Differences from C# Version

1. **Dependency Injection**: Converted from ASP.NET Core DI to FastAPI's dependency system
2. **Async Patterns**: All database operations use async/await
3. **Validation**: Pydantic models replace C# model validation attributes
4. **Background Tasks**: Email sending uses async patterns instead of Hangfire
5. **Configuration**: Environment-based configuration using Pydantic Settings

## Setup

1. **Clone and Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Setup Database**:
   ```bash
   # Run migrations
   alembic upgrade head
   ```

4. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload --port 5555
   ```

5. **Using Docker**:
   ```bash
   docker-compose up -d
   ```

## API Endpoints

The API maintains the same endpoints as the original C# version:

- **Authentication**: `/api/account/*`
- **File Management**: `/api/file/*`
- **Approval Requests**: `/api/request/*`
- **Approval Tasks**: `/api/task/*`

## Configuration

All configuration is handled through environment variables. See `.env.example` for all available options.

## Database Migrations

Use Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Testing

The application includes the same business logic and validation as the original C# version, ensuring functional equivalence.

## Production Deployment

For production deployment:

1. Set proper environment variables
2. Use a production WSGI server (Gunicorn with Uvicorn workers)
3. Configure proper database connection pooling
4. Set up Redis for background tasks
5. Configure email service credentials
6. Set up file storage with proper permissions

## Migration Notes

- **Identity Framework**: Replaced with custom user management using SQLAlchemy
- **Entity Framework**: Replaced with SQLAlchemy 2.0 async patterns
- **Hangfire**: Replaced with async email sending (Celery can be added for complex background tasks)
- **ASP.NET Core Features**: Converted to FastAPI equivalents while maintaining the same functionality
- **C# Async Patterns**: Converted to Python async/await patterns
- **Validation**: Pydantic models provide the same validation as C# model attributes