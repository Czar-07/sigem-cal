# ============================================================
# SIGEM CAL
# API — CERTIFICADOS
# ============================================================

import io
import os

from datetime import datetime

from sqlalchemy.orm import joinedload

from flask import (
    Blueprint,
    jsonify,
    request,
    send_file,
    current_app,
    redirect
)

import io

from app.utils.r2_storage import (
    get_r2,
    content_type_for
)

from pathlib import Path
from html import escape

from openpyxl import load_workbook

from app.database.database import db

from app.models.device import Device
from app.models.certificate import Certificate

from app.services.certificate_sync_service import synchronize_certificates, read_source_member

from app.utils.certificate_storage import (
    salvar_certificado,
    excluir_certificado_arquivo
)


# ============================================================
# BLUEPRINT
# ============================================================

certificate = Blueprint(
    "certificate",
    __name__,
    url_prefix="/api/certificates"
)

def normalizar_r2_key(valor: str | None) -> str | None:
    """
    Converte diferentes formatos de referência R2
    para a chave real do objeto dentro do bucket.

    Exemplos aceitos:

    r2://sigem-certificados/Certificados/arquivo.xlsx
    r2:/sigem-certificados/Certificados/arquivo.xlsx
    /Certificados/arquivo.xlsx
    Certificados/arquivo.xlsx

    Resultado:

    Certificados/arquivo.xlsx
    """
    if not valor:
        return None

    valor = str(valor).strip().replace("\\", "/")

    # URI completa do R2:
    # r2://bucket/key
    if valor.lower().startswith("r2://"):
        resto = valor[5:]  # remove "r2://"

        # Remove o nome do bucket.
        # Ex.: sigem-certificados/Certificados/arquivo.xlsx
        partes = resto.split("/", 1)

        if len(partes) == 2:
            valor = partes[1]
        else:
            return None

    # Formato quebrado r2:/bucket/key
    elif valor.lower().startswith("r2:/"):
        resto = valor[4:]  # remove "r2:/"

        partes = resto.split("/", 1)

        if len(partes) == 2:
            valor = partes[1]
        else:
            return None

    # Remove barras iniciais
    valor = valor.lstrip("/")

    # Normaliza barras duplicadas
    while "//" in valor:
        valor = valor.replace("//", "/")

    return valor


# ============================================================
# SERIALIZAÇÃO
# ============================================================

def certificado_para_dict(
    certificado
):

    device = getattr(certificado, "device", None)

    return {

        "id":
            certificado.id,

        "device_id":
            certificado.device_id,

        "ano":
            certificado.ano,

        "numero_certificado":
            certificado.numero_certificado,

        "nome_arquivo":
            certificado.nome_arquivo,

        "arquivo":
            certificado.arquivo,

        "data_emissao":
            (
                certificado.data_emissao.isoformat()
                if certificado.data_emissao
                else None
            ),

        "data_validade":
            (
                certificado.data_validade.isoformat()
                if certificado.data_validade
                else None
            ),

        "laboratorio":
            certificado.laboratorio,

        "resultado":
            certificado.resultado,

        "observacoes":
            certificado.observacoes,

        "source_key": certificado.source_key,
        "source_hash": certificado.source_hash,
        "source_type": certificado.source_type,
        "source_path": certificado.source_path,

        "created_at":
            (
                certificado.created_at.isoformat()
                if certificado.created_at
                else None
            ),

        "updated_at":
            (
                certificado.updated_at.isoformat()
                if certificado.updated_at
                else None
            ),

        # ====================================================
        # DISPOSITIVO
        # ====================================================

        "numero_dispositivo":
            device.numero
            if device
            else None,

        "numero":
            device.numero
            if device
            else None,

        "descricao":
            device.descricao
            if device
            else None,

        "cliente":
            device.cliente
            if device
            else None,

        "part_number":
            device.part_number
            if device
            else None,

        "status_dispositivo":
            device.status
            if device
            else None,

        "condicao_dispositivo":
            device.condicao
            if device
            else None

    }


# ============================================================
# CONVERTER DATA
# ============================================================

def converter_data(valor):

    if not valor:
        return None

    if hasattr(
        valor,
        "isoformat"
    ):
        return valor

    try:

        return datetime.strptime(
            str(valor),
            "%Y-%m-%d"
        ).date()

    except ValueError:

        raise ValueError(
            "Data inválida. "
            "Use o formato YYYY-MM-DD."
        )


