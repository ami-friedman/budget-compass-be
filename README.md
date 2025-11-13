# Budget Compass Backend

FastAPI backend for the Budget Compass home budgeting application.

## Features

- **Multi-user support** with passwordless authentication (magic links)
- **MySQL database** with SQLModel ORM
- **Dual-account system** (Checking and Savings accounts)
- **Monthly budgeting** with rollover capabilities
- **RESTful API** with automatic OpenAPI documentation
- **Database migrations** with Alembic

## Prerequisites

- Python 3.12 or higher
- MySQL 8.0 or higher
- UV package manager (recommended) or pip

## Quick Start

### 1. Install Dependencies

Using UV (recommended):
```bash
cd backend
uv sync
```

Using pip:
```bash
cd backend
pip install -e .
```

**Note:** The `python-dotenv` package is included in dependencies and will automatically load environment variables from the `.env` file.

### 2. Set Up MySQL Database

Create a MySQL database and user:

```sql
CREATE DATABASE budget_compass;
CREATE USER 'budget_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON budget_compass.* TO 'budget_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configure Environment Variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and set your database credentials:
```bash
DB_USER=budget_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=budget_compass
```

**Alternative:** You can provide a complete database URL instead:
```bash
DATABASE_URL=mysql+pymysql://budget_user:password@localhost:3306/budget_compass
```

### 4. Run the Application

The application will automatically:
- Load environment variables from `.env` file (via `python-dotenv`)
- Connect to MySQL using the configured credentials
- Create all database tables on first run

```bash
# Using UV
uv run uvicorn app.main:app --reload

# Or using Python directly
python main.py
```

The API will be available at `http://localhost:8000`

**VS Code Users:** The `.env` file is automatically loaded by the application code. No VS Code plugin is needed, but you can install the "DotENV" extension for syntax highlighting of `.env` files.

## Database Configuration

### Environment Variables

The application supports two methods for database configuration:

**Method 1: Individual Variables (Recommended)**
- `DB_USER` - MySQL username (required)
- `DB_PASSWORD` - MySQL password (required)
- `DB_HOST` - MySQL host (default: localhost)
- `DB_PORT` - MySQL port (default: 3306)
- `DB_NAME` - Database name (default: budget_compass)

**Method 2: Complete URL**
- `DATABASE_URL` - Complete connection string (overrides individual variables)

### Connection Details

- **Driver:** PyMySQL (pure Python, no C dependencies)
- **Connection Pooling:** Enabled with pre-ping verification
- **Pool Recycle:** Connections recycled after 1 hour
- **Character Set:** UTF-8 (utf8mb4)

## Database Migrations

### Using Alembic

The application uses Alembic for database schema migrations.

**Generate a new migration:**
```bash
alembic revision --autogenerate -m "description of changes"
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

**View migration history:**
```bash
alembic history
```

### Auto-create Tables (Development)

For development, the application automatically creates tables on startup using SQLModel's `create_all()`. This is configured in `main.py`:

```python
@app.on_event("startup")
def on_startup():
    create_db_and_tables()
```

For production, it's recommended to use Alembic migrations instead.

## API Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── auth.py              # Authentication logic (magic links, JWT)
│   ├── budget_items.py      # Budget items endpoints
│   ├── budgets.py           # Budget management endpoints
│   ├── categories.py        # Category management endpoints
│   ├── database.py          # Database configuration and session management
│   ├── default_data.py      # Default categories for new users
│   ├── models.py            # SQLModel database models
│   └── transactions.py      # Transaction endpoints
├── alembic/
│   ├── versions/            # Migration files
│   ├── env.py              # Alembic environment configuration
│   └── script.py.mako      # Migration template
├── alembic.ini             # Alembic configuration
├── main.py                 # FastAPI application entry point
├── pyproject.toml          # Project dependencies
├── .env.example            # Example environment variables
└── README.md               # This file
```

## Development

### Running Tests

```bash
# TODO: Add test suite
pytest
```

### Code Style

The project follows Python best practices:
- Type hints for all function signatures
- Docstrings for public APIs
- 4-space indentation
- Maximum line length: 100 characters

### Logging

The application uses Python's built-in logging. SQL queries are logged when `echo=True` in the database engine configuration.

## Troubleshooting

### Database Connection Issues

**Error: "DB_USER and DB_PASSWORD environment variables are required"**
- Ensure you've created a `.env` file with the required variables
- Check that the `.env` file is in the `backend/` directory

**Error: "Access denied for user"**
- Verify MySQL user credentials are correct
- Ensure the user has proper permissions on the database

**Error: "Can't connect to MySQL server"**
- Check that MySQL is running: `sudo systemctl status mysql`
- Verify the host and port are correct
- Check firewall settings if connecting to a remote database

### Migration Issues

**Error: "Target database is not up to date"**
```bash
alembic upgrade head
```

**Error: "Can't locate revision"**
- Check that all migration files are present in `alembic/versions/`
- Verify the alembic_version table in your database

## Production Deployment

### Environment Variables

Set these environment variables in your production environment:
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- Or use `DATABASE_URL` for a complete connection string

### Database Setup

1. Create production database and user with strong password
2. Run migrations: `alembic upgrade head`
3. Disable auto-create tables (comment out `create_db_and_tables()` in `main.py`)

### Security Considerations

- Use strong, unique passwords for database users
- Enable SSL/TLS for database connections in production
- Set up proper firewall rules
- Use environment-specific configuration files
- Never commit `.env` files to version control

### Performance Optimization

- Enable query caching in MySQL
- Add indexes for frequently queried columns
- Monitor slow query log
- Adjust connection pool size based on load
- Consider read replicas for high-traffic scenarios

## License

[Add your license information here]

## Support

For issues and questions, please [open an issue](https://github.com/your-repo/budget-compass/issues).