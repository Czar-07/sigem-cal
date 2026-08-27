import os

import qrcode

from flask import current_app, url_for


def gerar_qrcode_dispositivo(numero):

    numero = str(numero).strip()

    url_dispositivo = url_for(
        "device_page",
        numero=numero,
        _external=True
    )

    pasta_qrcodes = os.path.join(
        current_app.static_folder,
        "qrcodes"
    )

    os.makedirs(
        pasta_qrcodes,
        exist_ok=True
    )

    nome_arquivo = f"{numero}.png"

    caminho_arquivo = os.path.join(
        pasta_qrcodes,
        nome_arquivo
    )

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    qr.add_data(
        url_dispositivo
    )

    qr.make(
        fit=True
    )

    imagem = qr.make_image()

    imagem.save(
        caminho_arquivo
    )

    return {
        "url": url_dispositivo,
        "arquivo": nome_arquivo
    }