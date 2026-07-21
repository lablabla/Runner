"""Symmetric encryption for integration credentials stored at rest.

Garmin/Strava credentials and cached session tokens are never stored in plaintext.
They are encrypted with a Fernet key supplied via ENCRYPTION_KEY. Losing the key
means stored credentials can no longer be decrypted (users simply re-enter them).
"""
from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


class CryptoError(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        raise CryptoError(
            "ENCRYPTION_KEY is not set. Generate one with "
            '`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`'
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as exc:  # malformed key
        raise CryptoError(f"ENCRYPTION_KEY is invalid: {exc}") from exc


def encrypt_json(payload: dict[str, Any]) -> str:
    """Encrypt a JSON-serialisable dict, returning a urlsafe token string."""
    raw = json.dumps(payload, separators=(",", ":")).encode()
    return _fernet().encrypt(raw).decode()


def decrypt_json(token: str) -> dict[str, Any]:
    """Decrypt a token produced by :func:`encrypt_json`."""
    try:
        raw = _fernet().decrypt(token.encode())
    except InvalidToken as exc:
        raise CryptoError("Could not decrypt stored credentials (wrong key?)") from exc
    return json.loads(raw.decode())
