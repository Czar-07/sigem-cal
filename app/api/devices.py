from flask import Blueprint, jsonify, url_for

from app.models.device import Device

from app.utils.calibration import calcular_calibracao


devices = Blueprint(
    "devices",
    __name__,
    url_prefix="/api"
)


# ============================================================
# SERIALIZAR DISPOSITIVO
# ============================================================

def serializar_dispositivo(dispositivo):
    """
    Converte um objeto Device em um dicionário
    pronto para ser enviado pela API.
    """

    # --------------------------------------------------------
    # CÁLCULO AUTOMÁTICO DA CALIBRAÇÃO
    # --------------------------------------------------------

    calibracao = calcular_calibracao(
        dispositivo.proxima_calibracao,
        dispositivo.status
    )


    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    return {

        "id": dispositivo.id,

        "numero": dispositivo.numero,

        "descricao": dispositivo.descricao,

        "cliente": dispositivo.cliente,

        "part_number": dispositivo.part_number,

        "ultima_calibracao": (
            dispositivo.ultima_calibracao.isoformat()
            if dispositivo.ultima_calibracao
            else None
        ),

        "proxima_calibracao": (
            dispositivo.proxima_calibracao.isoformat()
            if dispositivo.proxima_calibracao
            else None
        ),

        "condicao": dispositivo.condicao,

        "status": dispositivo.status,

        "calibracao": calibracao,

        "qr_code_url": url_for(
            "device_qr_code",
            numero=dispositivo.numero
        ),

        "device_url": url_for(
            "device_page",
            numero=dispositivo.numero
        )

    }


# ============================================================
# LISTAR TODOS OS DISPOSITIVOS
# ============================================================

@devices.route(
    "/devices",
    methods=["GET"]
)
def listar_dispositivos():

    dispositivos = Device.query.all()


    dados = [
        serializar_dispositivo(dispositivo)
        for dispositivo in dispositivos
    ]


    return jsonify(dados)


# ============================================================
# BUSCAR UM DISPOSITIVO
# ============================================================

@devices.route(
    "/devices/<path:numero>",
    methods=["GET"]
)
def buscar_dispositivo(numero):

    print("========================================")
    print("BUSCANDO DISPOSITIVO")
    print(f"Número recebido: [{numero}]")
    print("========================================")

    dispositivo = Device.query.filter_by(
        numero=numero
    ).first()

    print(f"Resultado: {dispositivo}")

    if dispositivo is None:

        return jsonify({
            "erro": "Dispositivo não encontrado.",
            "numero_recebido": numero
        }), 404

    return jsonify(
        serializar_dispositivo(dispositivo)
    )

