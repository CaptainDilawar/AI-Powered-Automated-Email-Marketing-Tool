from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# --- Load Environment Variables ---
load_dotenv()

# --- Database Encryption Setup ---
DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")
if not DB_ENCRYPTION_KEY:
    raise ValueError("DB_ENCRYPTION_KEY not set in .env file. Please set a strong password.")

# --- Database Connection Logic ---
# Use DATABASE_URL for production (PostgreSQL), otherwise default to a local SQLite file.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Production setup (PostgreSQL)
    engine = create_engine(DATABASE_URL)
else:
    # Local development setup (SQLite)
    # The project_root is one level up from the `database` directory where this file is.
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    sqlite_path = os.path.join(project_root, "app.db")
    engine = create_engine(f"sqlite:///{sqlite_path}")

# 🧠 Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 🧱 Base class for all models
Base = declarative_base()

# 🧰 Dependency for getting DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()