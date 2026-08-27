# ============================================================
# SIGEM CAL
# API — CONFIGURAÇÕES
# ============================================================

from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    request
)

from app.database.database import db
from app.models.setting import Setting


# ============================================================
# BLUEPRINT
# ============================================================

settings = Blueprint(
    "settings",
    __name__,
    url_prefix="/api/settings"
)


# ============================================================
# CONFIGURAÇÕES PADRÃO
# ============================================================

DEFAULT_SETTINGS = {

    # ========================================================
    # GERAL
    # ========================================================

    "system.name": {
        "valor": "SIGEM CAL",
        "tipo": "string",
        "categoria": "geral",
        "descricao": "Nome do sistema"
    },

    "system.description": {
        "valor":
            "Sistema Inteligente de Gestão de Calibração",
        "tipo": "string",
        "categoria": "geral",
        "descricao": "Descrição do sistema"
    },

    "system.language": {
        "valor": "pt-BR",
        "tipo": "string",
        "categoria": "geral",
        "descricao": "Idioma principal do sistema"
    },

    "system.timezone": {
        "valor": "America/Sao_Paulo",
        "tipo": "string",
        "categoria": "geral",
        "descricao": "Fuso horário do sistema"
    },


    "company.name": {
        "valor": "Itaesbra",
        "tipo": "string",
        "categoria": "geral",
        "descricao": "Empresa responsável pelo sistema"
    },

    # ========================================================
    # APARÊNCIA
    # ========================================================

    "appearance.theme": {
        "valor": "light",
        "tipo": "string",
        "categoria": "aparencia",
        "descricao": "Tema visual do sistema"
    },

    "appearance.sidebar_collapsed": {
        "valor": "false",
        "tipo": "boolean",
        "categoria": "aparencia",
        "descricao": "Inicia o menu lateral recolhido"
    },

    "appearance.animations": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "aparencia",
        "descricao": "Ativa animações da interface"
    },


    # ========================================================
    # NOTIFICAÇÕES
    # ========================================================

    "notifications.enabled": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "notificacoes",
        "descricao": "Ativa notificações do sistema"
    },

    "notifications.calibration": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "notificacoes",
        "descricao": "Notificações relacionadas à calibração"
    },

    "notifications.expiration_days": {
        "valor": "30",
        "tipo": "integer",
        "categoria": "notificacoes",
        "descricao":
            "Dias de antecedência para alertas de validade"
    },

    "notifications.email_enabled": {
        "valor": "false", "tipo": "boolean", "categoria": "notificacoes",
        "descricao": "Ativa o envio automático de e-mails"
    },
    "notifications.smtp_host": {
        "valor": "", "tipo": "string", "categoria": "notificacoes",
        "descricao": "Servidor SMTP"
    },
    "notifications.smtp_port": {
        "valor": "587", "tipo": "integer", "categoria": "notificacoes",
        "descricao": "Porta SMTP"
    },
    "notifications.smtp_username": {
        "valor": "", "tipo": "string", "categoria": "notificacoes",
        "descricao": "Usuário SMTP"
    },
    "notifications.smtp_password": {
        "valor": "", "tipo": "string", "categoria": "notificacoes",
        "descricao": "Senha SMTP"
    },
    "notifications.smtp_sender": {
        "valor": "", "tipo": "string", "categoria": "notificacoes",
        "descricao": "E-mail remetente"
    },
    "notifications.recipients": {
        "valor": "", "tipo": "string", "categoria": "notificacoes",
        "descricao": "Destinatários separados por vírgula"
    },
    "notifications.smtp_tls": {
        "valor": "true", "tipo": "boolean", "categoria": "notificacoes",
        "descricao": "Usa STARTTLS"
    },
    "notifications.smtp_ssl": {
        "valor": "false", "tipo": "boolean", "categoria": "notificacoes",
        "descricao": "Usa conexão SMTP SSL"
    },
    "notifications.check_interval_minutes": {
        "valor": "30", "tipo": "integer", "categoria": "notificacoes",
        "descricao": "Intervalo do monitoramento automático"
    },


    # ========================================================
    # CALIBRAÇÃO
    # ========================================================

    "calibration.alert_days": {
        "valor": "30",
        "tipo": "integer",
        "categoria": "calibracao",
        "descricao":
            "Antecedência para alerta de calibração"
    },

    "calibration.overdue_enabled": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "calibracao",
        "descricao":
            "Identifica equipamentos com calibração vencida"
    },

    "calibration.auto_status": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "calibracao",
        "descricao":
            "Atualiza automaticamente o status de calibração"
    },


    # ========================================================
    # CERTIFICADOS
    # ========================================================

    "certificates.allowed_extension": {
        "valor": ".pdf",
        "tipo": "string",
        "categoria": "certificados",
        "descricao":
            "Extensão permitida para certificados"
    },

    "certificates.max_size_mb": {
        "valor": "20",
        "tipo": "integer",
        "categoria": "certificados",
        "descricao":
            "Tamanho máximo de certificado em MB"
    },

    "certificates.auto_organize": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "certificados",
        "descricao":
            "Organiza automaticamente os arquivos"
    },


    # ========================================================
    # ARMAZENAMENTO
    # ========================================================

    "storage.upload_folder": {
        "valor": "uploads",
        "tipo": "string",
        "categoria": "armazenamento",
        "descricao":
            "Diretório principal dos arquivos"
    },

    "storage.keep_original_name": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "armazenamento",
        "descricao":
            "Mantém o nome original dos arquivos"
    },


    # ========================================================
    # SISTEMA
    # ========================================================

    "system.auto_refresh": {
        "valor": "true",
        "tipo": "boolean",
        "categoria": "sistema",
        "descricao":
            "Atualiza automaticamente os dados"
    },

    "system.refresh_enabled": {
        "valor": "true", "tipo": "boolean", "categoria": "sistema",
        "descricao": "Ativa atualização automática da interface"
    },

    "system.refresh_interval": {
        "valor": "60",
        "tipo": "integer",
        "categoria": "sistema",
        "descricao":
            "Intervalo de atualização automática em segundos"
    }

}


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def setting_para_dict(setting):

    return setting.to_dict()


