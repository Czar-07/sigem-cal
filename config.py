"""
Configuração central do SIGEM CAL.

SQLite:
    Usado no desenvolvimento/local.

PostgreSQL:
    Usado no Render através da variável DATABASE_URL.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# DIRETÓRIO BASE
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


# ============================================================
# CAMINHOS
# ============================================================

def resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default.resolve()

    candidate = Path(value).expanduser()

    if not candidate.is_absolute():
        candidate = BASE_DIR / candidate

    return candidate.resolve()


# ============================================================
# BANCO DE DADOS
# ============================================================

def build_database_uri(value: str | None) -> str:
    """
    Seleciona automaticamente:

    LOCAL:
        SQLite

    RENDER:
        PostgreSQL através de DATABASE_URL
    """

    raw = (value or "").strip()

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    if raw.startswith("postgres://"):
        return "postgresql+psycopg://" + raw[len("postgres://"):]

    if raw.startswith("postgresql://"):
        return "postgresql+psycopg://" + raw[len("postgresql://"):]

    # --------------------------------------------------------
    # SQLite
    # --------------------------------------------------------

    default_path = BASE_DIR / "instance" / "sigem.db"

    if not raw:
        db_path = default_path

    elif raw.startswith("sqlite:///"):

        db_path = Path(
            raw[len("sqlite:///"):]
        )

        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path

    else:

        db_path = Path(raw).expanduser()

        if not db_path.is_absolute():
            db_path = BASE_DIR / db_path

    db_path = db_path.resolve()

    # Cria instance somente para SQLite
    db_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return f"sqlite:///{db_path.as_posix()}"


# ============================================================
# BOOLEAN
# ============================================================

def env_bool(
    name: str,
    default: bool = False
) -> bool:

    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "sim",
        "on",
    }


# ============================================================
# CONFIGURAÇÃO
# ============================================================

class Config:

    # --------------------------------------------------------
    # AMBIENTE
    # --------------------------------------------------------

    ENV = os.getenv(
        "FLASK_ENV",
        "development"
    ).lower()

    DEBUG = ENV == "development"

    # --------------------------------------------------------
    # SEGURANÇA
    # --------------------------------------------------------

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        ""
    ).strip()

    if not SECRET_KEY:
        SECRET_KEY = "dev-only-change-this-secret"

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        ""
    ).strip()

    SQLALCHEMY_DATABASE_URI = build_database_uri(
        DATABASE_URL
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --------------------------------------------------------
    # UPLOADS
    # --------------------------------------------------------

    UPLOAD_FOLDER = str(
        resolve_path(
            os.getenv("UPLOAD_FOLDER"),
            BASE_DIR / "uploads",
        )
    )

    # --------------------------------------------------------
    # EXCEL
    # --------------------------------------------------------

    EXCEL_PATH = str(
        resolve_path(
            os.getenv("EXCEL_PATH"),
            BASE_DIR
            / "excel"
            / "Controle Calibração de Dispositivos 2026 REV1.xlsx",
        )
    )

    # --------------------------------------------------------
    # CERTIFICADOS
    # --------------------------------------------------------

    CERTIFICATES_FOLDER = str(
        resolve_path(
            os.getenv("CERTIFICATES_FOLDER"),
            BASE_DIR / "certificados",
        )
    )

    # --------------------------------------------------------
    # CLOUDFLARE R2
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # UPLOAD
    # --------------------------------------------------------

    MAX_CONTENT_LENGTH = int(
        os.getenv(
            "MAX_CONTENT_LENGTH",
            20 * 1024 * 1024
        )
    )

    # --------------------------------------------------------
    # SESSÃO
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # CERTIFICADOS
    # --------------------------------------------------------

    ALLOWED_CERTIFICATE_EXTENSIONS = {
        ".pdf",
        ".xlsx",
    }

    # --------------------------------------------------------
    # VALIDAÇÃO
    # --------------------------------------------------------

    @classmethod
    def validate(cls) -> None:

        if cls.ENV == "production":

            if (
                len(cls.SECRET_KEY) < 32
                or cls.SECRET_KEY
                == "dev-only-change-this-secret"
            ):
                raise RuntimeError(
                    "SECRET_KEY ausente/fraca. "
                    "Gere uma chave aleatória de pelo menos 32 caracteres."
                )

            if not os.getenv(
                "ADMIN_PASSWORD_HASH",
                ""
            ).strip():

                raise RuntimeError(
                    "ADMIN_PASSWORD_HASH não configurada. "
                    "Execute scripts/security.py."
                )