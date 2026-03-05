"""One-time script to create all DB tables. Run: python -m backend.database.create_tables"""
from sqlmodel import SQLModel

from backend.database.connection import engine

# Import above registers all table models with SQLModel.metadata
SQLModel.metadata.create_all(engine)
print("Tables created successfully.")