# ============================================================
# POST — SINCRONIZAR FONTE DE CERTIFICADOS
# ============================================================

@certificate.post("/sync")
def sincronizar_certificados():
    try:
        dados = request.get_json(silent=True) or {}
        fonte = dados.get("source") or current_app.config.get("CERTIFICATES_FOLDER")
        if not fonte:
            base = Path(current_app.root_path).parent.resolve()
            candidatos = [
                base / "Certificados.zip",
                base / "certificados.zip",
                base / "Certificados",
                base / "certificados",
                Path.cwd() / "Certificados.zip",
                Path.cwd() / "certificados.zip",
                Path.cwd() / "Certificados",
                Path.cwd() / "certificados",
            ]
            fonte_path = next((p for p in candidatos if p.exists()), None)
            fonte = str(fonte_path) if fonte_path else ""
        resultado = synchronize_certificates(fonte)
        status = 200 if resultado.get("success") else 400
        return jsonify(resultado), status
    except Exception as erro:
        db.session.rollback()
        current_app.logger.exception("SIGEM CAL — Erro na sincronização de certificados")
        return jsonify({
            "success": False,
            "message": "Falha ao sincronizar certificados.",
            "error": str(erro),
            "type": type(erro).__name__,
        }), 500


# ============================================================
# GET — LISTAR
# ============================================================

@certificate.get("")
def listar_certificados():

    try:

        query = Certificate.query

        device_id = request.args.get(
            "device_id",
            type=int
        )

        ano = request.args.get(
            "ano",
            type=int
        )

        resultado = request.args.get(
            "resultado"
        )

        if device_id:

            query = query.filter(
                Certificate.device_id ==
                device_id
            )

        if ano:

            query = query.filter(
                Certificate.ano == ano
            )

        if resultado:

            query = query.filter(
                Certificate.resultado ==
                resultado
            )

        certificados = (
            query
            .options(joinedload(Certificate.device))
            .order_by(
                Certificate.ano.desc(),
                Certificate.id.desc()
            )
            .all()
        )

        lista = [
            certificado_para_dict(
                item
            )
            for item in certificados
        ]

        return jsonify({

            "success": True,

            "total":
                len(lista),

            "certificados":
                lista

        })

    except Exception as erro:

        print(
            "SIGEM CAL — Erro ao listar:",
            erro
        )

        return jsonify({

            "success": False,

            "message":
                "Não foi possível carregar os certificados."

        }), 500


# ============================================================
# GET — RESUMO
# ============================================================

@certificate.get("/summary")
def resumo_certificados():

    try:

        certificados = (
            Certificate.query
            .all()
        )

        hoje = datetime.now().date()

        ano_atual = hoje.year

        total = len(
            certificados
        )

        ano_atual_total = sum(
            1
            for item in certificados
            if item.ano == ano_atual
        )

        validos = 0
        vencendo = 0
        vencidos = 0
        sem_validade = 0

        for certificado in certificados:

            validade = (
                certificado.data_validade
            )

            if not validade:

                sem_validade += 1

                continue

            if validade < hoje:

                vencidos += 1

                continue

            dias = (
                validade - hoje
            ).days

            if dias <= 30:

                vencendo += 1

                continue

            validos += 1

        return jsonify({

            "success": True,

            "resumo": {

                "total":
                    total,

                "ano_atual":
                    ano_atual_total,

                "validos":
                    validos,

                "vencendo":
                    vencendo,

                "vencidos":
                    vencidos,

                "sem_validade":
                    sem_validade

            }

        })

    except Exception as erro:

        print(
            "SIGEM CAL — Erro no resumo:",
            erro
        )

        return jsonify({

            "success": False,

            "message":
                "Não foi possível gerar o resumo."

        }), 500


# ============================================================
# GET — POR ID
# ============================================================

@certificate.get(
    "/<int:certificate_id>"
)
def obter_certificado(
    certificate_id
):

    certificado = (
        Certificate.query
        .options(joinedload(Certificate.device))
        .filter_by(
            id=certificate_id
        )
        .first()
    )

    if not certificado:

        return jsonify({

            "success": False,

            "message":
                "Certificado não encontrado."

        }), 404

    return jsonify({

        "success": True,

        "certificado":
            certificado_para_dict(
                certificado
            )

    })


