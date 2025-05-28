import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Secret Manager–mounted env vars:
db_user   = os.environ['DB_USER']
db_pass   = os.environ['DB_PASS']
db_name   = os.environ['DB_NAME']
conn_name = os.environ['CLOUD_SQL_CONNECTION_NAME']

# Standard env: Cloud SQL proxy creates a Unix socket at /cloudsql/<INSTANCE>
DATABASE_URL = (
    f"postgresql+psycopg2://{db_user}:{db_pass}@/{db_name}"
    f"?host=/cloudsql/{conn_name}"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_timeout=30,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)