# ============================================================
# VALIDAR TIPO
# ============================================================

def validar_valor(valor, tipo):

    if tipo == "integer":

        try:

            return int(valor)

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "O valor precisa ser um número inteiro."
            )


    if tipo == "float":

        try:

            return float(valor)

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "O valor precisa ser um número decimal."
            )


    if tipo == "boolean":

        if isinstance(valor, bool):

            return valor


        if isinstance(valor, str):

            valor_normalizado = (
                valor
                .strip()
                .lower()
            )

            if valor_normalizado in (
                "true",
                "1",
                "yes",
                "sim",
                "on"
            ):

                return True


            if valor_normalizado in (
                "false",
                "0",
                "no",
                "nao",
                "não",
                "off"
            ):

                return False


        raise ValueError(
            "O valor booleano informado é inválido."
        )


    return str(valor)


# ============================================================
# GARANTIR CONFIGURAÇÕES PADRÃO
# ============================================================

def garantir_configuracoes_padrao():

    alterado = False


    for chave, dados in DEFAULT_SETTINGS.items():

        setting = (
            Setting.query
            .filter_by(
                chave=chave
            )
            .first()
        )


        if setting:

            continue


        setting = Setting(

            chave=chave,

            valor=str(
                dados["valor"]
            ),

            tipo=dados["tipo"],

            categoria=dados["categoria"],

            descricao=dados["descricao"],

            editavel=True,

            ativo=True

        )


        db.session.add(
            setting
        )

        alterado = True


    if alterado:

        db.session.commit()


# ============================================================
# GET — LISTAR CONFIGURAÇÕES
# ============================================================

@settings.get("")
def listar_configuracoes():

    try:

        garantir_configuracoes_padrao()


        categoria = (
            request.args
            .get("categoria")
        )


        query = Setting.query


        if categoria:

            query = query.filter(
                Setting.categoria == categoria
            )


        configuracoes = (

            query

            .filter(
                Setting.ativo.is_(True)
            )

            .order_by(

                Setting.categoria.asc(),

                Setting.chave.asc()

            )

            .all()

        )


        return jsonify({

            "success": True,

            "total":
                len(configuracoes),

            "configuracoes": [

                setting_para_dict(
                    setting
                )

                for setting
                in configuracoes

            ]

        })


    except Exception as erro:

        print(
            "SIGEM CAL — Erro ao listar configurações:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível carregar as configurações."

        }), 500


# ============================================================
# GET — CONFIGURAÇÃO POR CHAVE
# ============================================================

@settings.get("/<string:chave>")
def obter_configuracao(chave):

    setting = (

        Setting.query

        .filter_by(
            chave=chave
        )

        .first()

    )


    if not setting:

        return jsonify({

            "success": False,

            "message":
                "Configuração não encontrada."

        }), 404


    return jsonify({

        "success": True,

        "configuracao":
            setting_para_dict(
                setting
            )

    })


# ============================================================
# PUT — ALTERAR CONFIGURAÇÃO
# ============================================================

@settings.put("/<string:chave>")
def atualizar_configuracao(chave):

    setting = (

        Setting.query

        .filter_by(
            chave=chave
        )

        .first()

    )


    if not setting:

        return jsonify({

            "success": False,

            "message":
                "Configuração não encontrada."

        }), 404


    if not setting.editavel:

        return jsonify({

            "success": False,

            "message":
                "Esta configuração não pode ser alterada."

        }), 403


    try:

        dados = (

            request.get_json(
                silent=True
            )

            or {}

        )


        if "valor" not in dados:

            return jsonify({

                "success": False,

                "message":
                    "O valor da configuração é obrigatório."

            }), 400


        valor = validar_valor(

            dados["valor"],

            setting.tipo

        )


        setting.set_value(
            valor
        )


        setting.updated_at = (
            datetime.utcnow()
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Configuração atualizada com sucesso.",

            "configuracao":
                setting_para_dict(
                    setting
                )

        })


    except ValueError as erro:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                str(erro)

        }), 400


    except Exception as erro:

        db.session.rollback()


        print(
            "SIGEM CAL — Erro ao atualizar configuração:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível atualizar a configuração."

        }), 500


