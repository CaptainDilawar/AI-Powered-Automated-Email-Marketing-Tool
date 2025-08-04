import os
from dotenv import load_dotenv
from database.db import engine, Base
from database.models import *
load_dotenv()

print("Attempting to create database tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print(f"Error creating database tables: {e}")
