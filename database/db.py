from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os



# 📦 Use SQLite for local development (always use absolute path)
import uuid
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
# Add a cache-busting query param to force new connection on each rerun
DB_CACHE_BUSTER = os.environ.get('DB_CACHE_BUSTER', str(uuid.uuid4()))
DATABASE_URL = f"sqlite:///{DB_PATH}?cache_buster={DB_CACHE_BUSTER}"

# For PostgreSQL (later): 
# DATABASE_URL = "postgresql://username:password@localhost/dbname"

# 🔌 Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Required for SQLite
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
