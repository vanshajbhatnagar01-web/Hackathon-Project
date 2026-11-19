import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables BEFORE importing SQLAlchemy
# so SQLALCHEMY_DISABLE_CYTHON=1 takes effect immediately.
load_dotenv()
os.environ.setdefault("SQLALCHEMY_DISABLE_CYTHON", "1")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Read MySQL credentials from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "growth360")

# Safely URL-encode the password in case it has special characters
encoded_password = quote_plus(DB_PASSWORD)

# Build the SQLAlchemy MySQL connection string
DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Create the SQLAlchemy Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Create SessionLocal factory for database requests
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all Phase 3 database models
Base = declarative_base()


def get_db():
    """Provides a database session per API request and closes it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_db_connection() -> bool:
    """Verifies that Python can connect to the growth360 MySQL database."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True