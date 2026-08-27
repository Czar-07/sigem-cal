# ============================================================
# SIGEM CAL
# CERTIFICATE STORAGE
# ============================================================

from __future__ import annotations

import re
import unicodedata

from app.utils.r2_storage import (
    get_r2,
    content_type_for
)

import uuid

from pathlib import Path

from flask import current_app
from werkzeug.utils import secure_filename


# ============================================================
# EXTENSÕES PERMITIDAS
# ============================================================

ALLOWED_EXTENSIONS = {
    "pdf"
}


# ============================================================
# VALIDAR EXTENSÃO
# ============================================================

def arquivo_permitido(nome):

    if not nome:
        return False

    extensao = (
        Path(nome)
        .suffix
        .lower()
        .replace(".", "")
    )

    return extensao in ALLOWED_EXTENSIONS


def limpar_nome(valor: str) -> str:

    valor = unicodedata.normalize(
        "NFKD",
        str(valor)
    )

    valor = "".join(
        char
        for char in valor
        if not unicodedata.combining(char)
    )

    valor = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "_",
        valor
    )

    return valor.strip("._-") or "certificado"


def construir_chave(
    arquivo_nome: str,
    numero: str,
    ano: int
) -> str:

    nome = limpar_nome(
        arquivo_nome
    )

    numero_limpo = limpar_nome(
        numero
    )

    return (
        f"Certificados/"
        f"{ano}/"
        f"{numero_limpo}/"
        f"{nome}"
    )


# ============================================================
# SALVAR CERTIFICADO
# ============================================================

def salvar_certificado(
    arquivo,
    numero: str,
    ano: int
):

    nome_original = (
        arquivo.filename
        or "certificado.pdf"
    )

    chave = construir_chave(
        nome_original,
        numero,
        ano
    )

    r2 = get_r2()

    r2.upload_fileobj(
        arquivo,
        chave,
        content_type_for(nome_original)
    )

    return {
        "nome_arquivo": nome_original,
        "arquivo": chave,
    }

# ============================================================
# EXCLUIR CERTIFICADO
# ============================================================


def excluir_certificado_arquivo(
    caminho: str
):

    if not caminho:
        return

    r2 = get_r2()

    chave = caminho.replace(
        "\\",
        "/"
    ).lstrip("/")

    if r2.exists(chave):
        r2.delete(chave)
