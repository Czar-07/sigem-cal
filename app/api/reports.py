# ============================================================
# SIGEM CAL
# API DE RELATÓRIOS
# ============================================================

from flask import Blueprint, jsonify, send_file

from app.services.report_service import (
    gerar_relatorio,
    obter_clientes,
    obter_filtros_request
)


reports = Blueprint(
    "reports",
    __name__
)


# ============================================================
# CLIENTES
# ============================================================

@reports.route(
    "/api/reports/clients",
    methods=["GET"]
)
def listar_clientes():

    try:

        clientes = obter_clientes()

        return jsonify({
            "success": True,
            "clientes": clientes
        })

    except Exception as erro:

        print(
            "Erro ao carregar clientes:",
            erro
        )

        return jsonify({
            "success": False,
            "clientes": [],
            "message": "Não foi possível carregar os clientes."
        }), 500


# ============================================================
# PDF
# ============================================================

@reports.route(
    "/api/reports/pdf",
    methods=["GET"]
)
def gerar_pdf():

    try:

        filtros = obter_filtros_request()

        buffer = gerar_relatorio(
            tipo=filtros["tipo"],
            cliente=filtros["cliente"],
            status=filtros["status"],
            periodo=filtros["periodo"]
        )

        nome_tipo = {
            "metrological": "metrologico",
            "calibrations": "calibracoes",
            "inventory": "inventario"
        }.get(
            filtros["tipo"],
            "relatorio"
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=(
                f"SIGEM_CAL_"
                f"{nome_tipo}_"
                f"{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"
                f".pdf"
            )
        )

    except Exception as erro:

        print(
            "Erro ao gerar relatório PDF:",
            erro
        )

        return jsonify({
            "success": False,
            "message": "Não foi possível gerar o relatório PDF.",
            "error": str(erro)
        }), 500


# ============================================================
# RESUMO
# ============================================================

@reports.route(
    "/api/reports/summary",
    methods=["GET"]
)
def resumo_relatorios():

    try:

        from datetime import datetime

        from app.models.device import Device

        hoje = datetime.now().date()

        dispositivos = Device.query.all()

        total = len(dispositivos)
        calibrados = 0
        vencendo_30 = 0
        atrasados = 0

        for dispositivo in dispositivos:

            status = str(
                dispositivo.status or ""
            ).strip().upper()

            if status == "CALIBRADO":
                calibrados += 1

            if dispositivo.proxima_calibracao:

                dias = (
                    dispositivo.proxima_calibracao - hoje
                ).days

                if 0 <= dias <= 30:
                    vencendo_30 += 1

                elif dias < 0:
                    atrasados += 1

        return jsonify({
            "success": True,
            "resumo": {
                "total": total,
                "calibrados": calibrados,
                "vencendo_30": vencendo_30,
                "atrasados": atrasados
            }
        })

    except Exception as erro:

        print(
            "Erro no resumo dos relatórios:",
            erro
        )

        return jsonify({
            "success": False,
            "message": "Não foi possível carregar o resumo."
        }), 500
