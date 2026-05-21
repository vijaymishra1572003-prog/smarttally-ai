"""WSGI entry point for production deployment."""

from backend.app import create_app

app = create_app("production")
