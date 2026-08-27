# ============================================================
# SIGEM CAL
# MODEL — DEVICE
# ============================================================

from app.database.database import db


class Device(db.Model):

    __tablename__ = "devices"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    numero = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    descricao = db.Column(
        db.String(255)
    )

    cliente = db.Column(
        db.String(255)
    )

    part_number = db.Column(
        db.String(255)
    )

    ultima_calibracao = db.Column(
        db.Date
    )

    proxima_calibracao = db.Column(
        db.Date
    )

    certificado2025 = db.Column(
        db.String(255)
    )

    certificado2026 = db.Column(
        db.String(255)
    )

    condicao = db.Column(
        db.String(50)
    )

    status = db.Column(
        db.String(50)
    )

    # ========================================================
    # RELAÇÃO COM CERTIFICADOS
    # ========================================================

    certificados = db.relationship(
        "Certificate",
        backref="device",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):

        return (
            f"<Device "
            f"id={self.id} "
            f"numero={self.numero!r}>"
        )