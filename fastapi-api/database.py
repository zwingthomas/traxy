# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ... build your DATABASE_URL exactly as you have it ...

engine = create_engine(
    os.getenv('DATABASE_URL'),
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)

# “Base” that all models inherit from
Base = declarative_base()

# Factory for sessions to inject in FastAPI dependencies
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)