# ============================================================
# PUT — ATUALIZAR VÁRIAS CONFIGURAÇÕES
# ============================================================

@settings.put("/bulk")
def atualizar_configuracoes():

    try:

        dados = (

            request.get_json(
                silent=True
            )

            or {}

        )


        configuracoes = (
            dados.get(
                "configuracoes"
            )
        )


        if not isinstance(
            configuracoes,
            dict
        ):

            return jsonify({

                "success": False,

                "message":
                    "Formato de configurações inválido."

            }), 400


        atualizadas = []


        for chave, valor in configuracoes.items():

            setting = (

                Setting.query

                .filter_by(
                    chave=chave
                )

                .first()

            )


            if not setting:

                continue


            if not setting.editavel:

                continue


            # Segredos não são sobrescritos quando o formulário os deixa em branco.
            if "password" in setting.chave.lower() and (valor is None or str(valor) == ""):
                continue

            valor_validado = validar_valor(

                valor,

                setting.tipo

            )


            setting.set_value(
                valor_validado
            )


            setting.updated_at = (
                datetime.utcnow()
            )


            atualizadas.append(
                setting
            )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Configurações salvas com sucesso.",

            "total":
                len(atualizadas),

            "configuracoes": [

                setting_para_dict(
                    setting
                )

                for setting
                in atualizadas

            ]

        })


    except ValueError as erro:

        db.session.rollback()


        return jsonify({

            "success": False,

            "message":
                str(erro)

        }), 400


    except Exception as erro:

        db.session.rollback()


        print(
            "SIGEM CAL — Erro ao salvar configurações:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível salvar as configurações."

        }), 500


# ============================================================
# POST — RESTAURAR CONFIGURAÇÃO INDIVIDUAL
# ============================================================

@settings.post(
    "/<string:chave>/reset"
)
def restaurar_configuracao(chave):

    if chave not in DEFAULT_SETTINGS:

        return jsonify({

            "success": False,

            "message":
                "Não existe configuração padrão para esta chave."

        }), 404


    setting = (

        Setting.query

        .filter_by(
            chave=chave
        )

        .first()

    )


    if not setting:

        return jsonify({

            "success": False,

            "message":
                "Configuração não encontrada."

        }), 404


    if not setting.editavel:

        return jsonify({

            "success": False,

            "message":
                "Esta configuração não pode ser restaurada."

        }), 403


    try:

        dados_padrao = (
            DEFAULT_SETTINGS[
                chave
            ]
        )


        setting.set_value(dados_padrao["valor"])


        setting.updated_at = (
            datetime.utcnow()
        )


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Configuração restaurada para o padrão.",

            "configuracao":
                setting_para_dict(
                    setting
                )

        })


    except Exception as erro:

        db.session.rollback()


        print(
            "SIGEM CAL — Erro ao restaurar configuração:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível restaurar a configuração."

        }), 500


# ============================================================
# POST — RESTAURAR TODAS
# ============================================================

@settings.post("/reset-all")
def restaurar_todas_configuracoes():

    try:

        garantir_configuracoes_padrao()


        restauradas = 0


        for chave, dados in DEFAULT_SETTINGS.items():

            setting = (

                Setting.query

                .filter_by(
                    chave=chave
                )

                .first()

            )


            if not setting:

                continue


            if not setting.editavel:

                continue


            setting.set_value(dados["valor"])


            setting.updated_at = (
                datetime.utcnow()
            )


            restauradas += 1


        db.session.commit()


        return jsonify({

            "success": True,

            "message":
                "Configurações restauradas com sucesso.",

            "total":
                restauradas

        })


    except Exception as erro:

        db.session.rollback()


        print(
            "SIGEM CAL — Erro ao restaurar configurações:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível restaurar as configurações."

        }), 500


# ============================================================
# GET — CATEGORIAS
# ============================================================

@settings.get("/meta/categories")
def listar_categorias():

    try:

        garantir_configuracoes_padrao()


        categorias = (

            db.session.query(
                Setting.categoria
            )

            .filter(
                Setting.ativo.is_(True)
            )

            .distinct()

            .order_by(
                Setting.categoria.asc()
            )

            .all()

        )


        return jsonify({

            "success": True,

            "categorias": [

                categoria[0]

                for categoria
                in categorias

            ]

        })


    except Exception as erro:

        print(
            "SIGEM CAL — Erro ao listar categorias:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível carregar as categorias."

        }), 500


# ============================================================
# POST — RECRIAR PADRÕES AUSENTES
# ============================================================

@settings.post("/initialize")
def inicializar_configuracoes():

    try:

        garantir_configuracoes_padrao()


        return jsonify({

            "success": True,

            "message":
                "Configurações inicializadas com sucesso."

        })


    except Exception as erro:

        db.session.rollback()


        print(
            "SIGEM CAL — Erro ao inicializar configurações:",
            erro
        )


        return jsonify({

            "success": False,

            "message":
                "Não foi possível inicializar as configurações."

        }), 500