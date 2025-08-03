import subprocess
import time
import os
from database.db import engine
from database.models import Base

# Ensure database tables exist
Base.metadata.create_all(bind=engine)
ROOT = os.path.dirname(os.path.abspath(__file__))
print(f"🌍 Project root directory: {ROOT}")

if __name__ == "__main__":
    print("This script is for development purposes only.")
    print("For production, use systemd services with gunicorn and streamlit_start.sh.")
    print("Database tables ensured to exist.")