# ============================================================
# POST — CRIAR SEM PDF
# ============================================================

@certificate.post("")
def criar_certificado():

    try:

        dados = (
            request.get_json(
                silent=True
            )
            or {}
        )

        device_id = dados.get(
            "device_id"
        )

        if not device_id:

            return jsonify({

                "success": False,

                "message":
                    "O dispositivo é obrigatório."

            }), 400

        device = (
            Device.query
            .filter_by(
                id=device_id
            )
            .first()
        )

        if not device:

            return jsonify({

                "success": False,

                "message":
                    "Dispositivo não encontrado."

            }), 404

        try:

            ano = int(
                dados.get("ano")
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({

                "success": False,

                "message":
                    "O ano informado é inválido."

            }), 400

        certificado = Certificate(

            device_id=device.id,

            ano=ano,

            numero_certificado=
                dados.get(
                    "numero_certificado"
                ),

            data_emissao=
                converter_data(
                    dados.get(
                        "data_emissao"
                    )
                ),

            data_validade=
                converter_data(
                    dados.get(
                        "data_validade"
                    )
                ),

            laboratorio=
                dados.get(
                    "laboratorio"
                ),

            resultado=
                dados.get(
                    "resultado"
                ),

            observacoes=
                dados.get(
                    "observacoes"
                )

        )

        db.session.add(
            certificado
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Certificado criado com sucesso.",

            "certificado":
                certificado_para_dict(
                    certificado
                )

        }), 201

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
            "SIGEM CAL — Erro ao criar:",
            erro
        )

        return jsonify({

            "success": False,

            "message":
                "Não foi possível criar o certificado."

        }), 500


# ============================================================
# POST — UPLOAD PDF
# ============================================================

@certificate.post("/upload")
def upload_certificado():

    try:

        device_id = request.form.get(
            "device_id",
            type=int
        )

        ano = request.form.get(
            "ano",
            type=int
        )

        numero_certificado = (
            request.form.get(
                "numero_certificado"
            )
        )

        arquivo = request.files.get(
            "arquivo"
        )

        if not device_id:

            return jsonify({

                "success": False,

                "message":
                    "O dispositivo é obrigatório."

            }), 400

        if not ano:

            return jsonify({

                "success": False,

                "message":
                    "O ano é obrigatório."

            }), 400

        if not arquivo:

            return jsonify({

                "success": False,

                "message":
                    "O arquivo PDF é obrigatório."

            }), 400

        nome_original = (
            arquivo.filename or ""
        )

        if not nome_original:

            return jsonify({

                "success": False,

                "message":
                    "O arquivo não possui nome."

            }), 400

        if not nome_original.lower().endswith(
            ".pdf"
        ):

            return jsonify({

                "success": False,

                "message":
                    "Apenas arquivos PDF são permitidos."

            }), 400

        device = (
            Device.query
            .filter_by(
                id=device_id
            )
            .first()
        )

        if not device:

            return jsonify({

                "success": False,

                "message":
                    "Dispositivo não encontrado."

            }), 404

        dados_arquivo = (
            salvar_certificado(

                arquivo=arquivo,

                numero=(
                    numero_certificado
                    or device.numero
                ),

                ano=ano

            )
        )

        certificado = Certificate(

            device_id=device.id,

            ano=ano,

            numero_certificado=
                numero_certificado,

            nome_arquivo=
                dados_arquivo[
                    "nome_arquivo"
                ],

            arquivo=
                dados_arquivo[
                    "arquivo"
                ],

            data_emissao=
                converter_data(
                    request.form.get(
                        "data_emissao"
                    )
                ),

            data_validade=
                converter_data(
                    request.form.get(
                        "data_validade"
                    )
                ),

            laboratorio=
                request.form.get(
                    "laboratorio"
                ),

            resultado=
                request.form.get(
                    "resultado"
                ),

            observacoes=
                request.form.get(
                    "observacoes"
                )

        )

        db.session.add(
            certificado
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Certificado enviado com sucesso.",

            "certificado":
                certificado_para_dict(
                    certificado
                )

        }), 201

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
            "SIGEM CAL — Erro no upload:",
            erro
        )

        return jsonify({

            "success": False,

            "message":
                "Não foi possível enviar o certificado."

        }), 500


