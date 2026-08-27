from __future__ import annotations

import os
from pathlib import Path

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class R2Storage:
    """
    Cliente do Cloudflare R2 compatível com S3.

    As credenciais nunca são enviadas ao navegador.
    """

    def __init__(self):
        self.endpoint = os.getenv("R2_ENDPOINT", "").strip()
        self.access_key = os.getenv("R2_ACCESS_KEY_ID", "").strip()
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
        self.bucket = os.getenv(
            "R2_BUCKET",
            "sigem-certificados",
        ).strip()

        if not self.endpoint:
            raise RuntimeError("R2_ENDPOINT não configurado.")

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
                signature_version="s3v4"
            ),
        )

    # ========================================================
    # UPLOAD
    # ========================================================

    def upload_fileobj(
        self,
        fileobj,
        key: str,
        content_type: str = "application/octet-stream",
    ):
        fileobj.seek(0)

        self.client.upload_fileobj(
            fileobj,
            self.bucket,
            key,
            ExtraArgs={
                "ContentType": content_type
            },
        )

        return key

    def upload_bytes(
        self,
        data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ):
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

        return key

    # ========================================================
    # LEITURA
    # ========================================================

    def get_object(self, key: str):
        return self.client.get_object(
            Bucket=self.bucket,
            Key=key,
        )

    def read_object(self, key: str) -> bytes:
        response = self.get_object(key)

        body = response["Body"]

        try:
            return body.read()
        finally:
            body.close()

    # ========================================================
    # EXISTÊNCIA
    # ========================================================

    def exists(self, key: str) -> bool:
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

    # ========================================================
    # DELETE
    # ========================================================

    def delete(self, key: str):
        self.client.delete_object(
            Bucket=self.bucket,
            Key=key,
        )

    # ========================================================
    # DOWNLOAD
    # ========================================================

    def generate_download_url(
        self,
        key: str,
        expires: int = 900,
    ):
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
            },
            ExpiresIn=expires,
        )

    # ========================================================
    # UPLOAD URL
    # ========================================================

    def generate_upload_url(
        self,
        key: str,
        content_type: str,
        expires: int = 900,
    ):
        return self.client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expires,
        )


def get_r2():
    return R2Storage()


def content_type_for(filename: str) -> str:

    extension = Path(
        filename
    ).suffix.lower()

    return {
        ".pdf": "application/pdf",

        ".xlsx": (
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),

    }.get(
        extension,
        "application/octet-stream",
    )