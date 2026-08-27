"""
Autenticação administrativa.

Em produção, somente ADMIN_PASSWORD_HASH é aceito.
ADMIN_PASSWORD existe apenas como fallback de migração em desenvolvimento.
"""
import os
from hmac import compare_digest

from app.core.security import verify_password


def validar_admin(username: str, password: str) -> bool:
    admin_username = os.getenv("ADMIN_USERNAME", "admin").strip()
    password_hash = os.getenv("ADMIN_PASSWORD_HASH", "").strip()
    plain_password = os.getenv("ADMIN_PASSWORD", "")

    if not username or not password:
        return False

    if not compare_digest(username.strip(), admin_username):
        return False

    if password_hash:
        return verify_password(password_hash, password)

    # Nunca permitir senha plana quando o sistema está em produção.
    if os.getenv("FLASK_ENV", "production").lower() == "production":
        return False

    return bool(plain_password) and compare_digest(password, plain_password)
