"""
WSGI entry point for deployment.

Local development:
    python app.py

Production/cloud deployment:
    gunicorn wsgi:app
"""

from app import app

if __name__ == "__main__":
    app.run()