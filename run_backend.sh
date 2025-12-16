#!/bin/bash
cd backend
source venv/bin/activate
# Run with reload enabled for development
uvicorn app.main:app --reload --port 8000
