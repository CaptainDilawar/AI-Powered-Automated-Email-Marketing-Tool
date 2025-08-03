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

# --- PostgreSQL Connection Details ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "email_marketing_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres") # This is the DB connection password

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 🔌 Create engine
engine = create_engine(
    DATABASE_URL
)

# 🧠 Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 🧱 Base class for all models
Base = declarative_base()

# 🧰 Dependency for getting DB session (can be used in Streamlit/Flask/FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
