from models import Base
import secrets_manager
import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
current_dir = os.path.dirname(os.path.abspath(
    __file__))  # .../project_root/alembic
parent_dir = os.path.dirname(current_dir)                 # .../project_root
sys.path.insert(0, parent_dir)


# Alembic Config object
config = context.config

# Interpret the config file for Python logging
fileConfig(config.config_file_name)

# Give Alembic access to your MetaData:
target_metadata = Base.metadata

db_user = secrets_manager.get_secret("DB_USER")
db_pass = secrets_manager.get_secret("DB_PASS")
db_name = secrets_manager.get_secret("DB_NAME")
connection_id = secrets_manager.get_secret("CLOUD_SQL_CONNECTION_NAME")

if os.getenv("DB_USE_TCP"):
    # local dev or Cloud Build migrations use TCP
    tcp_host = os.getenv("DB_HOST", "127.0.0.1:5432")
    database_url = (
        f"postgresql+psycopg2://{db_user}:{db_pass}@{tcp_host}/{db_name}"
    )
else:
    # App Engine standard at runtime uses Unix socket
    database_url = (
        f"postgresql+psycopg2://{db_user}:{db_pass}@/"
        f"{db_name}?host=/cloudsql/{connection_id}"
    )

config.set_main_option("sqlalchemy.url", database_url)

# Override the config’s sqlalchemy.url with dynamically built URL
config.set_main_option("sqlalchemy.url", database_url)


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
