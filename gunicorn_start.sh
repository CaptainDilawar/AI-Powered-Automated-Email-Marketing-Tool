#!/bin/bash

# Start Gunicorn with Uvicorn workers
exec gunicorn backend.api:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --log-level info \
  --timeout 120