# ============================================================
# POST — SUBSTITUIR / ANEXAR PDF
# ============================================================

@certificate.post("/<int:certificate_id>/upload")
def substituir_certificado_arquivo(certificate_id):

    certificado = (
        Certificate.query
        .filter_by(id=certificate_id)
        .first()
    )

    if not certificado:
        return jsonify({
            "success": False,
            "message": "Certificado não encontrado."
        }), 404

    try:
        arquivo = request.files.get("arquivo")
        if not arquivo or not arquivo.filename:
            return jsonify({
                "success": False,
                "message": "Selecione um arquivo PDF."
            }), 400

        if not arquivo.filename.lower().endswith(".pdf"):
            return jsonify({
                "success": False,
                "message": "Apenas arquivos PDF são permitidos."
            }), 400

        device_id = request.form.get("device_id", type=int) or certificado.device_id
        device = Device.query.filter_by(id=device_id).first()

        if not device:
            return jsonify({
                "success": False,
                "message": "Dispositivo não encontrado."
            }), 404

        ano = request.form.get("ano", type=int) or certificado.ano
        numero = request.form.get("numero_certificado") or certificado.numero_certificado or device.numero

        # O novo arquivo é gravado primeiro. Assim, uma falha não destrói o PDF atual.
        novo_arquivo = salvar_certificado(
            arquivo=arquivo,
            numero=numero,
            ano=ano
        )

        arquivo_anterior = certificado.arquivo

        certificado.device_id = device.id
        certificado.ano = ano
        certificado.numero_certificado = request.form.get("numero_certificado") or None
        certificado.nome_arquivo = novo_arquivo["nome_arquivo"]
        certificado.arquivo = novo_arquivo["arquivo"]
        certificado.data_emissao = converter_data(request.form.get("data_emissao"))
        certificado.data_validade = converter_data(request.form.get("data_validade"))
        certificado.laboratorio = request.form.get("laboratorio") or None
        certificado.resultado = request.form.get("resultado") or None
        certificado.observacoes = request.form.get("observacoes") or None
        certificado.updated_at = datetime.utcnow()

        db.session.commit()

        if arquivo_anterior and arquivo_anterior != certificado.arquivo:
            try:
                excluir_certificado_arquivo(arquivo_anterior)
            except Exception as erro:
                print("SIGEM CAL — Erro ao remover PDF anterior:", erro)

        return jsonify({
            "success": True,
            "message": "Certificado atualizado com sucesso.",
            "certificado": certificado_para_dict(certificado)
        })

    except ValueError as erro:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": str(erro)
        }), 400

    except Exception as erro:
        db.session.rollback()
        print("SIGEM CAL — Erro ao substituir PDF:", erro)
        return jsonify({
            "success": False,
            "message": "Não foi possível atualizar o certificado."
        }), 500


# ============================================================
# PUT — ATUALIZAR
# ============================================================

@certificate.put(
    "/<int:certificate_id>"
)
def atualizar_certificado(
    certificate_id
):

    certificado = (
        Certificate.query
        .options(joinedload(Certificate.device))
        .filter_by(
            id=certificate_id
        )
        .first()
    )

    if not certificado:

        return jsonify({

            "success": False,

            "message":
                "Certificado não encontrado."

        }), 404

    try:

        dados = (
            request.get_json(
                silent=True
            )
            or {}
        )

        if "device_id" in dados:

            device = (
                Device.query
                .filter_by(
                    id=dados[
                        "device_id"
                    ]
                )
                .first()
            )

            if not device:

                return jsonify({

                    "success": False,

                    "message":
                        "Dispositivo não encontrado."

                }), 404

            certificado.device_id = (
                device.id
            )

        if "ano" in dados:

            try:

                certificado.ano = int(
                    dados["ano"]
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "O ano informado é inválido."

                }), 400

        campos = [
            "numero_certificado",
            "laboratorio",
            "resultado",
            "observacoes"
        ]

        for campo in campos:

            if campo in dados:

                setattr(
                    certificado,
                    campo,
                    dados[campo]
                )

        if "data_emissao" in dados:

            certificado.data_emissao = (
                converter_data(
                    dados[
                        "data_emissao"
                    ]
                )
            )

        if "data_validade" in dados:

            certificado.data_validade = (
                converter_data(
                    dados[
                        "data_validade"
                    ]
                )
            )

        certificado.updated_at = (
            datetime.utcnow()
        )

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Certificado atualizado com sucesso.",

            "certificado":
                certificado_para_dict(
                    certificado
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
            "SIGEM CAL — Erro ao atualizar:",
            erro
        )

        return jsonify({

            "success": False,

            "message":
                "Não foi possível atualizar o certificado."

        }), 500


