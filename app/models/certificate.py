# ============================================================
# SIGEM CAL
# MODEL — CERTIFICATE
# ============================================================

from datetime import datetime

from app.database.database import db


class Certificate(db.Model):

    __tablename__ = "certificates"

    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    # ========================================================
    # RELAÇÃO COM DISPOSITIVO
    # ========================================================

    device_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "devices.id",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # RASTREABILIDADE DA IMPORTAÇÃO
    # ========================================================

    source_key = db.Column(
        db.String(500),
        unique=True,
        index=True,
        nullable=True,
    )

    source_hash = db.Column(
        db.String(64),
        index=True,
        nullable=True,
    )

    source_type = db.Column(
        db.String(20),
        nullable=True,
    )

    source_path = db.Column(
        db.String(500),
        nullable=True,
    )

    # ========================================================
    # ARMAZENAMENTO
    # ========================================================

    storage_type = db.Column(
        db.String(20),
        nullable=True,
        index=True,
    )

    r2_key = db.Column(
        db.String(500),
        unique=True,
        index=True,
        nullable=True,
    )

    # ========================================================
    # DADOS DO CERTIFICADO
    # ========================================================

    ano = db.Column(
        db.Integer,
        nullable=False,
        index=True,
    )

    numero_certificado = db.Column(
        db.String(100),
        nullable=True,
        index=True,
    )

    nome_arquivo = db.Column(
        db.String(255),
        nullable=True,
    )

    arquivo = db.Column(
        db.String(500),
        nullable=True,
    )

    # ========================================================
    # DATAS
    # ========================================================

    data_emissao = db.Column(
        db.Date,
        nullable=True,
    )

    data_validade = db.Column(
        db.Date,
        nullable=True,
    )

    # ========================================================
    # LABORATÓRIO
    # ========================================================

    laboratorio = db.Column(
        db.String(255),
        nullable=True,
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    resultado = db.Column(
        db.String(50),
        nullable=True,
    )

    # ========================================================
    # OBSERVAÇÕES
    # ========================================================

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    # ========================================================
    # AUDITORIA
    # ========================================================

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ========================================================
    # REPRESENTAÇÃO
    # ========================================================

    def __repr__(self):

        return (
            f"<Certificate "
            f"id={self.id} "
            f"device_id={self.device_id} "
            f"ano={self.ano} "
            f"numero={self.numero_certificado!r}>"
        )