# Budget Compass: Backend Coding Guidelines

This document provides specific guidelines for developing the FastAPI backend of the Budget Compass application. Follow these instructions to ensure consistent, high-quality code.

## Technology Stack

- **Framework**: FastAPI
- **Python Version**: 3.12+
- **ORM**: SQLModel
- **Database**: MySQL
- **Migration Tool**: Alembic
- **Package Management**: UV

## Task Planning

**IMPORTANT: Before starting any new task, always consult [`plan.md`](../plan.md) first.**

- Check [`plan.md`](../plan.md) for existing project plans, architectural decisions, and ongoing work
- Review any relevant context, requirements, or constraints documented in the plan
- Update [`plan.md`](../plan.md) with your task breakdown and approach before implementation
- Keep [`plan.md`](../plan.md) synchronized with actual progress and any changes to the plan
- Use the plan as a single source of truth for project direction and task coordination

This ensures all agents and developers are aligned on project goals, avoid duplicate work, and maintain consistency across the codebase.

## Project Structure

```
backend/
├── alembic/                # Database migrations
├── app/                    # Application code
│   ├── __init__.py
│   ├── auth.py             # Authentication logic
│   ├── database.py         # Database connection and session management
│   ├── models.py           # SQLModel models
│   ├── routes/             # API route modules
│   │   ├── __init__.py
│   │   ├── auth.py         # Auth-related endpoints
│   │   ├── users.py        # User-related endpoints
│   │   ├── budgets.py      # Budget-related endpoints
│   │   └── ...
│   ├── schemas/            # Pydantic schemas for request/response
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   └── ...
│   ├── services/           # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── ...
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── email.py
│       └── ...
├── tests/                  # Test files
├── alembic.ini             # Alembic configuration
├── main.py                 # Application entry point
└── pyproject.toml          # Project dependencies
```

## Code Style and Formatting

- Use 4 spaces for indentation
- Follow PEP 8 guidelines
- Use type hints for all function parameters and return values
- Use descriptive variable and function names
- Keep functions focused on a single responsibility
- Use docstrings for all public functions, classes, and modules

```python
def get_user_by_email(email: str) -> User | None:
    """
    Retrieve a user by their email address.
    
    Args:
        email: The email address to search for
        
    Returns:
        The User object if found, None otherwise
    """
    # Implementation
```

## FastAPI Best Practices

### 1. Route Organization

- Group related endpoints in separate router modules
- Use consistent URL patterns
- Include version prefix in API routes

```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/")
async def get_users():
    # Implementation
    
@router.get("/{user_id}")
async def get_user(user_id: int):
    # Implementation
```

### 2. Request Validation

- Use Pydantic models for request validation
- Define separate models for requests and responses
- Include field validation with descriptive error messages

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    
@router.post("/")
async def create_user(user: UserCreate):
    # Implementation
```

### 3. Response Models

- Define explicit response models for all endpoints
- Use status codes consistently
- Include proper error responses

```python
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    # Implementation
```

### 4. Dependency Injection

- Use FastAPI's dependency injection for common functionality
- Create reusable dependencies for database sessions, authentication, etc.

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    # Implementation
```

## Database and ORM

### 1. SQLModel Usage

- Define clear, well-documented models
- Use appropriate field types and constraints
- Implement relationships correctly

```python
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)
    
    # Relationships
    budgets: List["Budget"] = Relationship(back_populates="user")
```

### 2. Query Optimization

- Use appropriate indexes
- Implement pagination for list endpoints
- Use select_related/join for related data
- Avoid N+1 query problems

```python
from sqlmodel import select

def get_users_with_pagination(skip: int = 0, limit: int = 100, db: Session):
    return db.exec(select(User).offset(skip).limit(limit)).all()
```

### 3. Migrations

- Create migrations for all schema changes
- Include descriptive comments in migration files
- Test migrations before applying to production

```bash
# Generate a new migration
alembic revision --autogenerate -m "Add budget categories table"

# Apply migrations
alembic upgrade head
```

## Authentication and Security

### 1. JWT Implementation

- Use secure JWT configuration
- Implement token refresh mechanism
- Store tokens securely

```python
from jose import jwt
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

### 2. Password Security

- Use proper password hashing (for future password-based auth)
- Implement rate limiting for auth endpoints
- Follow OWASP security guidelines

### 3. Authorization

- Implement role-based access control
- Check permissions for all protected resources
- Use dependency injection for auth checks

```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify token and return user
    
@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
```

## Error Handling

- Use consistent error responses
- Include appropriate HTTP status codes
- Provide helpful error messages
- Log errors with context

```python
from fastapi import HTTPException

@router.get("/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## Testing

### 1. Unit Tests

- Test all business logic functions
- Use pytest for testing
- Mock external dependencies

### 2. Integration Tests

- Test API endpoints with TestClient
- Include happy path and error cases
- Test database interactions

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_read_user():
    response = client.get("/api/users/1")
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
```

### 3. Test Database

- Use a separate test database
- Reset database state between tests
- Use fixtures for common test data

## Performance

- Implement caching where appropriate
- Use async endpoints for I/O-bound operations
- Monitor and optimize slow queries
- Implement proper indexing

## Documentation

- Document all endpoints with clear descriptions
- Include example requests and responses
- Document authentication requirements
- Keep documentation up-to-date with code changes

```python
@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """
    Create a new user.
    
    - **email**: User's email address (must be unique)
    - **name**: User's full name
    """
    # Implementation
```

By following these guidelines, we'll create a robust, maintainable, and performant FastAPI backend that integrates well with the Angular frontend and provides a solid foundation for the Budget Compass application.