# ============================================================
# SIGEM CAL
# MODELO DE SINCRONIZAÇÃO
# ============================================================

from datetime import datetime

from app.database.database import db


class SyncLog(db.Model):

    __tablename__ = "sync_log"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    version = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    source = db.Column(
        db.String(50),
        nullable=False,
        default="system"
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )
