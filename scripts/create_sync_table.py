# ============================================================
# SIGEM CAL
# CRIAÇÃO DA TABELA DE SINCRONIZAÇÃO
# ============================================================

import sys

from pathlib import Path


# ============================================================
# RAIZ DO PROJETO
# ============================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR)
    )


# ============================================================
# IMPORTS
# ============================================================

from app import create_app

from app.database.database import db

from app.models.sync_log import SyncLog


# ============================================================
# APLICAÇÃO
# ============================================================

app = create_app()


# ============================================================
# CRIAR TABELA
# ============================================================

with app.app_context():

    print()
    print("========================================")
    print("SIGEM CAL — BANCO DE DADOS")
    print("========================================")
    print()

    print(
        "Banco utilizado:"
    )

    print(
        db.engine.url
    )

    print()

    print(
        "Verificando tabela sync_log..."
    )


    SyncLog.__table__.create(
        bind=db.engine,
        checkfirst=True
    )


    print()
    print(
        "Tabela sync_log criada/verificada com sucesso."
    )

    print()
    print("========================================")
