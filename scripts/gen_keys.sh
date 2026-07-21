#!/usr/bin/env bash
# Generate the two required secrets for .env.
set -euo pipefail

echo "# Paste these into your .env file:"
echo

if command -v openssl >/dev/null 2>&1; then
  echo "JWT_SECRET=$(openssl rand -hex 32)"
else
  echo "JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
fi

echo "ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
