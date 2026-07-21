from app.core.crypto import decrypt_json, encrypt_json


def test_encrypt_decrypt_roundtrip():
    payload = {"username": "runner@example.com", "password": "s3cr3t", "tokens": {"a": "b"}}
    token = encrypt_json(payload)
    assert token != str(payload)
    assert "s3cr3t" not in token  # not stored in plaintext
    assert decrypt_json(token) == payload


def test_encrypt_produces_distinct_tokens():
    # Fernet includes a random IV, so identical payloads yield different tokens.
    payload = {"k": "v"}
    assert encrypt_json(payload) != encrypt_json(payload)
