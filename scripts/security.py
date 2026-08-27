"""Ferramentas de segurança do SIGEM CAL.

Uso:
    python scripts/security.py
"""
from __future__ import annotations

import secrets
import sys
from pathlib import Path

# Permite execução direta: python scripts/security.py
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.security import hash_password  # noqa: E402


def main() -> None:
    password = input("Nova senha administrativa: ")
    confirm = input("Confirme a senha: ")
    if not password or password != confirm:
        raise SystemExit("Senhas vazias ou diferentes.")

    secret_key = secrets.token_urlsafe(48)
    password_hash = hash_password(password)

    print("\n--- COLE NO .env ---")
    print(f"SECRET_KEY={secret_key}")
    print("FLASK_ENV=production")
    print("SESSION_COOKIE_SECURE=true")
    print("ADMIN_USERNAME=admin")
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print("\nNão compartilhe o .env nem o hash fora do ambiente de execução.")


if __name__ == "__main__":
    main()
