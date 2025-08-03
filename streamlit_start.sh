#!/bin/bash

# Start Streamlit
exec streamlit run dashboard/Home.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.enableCORS false \
  --server.enableXsrfProtection false

