#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Start the FastAPI backend in the background
echo "Starting FastAPI backend..."
nohup uvicorn backend.api:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &

# Start the Streamlit dashboard in the background
echo "Starting Streamlit dashboard..."
nohup streamlit run dashboard/Home.py --server.port 8501 > streamlit.log 2>&1 &

echo "Application started."