def _xlsx_to_pdf(data: bytes, filename: str) -> bytes:
    """
    Converte XLSX/XLSM para PDF usando LibreOffice.

    O arquivo original permanece no R2.
    A conversão acontece somente em memória/arquivo temporário.
    """

    import shutil
    import subprocess
    import tempfile

    # --------------------------------------------------------
    # Localiza LibreOffice
    # --------------------------------------------------------

    soffice = (
        shutil.which("soffice")
        or shutil.which("libreoffice")
    )

    # Caminhos comuns do Windows
    if not soffice and os.name == "nt":
        caminhos_windows = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]

        for caminho in caminhos_windows:
            if os.path.exists(caminho):
                soffice = caminho
                break

    if not soffice:
        raise RuntimeError(
            "LibreOffice não encontrado. "
            "Instale o LibreOffice ou configure o caminho do soffice."
        )

    # --------------------------------------------------------
    # Diretório temporário
    # --------------------------------------------------------

    with tempfile.TemporaryDirectory(
        prefix="sigem_xlsx_"
    ) as temp_dir:

        nome_original = Path(filename).name

        if not nome_original.lower().endswith(
            (".xlsx", ".xlsm")
        ):
            nome_original += ".xlsx"

        arquivo_xlsx = Path(temp_dir) / nome_original

        # ----------------------------------------------------
        # Salva XLSX temporariamente
        # ----------------------------------------------------

        arquivo_xlsx.write_bytes(data)

        # ----------------------------------------------------
        # Conversão XLSX → PDF
        # ----------------------------------------------------

        comando = [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            temp_dir,
            str(arquivo_xlsx),
        ]

        resultado = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )

        if resultado.returncode != 0:
            raise RuntimeError(
                "Erro ao converter Excel para PDF: "
                f"{resultado.stderr or resultado.stdout}"
            )

        # ----------------------------------------------------
        # Nome esperado do PDF
        # ----------------------------------------------------

        arquivo_pdf = (
            Path(temp_dir)
            / f"{arquivo_xlsx.stem}.pdf"
        )

        if not arquivo_pdf.exists():
            # Algumas versões podem retornar o nome no stdout.
            pdfs = list(
                Path(temp_dir).glob("*.pdf")
            )

            if not pdfs:
                raise RuntimeError(
                    "LibreOffice terminou a conversão, "
                    "mas o PDF não foi encontrado. "
                    f"stdout={resultado.stdout} "
                    f"stderr={resultado.stderr}"
                )

            arquivo_pdf = pdfs[0]

        return arquivo_pdf.read_bytes()

# ============================================================
# GET — VISUALIZAR PDF
# ============================================================

