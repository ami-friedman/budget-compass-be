from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
import os

# For now, we'll use SQLite for simplicity. We can switch to MySQL later.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./budget_compass.db")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session