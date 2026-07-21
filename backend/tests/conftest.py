"""Test environment setup.

Sets required env vars *before* app modules import their settings, so importing
``app.config`` inside tests picks up a valid encryption key and an in-memory DB.
"""
import os

from cryptography.fernet import Fernet

os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