@certificate.get("/<int:certificate_id>/view")
def visualizar_certificado(certificate_id):

    certificado = (
        Certificate.query
        .options(joinedload(Certificate.device))
        .filter_by(id=certificate_id)
        .first()
    )

    if not certificado:
        return jsonify({
            "success": False,
            "message": "Certificado não encontrado."
        }), 404

    if not certificado.arquivo:
        return jsonify({
            "success": False,
            "message": "Este certificado não possui arquivo."
        }), 404

    try:
        r2 = get_r2()

        key = normalizar_r2_key(certificado.arquivo)

        if not key:
            return jsonify({
                "success": False,
                "message": "Chave R2 inválida."
            }), 500

        if not r2.exists(key):
            return jsonify({
                "success": False,
                "message": "Arquivo não encontrado no Cloudflare R2.",
                "key": key
            }), 404

        extensao = Path(key).suffix.lower()

        if extensao in {".xlsx", ".xlsm"}:

            data = r2.read_object(key)

            nome_arquivo = (
                certificado.nome_arquivo
                or Path(key).name
                or f"Certificado-{certificado.numero_certificado}.xlsx"
            )

            pdf_data = _xlsx_to_pdf(
                data=data,
                filename=nome_arquivo
            )

            nome_pdf = (
                Path(nome_arquivo).stem
                + ".pdf"
            )

            return send_file(
                io.BytesIO(pdf_data),
                mimetype="application/pdf",
                download_name=nome_pdf,
                as_attachment=False,
            )


        # ====================================================
        # PDF → VISUALIZAÇÃO DIRETA NO NAVEGADOR
        # ====================================================
        if extensao == ".pdf":

            data = r2.read_object(key)

            return send_file(
                io.BytesIO(data),
                mimetype="application/pdf",
                download_name=(
                    certificado.nome_arquivo
                    or Path(key).name
                ),
                as_attachment=False
            )


        # ====================================================
        # FORMATO NÃO SUPORTADO
        # ====================================================
        return jsonify({
            "success": False,
            "message": (
                f"Formato de certificado não suportado para "
                f"visualização: {extensao}"
            ),
            "filename": Path(key).name
        }), 415

    except Exception as erro:

        current_app.logger.exception(
            "SIGEM CAL — Erro ao visualizar certificado"
        )

        return jsonify({
            "success": False,
            "message": (
                "Não foi possível visualizar "
                "o certificado."
            ),
            "error": str(erro)
        }), 500

# ============================================================
# GET — DOWNLOAD PDF
# ============================================================

@certificate.get("/<int:certificate_id>/download")
def baixar_certificado(certificate_id):

    certificado = (
        Certificate.query
        .options(joinedload(Certificate.device))
        .filter_by(id=certificate_id)
        .first()
    )

    if not certificado:
        return jsonify({
            "success": False,
            "message": "Certificado não encontrado."
        }), 404

    if not certificado.arquivo:
        return jsonify({
            "success": False,
            "message": "Este certificado não possui arquivo."
        }), 404

    try:

        r2 = get_r2()

        key = normalizar_r2_key(
            certificado.arquivo
        )

        if not key:
            return jsonify({
                "success": False,
                "message": "Chave R2 inválida."
            }), 500

        filename = (
            certificado.nome_arquivo
            or Path(key).name
        )

        extension = Path(key).suffix.lower()

        content_type = {
            ".pdf": "application/pdf",
            ".xlsx": (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            ".xls": "application/vnd.ms-excel",
            ".xlsm": (
                "application/vnd.ms-excel.sheet.macroEnabled.12"
            ),
        }.get(
            extension,
            "application/octet-stream"
        )

        url = r2.generate_download_url(
            key,
            expires=900,
            response_content_disposition=(
                f'attachment; filename="{filename}"'
            ),
            response_content_type=content_type,
        )

        return redirect(url, code=302)

    except Exception as erro:

        current_app.logger.exception(
            "SIGEM CAL — Erro no download R2"
        )

        return jsonify({
            "success": False,
            "message": "Erro ao gerar download do certificado.",
            "error": str(erro)
        }), 500

# ============================================================
# DELETE
# ============================================================

@certificate.delete(
    "/<int:certificate_id>"
)
def excluir_certificado(
    certificate_id
):

    try:

        certificado = (
            Certificate.query
            .filter_by(
                id=certificate_id
            )
            .first()
        )

        if not certificado:

            return jsonify({

                "success": False,

                "message":
                    "Certificado não encontrado."

            }), 404

        caminho_arquivo = (
            certificado.arquivo
        )

        db.session.delete(
            certificado
        )

        db.session.commit()

        if caminho_arquivo:

            try:

                excluir_certificado_arquivo(
                    caminho_arquivo
                )

            except Exception as erro:

                print(
                    "SIGEM CAL — "
                    "Erro ao remover PDF:",
                    erro
                )

        return jsonify({

            "success": True,

            "message":
                "Certificado excluído com sucesso."

        })

    except Exception as erro:

        db.session.rollback()

        print(
            "SIGEM CAL — Erro ao excluir:",
            erro
        )

        return jsonify({

            "success": False,

            "message":
                "Não foi possível excluir o certificado."

        }), 500