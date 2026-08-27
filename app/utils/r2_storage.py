from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class R2Storage:
    """
    Cliente Cloudflare R2 compatível com S3.

    As credenciais ficam exclusivamente no backend.

    Variáveis de ambiente esperadas:

        R2_ENDPOINT
        R2_ACCESS_KEY_ID
        R2_SECRET_ACCESS_KEY
        R2_BUCKET

    Exemplo:

        R2_BUCKET=sigem-certificados

    Estrutura esperada no bucket:

        sigem-certificados/
        └── Certificados/
            ├── Certificados de Calibração 2025/
            └── Certificados de Calibração 2026/
    """

    def __init__(self):
        self.endpoint = os.getenv(
            "R2_ENDPOINT",
            "",
        ).strip()

        self.access_key = os.getenv(
            "R2_ACCESS_KEY_ID",
            "",
        ).strip()

        self.secret_key = os.getenv(
            "R2_SECRET_ACCESS_KEY",
            "",
        ).strip()

        self.bucket = os.getenv(
            "R2_BUCKET",
            "sigem-certificados",
        ).strip()

        if not self.endpoint:
            raise RuntimeError(
                "R2_ENDPOINT não configurado."
            )

        if not self.access_key:
            raise RuntimeError(
                "R2_ACCESS_KEY_ID não configurado."
            )

        if not self.secret_key:
            raise RuntimeError(
                "R2_SECRET_ACCESS_KEY não configurado."
            )

        if not self.bucket:
            raise RuntimeError(
                "R2_BUCKET não configurado."
            )

        self.client = boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto",
            config=Config(
                signature_version="s3v4",
                retries={
                    "max_attempts": 3,
                    "mode": "standard",
                },
            ),
        )

    # ============================================================
    # UPLOAD
    # ============================================================

    def upload_fileobj(
        self,
        fileobj,
        key: str,
        content_type: str = "application/octet-stream",
    ):
        """
        Envia um arquivo/stream para o R2.
        """

        key = self._normalize_key(key)

        fileobj.seek(0)

        self.client.upload_fileobj(
            fileobj,
            self.bucket,
            key,
            ExtraArgs={
                "ContentType": content_type,
            },
        )

        return key

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ):
        """
        Envia bytes diretamente para o R2.
        """

        key = self._normalize_key(key)

        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

        return key

    # ============================================================
    # LEITURA
    # ============================================================

    def get_object(self, key: str):
        """
        Retorna o objeto bruto do R2.
        """

        key = self._normalize_key(key)

        return self.client.get_object(
            Bucket=self.bucket,
            Key=key,
        )

    def read_object(self, key: str) -> bytes:
        """
        Lê um objeto inteiro como bytes.
        """

        response = self.get_object(key)

        body = response["Body"]

        try:
            return body.read()
        finally:
            body.close()

    # ============================================================
    # LISTAGEM
    # ============================================================

    def list_objects(
        self,
        prefix: str = "",
        extensions: set[str] | None = None,
    ) -> Iterator[dict]:
        """
        Lista objetos do bucket usando paginação.

        Retorna:

            key
            name
            ext
            size
            etag
            last_modified
        """

        prefix = self._normalize_prefix(prefix)

        normalized_extensions = None

        if extensions:
            normalized_extensions = {
                ext.lower()
                if ext.startswith(".")
                else f".{ext.lower()}"
                for ext in extensions
            }

        continuation_token = None

        while True:
            params = {
                "Bucket": self.bucket,
                "Prefix": prefix,
                "MaxKeys": 1000,
            }

            if continuation_token:
                params[
                    "ContinuationToken"
                ] = continuation_token

            response = self.client.list_objects_v2(
                **params
            )

            for item in response.get(
                "Contents",
                [],
            ):
                key = item.get("Key", "")

                if not key:
                    continue

                # Diretórios virtuais.
                if key.endswith("/"):
                    continue

                name = Path(key).name

                # Arquivos temporários do Excel.
                if name.startswith("~$"):
                    continue

                extension = Path(
                    name
                ).suffix.lower()

                if (
                    normalized_extensions
                    and extension
                    not in normalized_extensions
                ):
                    continue

                yield {
                    "key": key,
                    "name": name,
                    "ext": extension,
                    "size": item.get(
                        "Size",
                        0,
                    ),
                    "etag": (
                        str(
                            item.get(
                                "ETag",
                                "",
                            )
                        )
                        .strip('"')
                    ),
                    "last_modified": item.get(
                        "LastModified"
                    ),
                }

            if not response.get(
                "IsTruncated",
                False,
            ):
                break

            continuation_token = response.get(
                "NextContinuationToken"
            )

            if not continuation_token:
                break

    # ============================================================
    # EXISTÊNCIA
    # ============================================================

    def exists(
        self,
        key: str,
    ) -> bool:
        """
        Verifica se o objeto existe.
        """

        key = self._normalize_key(key)

        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=key,
            )

            return True

        except ClientError as exc:
            code = (
                exc.response
                .get("Error", {})
                .get("Code")
            )

            if code in {
                "404",
                "NoSuchKey",
                "NotFound",
            }:
                return False

            raise

    # ============================================================
    # DELETE
    # ============================================================

    def delete(
        self,
        key: str,
    ):
        """
        Remove um objeto do R2.
        """

        key = self._normalize_key(key)

        self.client.delete_object(
            Bucket=self.bucket,
            Key=key,
        )

    # ============================================================
    # DOWNLOAD / VISUALIZAÇÃO
    # ============================================================

    def generate_download_url(
        self,
        key: str,
        expires: int = 900,
        response_content_disposition: str | None = None,
        response_content_type: str | None = None,
    ):
        """
        Gera URL temporária para download/visualização.

        O bucket continua privado.

        expires:
            validade em segundos.
        """

        key = self._normalize_key(key)

        params = {
            "Bucket": self.bucket,
            "Key": key,
        }

        if response_content_disposition:
            params[
                "ResponseContentDisposition"
            ] = response_content_disposition

        if response_content_type:
            params[
                "ResponseContentType"
            ] = response_content_type

        return self.client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=int(expires),
        )

    # ============================================================
    # UPLOAD URL
    # ============================================================

    def generate_upload_url(
        self,
        key: str,
        content_type: str,
        expires: int = 900,
    ):
        """
        Gera URL temporária para upload.
        """

        key = self._normalize_key(key)

        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=int(expires),
        )

    # ============================================================
    # METADADOS
    # ============================================================

    def head(
        self,
        key: str,
    ):
        """
        Retorna metadados do objeto.
        """

        key = self._normalize_key(key)

        return self.client.head_object(
            Bucket=self.bucket,
            Key=key,
        )

    # ============================================================
    # UTILITÁRIOS
    # ============================================================

    @staticmethod
    def _normalize_key(
        key: str,
    ) -> str:
        """
        Normaliza uma chave do R2 sem alterar
        o nome lógico do arquivo.
        """

        key = str(key or "").strip()

        key = key.replace(
            "\\",
            "/",
        )

        while "//" in key:
            key = key.replace(
                "//",
                "/",
            )

        return key.lstrip("/")

    @staticmethod
    def _normalize_prefix(
        prefix: str,
    ) -> str:
        """
        Normaliza prefixo do R2.
        """

        prefix = str(
            prefix or ""
        ).strip()

        prefix = prefix.replace(
            "\\",
            "/",
        )

        while "//" in prefix:
            prefix = prefix.replace(
                "//",
                "/",
            )

        return prefix.lstrip("/")


