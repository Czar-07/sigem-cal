# ============================================================
# SIGEM CAL
# MODEL — CONFIGURAÇÕES DO SISTEMA
# ============================================================

from datetime import datetime

from app.database.database import db
from flask import current_app
from app.core.security import encrypt_secret, decrypt_secret


class Setting(db.Model):

    __tablename__ = "settings"

    # ========================================================
    # IDENTIFICAÇÃO
    # ========================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    chave = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    valor = db.Column(
        db.Text,
        nullable=True
    )

    tipo = db.Column(
        db.String(30),
        nullable=False,
        default="string"
    )

    categoria = db.Column(
        db.String(50),
        nullable=False,
        default="geral",
        index=True
    )

    descricao = db.Column(
        db.String(255),
        nullable=True
    )

    # ========================================================
    # CONTROLE
    # ========================================================

    editavel = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    ativo = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    # ========================================================
    # DATAS
    # ========================================================

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # ========================================================
    # REPRESENTAÇÃO
    # ========================================================

    def __repr__(self):

        return (
            f"<Setting "
            f"id={self.id} "
            f"chave={self.chave!r} "
            f"categoria={self.categoria!r}>"
        )

    # ========================================================
    # CONVERSÃO DO VALOR
    # ========================================================

    def get_value(self):

        if self.valor is None:
            return None

        if "password" in self.chave.lower() or "secret" in self.chave.lower() or "token" in self.chave.lower():
            secret = decrypt_secret(self.valor, current_app.config["SECRET_KEY"])
            if secret is None:
                return ""
            return secret

        if self.tipo == "integer":

            try:
                return int(self.valor)

            except (TypeError, ValueError):
                return 0

        if self.tipo == "float":

            try:
                return float(self.valor)

            except (TypeError, ValueError):
                return 0.0

        if self.tipo == "boolean":

            return self.valor.lower() in (
                "true",
                "1",
                "yes",
                "sim",
                "on"
            )

        return self.valor

    # ========================================================
    # DEFINIR VALOR
    # ========================================================

    def set_value(self, valor):

        if valor is None:

            self.valor = None

            return

        if self.tipo == "boolean":

            self.valor = (
                "true"
                if bool(valor)
                else "false"
            )

            return

        normalized = str(valor)
        if "password" in self.chave.lower() or "secret" in self.chave.lower() or "token" in self.chave.lower():
            self.valor = encrypt_secret(normalized, current_app.config["SECRET_KEY"])
        else:
            self.valor = normalized

    # ========================================================
    # SERIALIZAÇÃO
    # ========================================================

    def to_dict(self):

        return {

            "id":
                self.id,

            "chave":
                self.chave,

            "valor":
                ("" if "password" in self.chave.lower() else self.get_value()),

            "tipo":
                self.tipo,

            "categoria":
                self.categoria,

            "descricao":
                self.descricao,

            "editavel":
                self.editavel,

            "ativo":
                self.ativo,

            "created_at":
                (
                    self.created_at.isoformat()
                    if self.created_at
                    else None
                ),

            "updated_at":
                (
                    self.updated_at.isoformat()
                    if self.updated_at
                    else None
                )

        }