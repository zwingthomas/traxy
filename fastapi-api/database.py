# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import secrets_manager

db_user       = secrets_manager.get_secret("DB_USER")
db_pass       = secrets_manager.get_secret("DB_PASS")
db_name       = secrets_manager.get_secret("DB_NAME")
connection_id = secrets_manager.get_secret("CLOUD_SQL_CONNECTION_NAME")

# Build the SQLAlchemy URL in the correct format:
if os.getenv("DB_URL"):
    database_url = os.getenv("DB_URL")
else:
    database_url = (
        f"postgresql+psycopg2://{db_user}:{db_pass}@/"
        f"{db_name}?host=/cloudsql/{connection_id}"
    )

engine = create_engine(
    database_url,
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