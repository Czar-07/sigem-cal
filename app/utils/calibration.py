from datetime import date, datetime


# ============================================================
# CONFIGURAÇÕES
# ============================================================

DIAS_ALERTA = 30


# ============================================================
# NORMALIZAR DATA
# ============================================================

def normalizar_data(data):
    """
    Converte diferentes formatos de data para datetime.date.

    Aceita:
        - datetime.date
        - datetime.datetime
        - string YYYY-MM-DD
        - None

    Retorna:
        datetime.date ou None
    """

    if not data:
        return None


    # --------------------------------------------------------
    # datetime
    # --------------------------------------------------------

    if isinstance(data, datetime):

        return data.date()


    # --------------------------------------------------------
    # date
    # --------------------------------------------------------

    if isinstance(data, date):

        return data


    # --------------------------------------------------------
    # string
    # --------------------------------------------------------

    if isinstance(data, str):

        valor = data.strip()


        if not valor:
            return None


        try:

            return date.fromisoformat(
                valor[:10]
            )

        except ValueError:

            return None


    return None


# ============================================================
# CALCULAR CALIBRAÇÃO
# ============================================================

def calcular_calibracao(
    proxima_calibracao,
    status=None
):
    """
    Calcula automaticamente a situação metrológica
    de um dispositivo.

    Retorna informações padronizadas para a API
    e para o frontend.
    """


    # ========================================================
    # DATA ATUAL
    # ========================================================

    hoje = date.today()


    # ========================================================
    # STATUS
    # ========================================================

    status_normalizado = str(
        status or ""
    ).strip().lower()


    # ========================================================
    # RESULTADO BASE
    # ========================================================

    resultado = {

        "situacao": "Não informado",

        "classe": "desconhecido",

        "dias_restantes": None,

        "dias_atraso": 0,

        "vencida": False,

        "proxima": False,

        "vence_hoje": False,

        "data_validade": None

    }


    # ========================================================
    # STATUS — INATIVO
    # ========================================================

    if status_normalizado == "inativo":

        resultado.update({

            "situacao": "Inativo",

            "classe": "inativo"

        })

        return resultado


    # ========================================================
    # STATUS — DESENVOLVIMENTO
    # ========================================================

    if status_normalizado == "desenvolvimento":

        resultado.update({

            "situacao": "Em desenvolvimento",

            "classe": "desenvolvimento"

        })

        return resultado


    # ========================================================
    # NORMALIZAR DATA
    # ========================================================

    data_validade = normalizar_data(
        proxima_calibracao
    )


    # ========================================================
    # SEM DATA
    # ========================================================

    if data_validade is None:

        resultado.update({

            "situacao": "Sem validade definida",

            "classe": "desconhecido"

        })

        return resultado


    # ========================================================
    # DATA DE VALIDADE
    # ========================================================

    resultado["data_validade"] = (
        data_validade.isoformat()
    )


    # ========================================================
    # DIFERENÇA ENTRE DATAS
    # ========================================================

    diferenca = (
        data_validade - hoje
    ).days


    # ========================================================
    # VENCIDA
    # ========================================================

    if diferenca < 0:

        dias_atraso = abs(diferenca)


        resultado.update({

            "situacao": "Calibração atrasada",

            "classe": "atrasado",

            "dias_restantes": 0,

            "dias_atraso": dias_atraso,

            "vencida": True,

            "proxima": False,

            "vence_hoje": False

        })

        return resultado


    # ========================================================
    # VENCE HOJE
    # ========================================================

    if diferenca == 0:

        resultado.update({

            "situacao": "Vence hoje",

            "classe": "vence-hoje",

            "dias_restantes": 0,

            "dias_atraso": 0,

            "vencida": False,

            "proxima": True,

            "vence_hoje": True

        })

        return resultado


    # ========================================================
    # PRÓXIMA DO VENCIMENTO
    # ========================================================

    if diferenca <= DIAS_ALERTA:

        resultado.update({

            "situacao": "Próxima do vencimento",

            "classe": "proxima",

            "dias_restantes": diferenca,

            "dias_atraso": 0,

            "vencida": False,

            "proxima": True,

            "vence_hoje": False

        })

        return resultado


    # ========================================================
    # CALIBRAÇÃO VÁLIDA
    # ========================================================

    resultado.update({

        "situacao": "Calibração válida",

        "classe": "valida",

        "dias_restantes": diferenca,

        "dias_atraso": 0,

        "vencida": False,

        "proxima": False,

        "vence_hoje": False

    })


    return resultado