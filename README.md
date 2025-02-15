# MCQ Generator Application

A combined Flask web application and FastAPI service for generating and managing technical MCQs.

## Setup

1. Install Python 3.9+
2. Clone repository
3. Install dependencies:

```bash
#IN Q-Generator Directory itself
pip install -r requirements.txt

cd ../fastapi-app
pip install -r requirements.txt
```

running applications:
python app.py

cd fastapi-app
python api.py


Access Applications

    Flask Web Interface: http://localhost:5000

    FastAPI Docs: http://localhost:8000/docs



**Important Notes:**
1. Replace the Groq API key with your actual key
2. For production:
   - Use proper secret management
   - Add database persistence
   - Implement rate limiting
   - Add error handling
   - Use production WSGI server (Gunicorn for Flask, Uvicorn workers for FastAPI)

This setup provides both a user-friendly web interface (Flask) and a robust API service (FastAPI) for MCQ generation and management.
