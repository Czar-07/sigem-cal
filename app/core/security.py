"""
Primitivas de segurança do SIGEM CAL.

- Hash de senha: Werkzeug/PBKDF2.
- Criptografia de dados sensíveis: Fernet autenticado.
- A chave de criptografia é derivada da SECRET_KEY; não há chave hardcoded.
"""
from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return bool(password_hash) and check_password_hash(password_hash, password)
    except (TypeError, ValueError):
        return False


def _fernet(secret_key: str) -> Fernet:
    if not secret_key or len(secret_key) < 32:
        raise RuntimeError("SECRET_KEY deve possuir pelo menos 32 caracteres.")
    digest = hashlib.sha256(secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt_secret(value: str | None, secret_key: str) -> str | None:
    if value is None:
        return None
    if value.startswith("enc:v1:"):
        return value
    token = _fernet(secret_key).encrypt(value.encode("utf-8")).decode("ascii")
    return f"enc:v1:{token}"


def decrypt_secret(value: str | None, secret_key: str) -> str | None:
    if value is None:
        return None
    if not value.startswith("enc:v1:"):
        # Compatibilidade com dados antigos; serão convertidos ao salvar.
        return value
    try:
        return _fernet(secret_key).decrypt(value[7:].encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
