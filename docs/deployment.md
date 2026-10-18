# Deployment Guide

## Quick Local Run
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run test suite
python tests/run_all_tests.py

# 3. Launch application
python main.py
```

Access:
- Interactive Chatbot: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Docker Deployment
```bash
docker compose up -d --build
```
