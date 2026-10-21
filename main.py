"""Точка входа: uvicorn main:app"""

from app.web.app import create_app

app = create_app()
