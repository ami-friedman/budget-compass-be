from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os
from dotenv import load_dotenv
from sqlalchemy_utils import database_exists, create_database

# Load environment variables from .env file
load_dotenv()

# Import all models here to ensure they are registered with SQLModel's metadata
from app import models

def get_database_url() -> str:
    """
    Construct database URL from environment variables.
    
    Priority:
    1. Use DATABASE_URL if provided (for custom connection strings)
    2. Otherwise, construct MySQL URL from individual variables:
       - DB_USER (required)
       - DB_PASSWORD (required)
       - DB_HOST (default: localhost)
       - DB_PORT (default: 3306)
       - DB_NAME (default: budget_compass)
    
    Returns:
        str: Database connection URL
    """
    # Check for complete DATABASE_URL first
    # Construct MySQL URL from individual variables
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "budget_compass")
    
    if not db_user or not db_password:
        raise ValueError(
            "Database configuration error: DB_USER and DB_PASSWORD environment variables are required. "
            "Alternatively, provide a complete DATABASE_URL."
        )
    
    return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Get database URL
DATABASE_URL = get_database_url()

# Debug: Print the database URL (with password masked)
import re
masked_url = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', DATABASE_URL)
print(f"[DATABASE] Connecting to: {masked_url}")

# Create engine with MySQL-specific parameters
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

def create_db_and_tables():
    """Create database if it doesn't exist, then create all tables."""
    # Create database if it doesn't exist
    if not database_exists(engine.url):
        print(f"[DATABASE] Creating database...")
        create_database(engine.url)
        print(f"[DATABASE] Database created successfully")
    else:
        print(f"[DATABASE] Database already exists")
    
    # Create all tables based on the imported models if they don't exist
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session