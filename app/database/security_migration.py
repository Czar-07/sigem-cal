"""Migra segredos antigos armazenados em texto para formato criptografado."""
from app.database.database import db
from app.models.setting import Setting
from app.core.security import encrypt_secret


def migrate_sensitive_settings() -> int:
    changed = 0
    for setting in Setting.query.all():
        key = setting.chave.lower()
        if not any(part in key for part in ("password", "secret", "token")):
            continue
        if not setting.valor or setting.valor.startswith("enc:v1:"):
            continue
        setting.valor = encrypt_secret(
            setting.valor,
            __import__("flask").current_app.config["SECRET_KEY"],
        )
        changed += 1

    if changed:
        db.session.commit()
    return changed
