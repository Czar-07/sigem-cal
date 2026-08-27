"""
Configuração central do SIGEM CAL.

Princípios:
- nenhum segredo deve ficar hardcoded no código;
- caminhos são resolvidos de forma determinística;
- cookies e limites de upload são configuráveis;
- ambiente de produção exige SECRET_KEY forte.
"""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default.resolve()
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate
    return candidate.resolve()


def build_database_uri(value: str | None) -> str:
    default_path = BASE_DIR / "instance" / "sigem.db"
    raw = (value or "").strip()

    if not raw:
        db_path = default_path
    elif raw.startswith("sqlite:///"):
        db_path = Path(raw[len("sqlite:///"):])
        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path
    else:
        db_path = Path(raw).expanduser()
        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path

    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


class Config:

    ENV = os.getenv(
        "FLASK_ENV",
        "production"
    ).lower()

    DEBUG = ENV == "development"

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        ""
    ).strip()

    if not SECRET_KEY:
        SECRET_KEY = "dev-only-change-this-secret"

    SQLALCHEMY_DATABASE_URI = build_database_uri(
        os.getenv("DATABASE_URL")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = str(
        resolve_path(
            os.getenv("UPLOAD_FOLDER"),
            BASE_DIR / "uploads",
        )
    )

    EXCEL_PATH = str(
        resolve_path(
            os.getenv("EXCEL_PATH"),
            BASE_DIR
            / "excel"
            / "Controle Calibração de Dispositivos 2026 REV1.xlsx",
        )
    )

    CERTIFICATES_FOLDER = str(
        resolve_path(
            os.getenv("CERTIFICATES_FOLDER"),
            BASE_DIR / "certificados",
        )
    )

    R2_ENDPOINT = os.getenv(
        "R2_ENDPOINT",
        ""
    ).strip()

    R2_ACCESS_KEY_ID = os.getenv(
        "R2_ACCESS_KEY_ID",
        ""
    ).strip()

    R2_SECRET_ACCESS_KEY = os.getenv(
        "R2_SECRET_ACCESS_KEY",
        ""
    ).strip()

    R2_BUCKET = os.getenv(
        "R2_BUCKET",
        "sigem-certificados"
    ).strip()

    R2_ENABLED = bool(
        R2_ENDPOINT
        and R2_ACCESS_KEY_ID
        and R2_SECRET_ACCESS_KEY
        and R2_BUCKET
    )

    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            20 * 1024 * 1024
        )
    )

    SESSION_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = os.getenv(
        "SESSION_COOKIE_SAMESITE",
        "Lax"
    )

    SESSION_COOKIE_SECURE = env_bool(
        "SESSION_COOKIE_SECURE",
        not DEBUG
    )

    PERMANENT_SESSION_LIFETIME = int(
        os.getenv(
            "SESSION_LIFETIME_SECONDS",
            8 * 60 * 60
        )
    )

    ALLOWED_CERTIFICATE_EXTENSIONS = {
        ".pdf",
        ".xlsx"
    }

    @classmethod
    def validate(cls) -> None:
        if cls.ENV == "production":
            if len(cls.SECRET_KEY) < 32 or cls.SECRET_KEY == "dev-only-change-this-secret":
                raise RuntimeError(
                    "SECRET_KEY ausente/fraca. Gere uma chave aleatória de pelo menos 32 caracteres."
                )
            if os.getenv("ADMIN_PASSWORD_HASH", "").strip() == "":
                raise RuntimeError(
                    "ADMIN_PASSWORD_HASH não configurada. Execute scripts/security.py."
                )