# ================================================================
# FACTORY
# ================================================================


def get_r2() -> R2Storage:
    """
    Retorna uma instância do cliente R2.
    """

    return R2Storage()


# ================================================================
# CONTENT TYPE
# ================================================================


def content_type_for(
    filename: str,
) -> str:
    """
    Retorna Content-Type adequado.
    """

    extension = Path(
        filename
    ).suffix.lower()

    return {
        ".pdf": "application/pdf",

        ".xlsx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),

        ".xls": (
            "application/vnd.ms-excel"
        ),
    }.get(
        extension,
        "application/octet-stream",
    )


# ================================================================
# COMPATIBILIDADE COM O CERTIFICATE SYNC
# ================================================================


def is_enabled() -> bool:
    """
    Verifica se o R2 possui todas as configurações necessárias.

    Não tenta conectar ao R2.

    Isso permite que o sistema continue funcionando
    localmente mesmo sem R2 configurado.
    """

    required = (
        "R2_ENDPOINT",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
        "R2_BUCKET",
    )

    return all(
        os.getenv(
            variable,
            "",
        ).strip()
        for variable in required
    )


def list_certificates():
    """
    Lista certificados dentro do prefixo configurado.

    Por padrão:

        Certificados/

    Pode ser alterado por:

        R2_CERTIFICATES_PREFIX
    """

    prefix = os.getenv(
        "R2_CERTIFICATES_PREFIX",
        "Certificados/",
    ).strip()

    if prefix and not prefix.endswith("/"):
        prefix += "/"

    storage = get_r2()

    yield from storage.list_objects(
        prefix=prefix,
        extensions={
            ".pdf",
            ".xlsx",
        },
    )


def read_file(
    key: str,
) -> bytes:
    """
    Lê um certificado diretamente do R2.
    """

    return get_r2().read_object(
        key
    )


def generate_certificate_url(
    key: str,
    expires: int = 900,
    download: bool = False,
):
    """
    Gera URL temporária para um certificado.

    download=False:
        navegador tenta visualizar.

    download=True:
        navegador solicita download.
    """

    filename = Path(key).name

    content_type = content_type_for(
        filename
    )

    disposition = (
        f'attachment; filename="{filename}"'
        if download
        else f'inline; filename="{filename}"'
    )

    return get_r2().generate_download_url(
        key,
        expires=expires,
        response_content_disposition=disposition,
        response_content_type=content_type,
    )