# ============================================================
# SIGEM CAL
# SERVIÇO DE SINCRONIZAÇÃO
# ============================================================

from datetime import datetime

from app.database.database import db
from app.models.sync_log import SyncLog


# ============================================================
# OBTER REGISTRO
# ============================================================

def obter_sync_log():

    registro = (
        SyncLog.query
        .order_by(
            SyncLog.id.asc()
        )
        .first()
    )

    if registro is None:

        registro = SyncLog(

            version=1,

            source="system",

            updated_at=datetime.utcnow()

        )

        db.session.add(
            registro
        )

        db.session.commit()

    return registro


# ============================================================
# OBTER VERSÃO
# ============================================================

def obter_versao():

    registro = obter_sync_log()

    return registro.version


# ============================================================
# INCREMENTAR VERSÃO
# ============================================================

def incrementar_versao(
    source="system"
):

    registro = obter_sync_log()

    registro.version += 1

    registro.source = source

    registro.updated_at = (
        datetime.utcnow()
    )

    db.session.commit()

    return registro.version


# ============================================================
# ESTADO ATUAL
# ============================================================

def obter_estado():

    registro = obter_sync_log()

    return {

        "version": registro.version,

        "source": registro.source,

        "updated_at": (
            registro.updated_at.isoformat()
            if registro.updated_at
            else None
        )

    }
