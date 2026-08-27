from flask import Blueprint, jsonify
from datetime import date

from app.models.device import Device


calibrations = Blueprint(
    "calibrations",
    __name__
)


# ============================================================
# API — CALIBRAÇÕES
# ============================================================

@calibrations.route(
    "/api/calibrations",
    methods=["GET"]
)
def listar_calibracoes():

    dispositivos = Device.query.all()

    hoje = date.today()

    registros = []

    total = 0
    validas = 0
    vencendo = 0
    atrasadas = 0

    for dispositivo in dispositivos:

        status = str(
            dispositivo.status or ""
        ).strip().upper()

        # ----------------------------------------------------
        # INATIVOS
        # ----------------------------------------------------

        if status == "INATIVO":
            continue

        total += 1

        dias_restantes = None
        situacao = "Sem data"
        classe = "sem-data"

        # ----------------------------------------------------
        # PRÓXIMA CALIBRAÇÃO
        # ----------------------------------------------------

        if dispositivo.proxima_calibracao:

            data_calibracao = (
                dispositivo.proxima_calibracao
            )

            dias_restantes = (
                data_calibracao - hoje
            ).days

            # -----------------------------------------------
            # ATRASADA
            # -----------------------------------------------

            if dias_restantes < 0:

                atrasadas += 1

                situacao = "Atrasada"

                classe = "atrasada"

            # -----------------------------------------------
            # VENCE HOJE
            # -----------------------------------------------

            elif dias_restantes == 0:

                vencendo += 1

                situacao = "Vence hoje"

                classe = "hoje"

            # -----------------------------------------------
            # VENCENDO EM ATÉ 30 DIAS
            # -----------------------------------------------

            elif dias_restantes <= 30:

                vencendo += 1

                situacao = "Vencendo"

                classe = "vencendo"

            # -----------------------------------------------
            # VÁLIDA
            # -----------------------------------------------

            else:

                validas += 1

                situacao = "Válida"

                classe = "valida"

        else:

            situacao = "Sem data"

            classe = "sem-data"

        # ----------------------------------------------------
        # REGISTRO
        # ----------------------------------------------------

        registros.append({

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

            "dias_restantes": dias_restantes,

            "situacao": situacao,

            "classe": classe,

            "status": dispositivo.status,

            "condicao": dispositivo.condicao

        })

    return jsonify({

        "success": True,

        "resumo": {

            "total": total,

            "validas": validas,

            "vencendo": vencendo,

            "atrasadas": atrasadas

        },

        "calibracoes": registros

    })