# ============================================================
# SIGEM CAL
# TESTE DO SISTEMA DE SINCRONIZAÇÃO
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


# ============================================================
# PYTHON PATH
# ============================================================

if str(BASE_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(BASE_DIR)
    )


# ============================================================
# IMPORTS DO PROJETO
# ============================================================

from app import create_app

from app.services.sync_service import (
    obter_estado
)


# ============================================================
# CRIAR APLICAÇÃO
# ============================================================

app = create_app()


# ============================================================
# APPLICATION CONTEXT
# ============================================================

with app.app_context():

    estado = obter_estado()


    print()

    print(
        "========================================"
    )

    print(
        "SIGEM CAL — TESTE DE SINCRONIZAÇÃO"
    )

    print(
        "========================================"
    )

    print()

    print(
        f"Versão:       {estado['version']}"
    )

    print(
        f"Origem:       {estado['source']}"
    )

    print(
        f"Atualizado:   {estado['updated_at']}"
    )

    print()

    print(
        "SYNC OK"
    )

    print()

    print(
        "========================================"
    )
