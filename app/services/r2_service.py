from __future__ import annotations

import os
from pathlib import Path

from app.utils.r2_storage import get_r2


R2_PREFIX = os.getenv(
    "R2_CERTIFICATES_PREFIX",
    "Certificados/",
).strip()


def is_enabled() -> bool:
    """
    Verifica se o R2 está configurado.
    """

    required = (
        "R2_ENDPOINT",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET",
    )

    return all(
        os.getenv(name, "").strip()
        for name in required
    )


def list_certificates():
    """
    Lista PDFs e XLSX do diretório de certificados no R2.
    """

    storage = get_r2()

    results = []

    paginator = storage.client.get_paginator(
        "list_objects_v2"
    )

    for page in paginator.paginate(
        Bucket=storage.bucket,
        Prefix=R2_PREFIX,
    ):

        for item in page.get("Contents", []):

            key = item.get("Key", "")

            if not key:
                continue

            if key.endswith("/"):
                continue

            extension = Path(
                key
            ).suffix.lower()

            if extension not in {
                ".pdf",
                ".xlsx",
            }:
                continue

            results.append({
                "key": key,
                "name": Path(key).name,
                "ext": extension,
                "etag": (
                    item.get("ETag", "")
                    .strip('"')
                ),
                "size": item.get(
                    "Size",
                    0,
                ),
            })

    return results


def read_file(key: str) -> bytes:
    """
    Lê um certificado diretamente do R2.
    """

    storage = get_r2()

    return storage.read_object(key)


def certificate_url(
    key: str,
    expires: int = 900,
):
    """
    Gera URL temporária para visualizar/baixar
    o certificado.
    """

    storage = get_r2()

    return storage.generate_download_url(
        key,
        expires=expires,
    )


def delete_file(key: str):
    """
    Remove certificado do R2.
    """

    storage = get_r2()

    storage.delete(key)