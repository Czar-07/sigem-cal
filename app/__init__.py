import os
from flask import Flask, render_template, send_file, jsonify, request, send_from_directory

from config import Config

from app.database.database import db

from app.api.devices import devices
from app.api.dashboard import dashboard
from app.api.calibrations import calibrations
from app.api.reports import reports
from app.api.sync import sync
from app.api.certificates import certificate
from app.api.settings import settings
from app.api.notifications import notifications

from app.utils.qrcode_generator import gerar_qrcode_dispositivo
from app.auth import auth
from app.middleware.auth import register_auth_middleware
from app.middleware.security import register_security_headers

# ============================================================
# STATUS COLORIDO
# ============================================================

def status_colorido(status):

    status_normalizado = str(
        status or ""
    ).strip().lower()


    # --------------------------------------------------------
    # CALIBRADO
    # --------------------------------------------------------

    if status_normalizado == "calibrado":

        return """
        <span class="status-badge status-calibrado">
            <i class="bi bi-check-circle-fill"></i>
            Calibrado
        </span>
        """


    # --------------------------------------------------------
    # DESENVOLVIMENTO
    # --------------------------------------------------------

    if status_normalizado == "desenvolvimento":

        return """
        <span class="status-badge status-desenvolvimento">
            <i class="bi bi-hourglass-split"></i>
            Desenvolvimento
        </span>
        """


    # --------------------------------------------------------
    # ATRASADO
    # --------------------------------------------------------

    if status_normalizado == "atrasado":

        return """
        <span class="status-badge status-atrasado">
            <i class="bi bi-exclamation-triangle-fill"></i>
            Atrasado
        </span>
        """


    # --------------------------------------------------------
    # INATIVO
    # --------------------------------------------------------

    if status_normalizado == "inativo":

        return """
        <span class="status-badge status-inativo">
            <i class="bi bi-slash-circle-fill"></i>
            Inativo
        </span>
        """


    # --------------------------------------------------------
    # DESCONHECIDO
    # --------------------------------------------------------

    return """
    <span class="status-badge status-desconhecido">
        Não informado
    </span>
    """


# ============================================================
# APPLICATION FACTORY
# ============================================================

def create_app():

    app = Flask(__name__)


    # ========================================================
    # CONFIGURAÇÃO
    # ========================================================

    app.config.from_object(Config)
    Config.validate()
    app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH


    # ========================================================
    # BANCO DE DADOS
    # ========================================================

    db.init_app(app)

    # Importa todos os modelos antes de criar tabelas novas.
    from app.models import device as device_model, certificate as certificate_model, calibration as calibration_model, setting as setting_model, sync_log as sync_log_model, notification as notification_model, user as user_model  # noqa: F401
    with app.app_context():
        db.create_all()
        from app.database.certificate_migration import migrate_certificates
        migrate_certificates()
        from app.database.security_migration import migrate_sensitive_settings
        migrate_sensitive_settings()


    # ========================================================
    # BLUEPRINTS
    # ========================================================

    app.register_blueprint(devices)

    app.register_blueprint(dashboard)

    app.register_blueprint(calibrations)

    app.register_blueprint(reports)

    app.register_blueprint(sync)

    app.register_blueprint(certificate)

    app.register_blueprint(settings)
    app.register_blueprint(notifications)

    app.register_blueprint(auth)

    register_auth_middleware(app)
    register_security_headers(app)

    # ========================================================
    # JINJA
    # ========================================================

    app.jinja_env.globals.update(
        status_colorido=status_colorido
    )


    # ========================================================
    # DASHBOARD
    # ========================================================

    @app.route("/")
    @app.route("/dashboard")
    def home():

        return render_template(
            "admin/dashboard.html"
        )


    # ========================================================
    # PÁGINA DO DISPOSITIVO
    # ========================================================

    @app.route("/device/<path:numero>/qrcode.png")
    def device_qr_code(numero):

        """Gera/atualiza e entrega o QR Code do dispositivo."""

        from app.models.device import Device
        dispositivo = Device.query.filter_by(numero=numero).first()

        if not dispositivo:
            return ("Dispositivo não encontrado", 404)

        qr = gerar_qrcode_dispositivo(dispositivo.numero)
        caminho = os.path.join(
            app.static_folder,
            "qrcodes",
            qr["arquivo"]
        )

        return send_file(
            caminho,
            mimetype="image/png",
            max_age=86400
        )


    @app.route(
        "/device/<path:numero>"
    )
    def device_page(numero):

        from app.models.device import Device

        dispositivo = Device.query.filter_by(
            numero=numero
        ).first()


        if not dispositivo:

            return (
                "Dispositivo não encontrado",
                404
            )


        qr_code = gerar_qrcode_dispositivo(
            dispositivo.numero
        )


        return render_template(
            "public/device.html",
            numeroDispositivo=dispositivo.numero,
            qr_code=qr_code
        )


    # ========================================================
    # CERTIFICADOS PÚBLICOS DO DISPOSITIVO
    # ========================================================

    @app.route("/api/public/devices/<path:numero>/certificates")
    def public_device_certificates(numero):
        from app.models.device import Device
        from app.models.certificate import Certificate

        dispositivo = Device.query.filter_by(numero=numero).first()
        if not dispositivo:
            return jsonify({"success": False, "message": "Dispositivo não encontrado."}), 404

        certificados = (
            Certificate.query
            .filter(Certificate.device_id == dispositivo.id)
            .order_by(Certificate.ano.desc(), Certificate.id.desc())
            .all()
        )

        hoje = __import__("datetime").date.today()
        resultado = []
        for cert in certificados:
            validade = cert.data_validade
            if validade:
                situacao = "Vencido" if validade < hoje else ("Vence em breve" if (validade - hoje).days <= 30 else "Válido")
            else:
                situacao = "Sem validade informada"
            resultado.append({
                "id": cert.id,
                "ano": cert.ano,
                "numero_certificado": cert.numero_certificado,
                "nome_arquivo": cert.nome_arquivo,
                "data_emissao": cert.data_emissao.isoformat() if cert.data_emissao else None,
                "data_validade": validade.isoformat() if validade else None,
                "laboratorio": cert.laboratorio,
                "resultado": cert.resultado,
                "situacao": situacao,
                "view_url": f"/device/{dispositivo.numero}/certificate/{cert.id}/view",
                "download_url": f"/device/{dispositivo.numero}/certificate/{cert.id}/download",
            })

        return jsonify({
            "success": True,
            "device": {"id": dispositivo.id, "numero": dispositivo.numero, "descricao": dispositivo.descricao},
            "total": len(resultado),
            "certificados": resultado,
        })


    @app.route("/device/<path:numero>/certificate/<int:certificate_id>/view")
    def public_certificate_view(numero, certificate_id):
        from app.models.device import Device
        from app.models.certificate import Certificate
        from app.services.certificate_sync_service import read_source_member
        from app.api.certificates import _xlsx_preview
        from pathlib import Path
        import io

        dispositivo = Device.query.filter_by(numero=numero).first()
        cert = Certificate.query.filter_by(id=certificate_id).first()
        if not dispositivo or not cert or cert.device_id != dispositivo.id:
            return ("Certificado não encontrado.", 404)
        if not cert.arquivo:
            return ("Este certificado não possui arquivo.", 404)

        partes = cert.arquivo.replace("\\", "/").split("/")
        upload_root = Path(app.config["UPLOAD_FOLDER"]).resolve()
        arquivo_local = upload_root / Path(*partes)
        extensao = Path(partes[-1]).suffix.lower()
        if arquivo_local.is_file():
            if extensao == ".pdf":
                return send_from_directory(str(arquivo_local.parent), arquivo_local.name, mimetype="application/pdf", as_attachment=False)
            if extensao == ".xlsx":
                html = _xlsx_preview(arquivo_local.read_bytes(), cert.nome_arquivo or arquivo_local.name)
                return html, 200, {"Content-Type": "text/html; charset=utf-8"}

        recuperado = read_source_member(cert.source_path, cert.source_key)
        if recuperado:
            data, source_ext = recuperado
            if source_ext == ".pdf":
                from flask import send_file
                return send_file(io.BytesIO(data), mimetype="application/pdf", as_attachment=False, download_name=cert.nome_arquivo or partes[-1])
            if source_ext == ".xlsx":
                html = _xlsx_preview(data, cert.nome_arquivo or partes[-1])
                return html, 200, {"Content-Type": "text/html; charset=utf-8"}
        return ("Arquivo do certificado não encontrado.", 404)


    @app.route("/device/<path:numero>/certificate/<int:certificate_id>/download")
    def public_certificate_download(numero, certificate_id):
        from app.models.device import Device
        from app.models.certificate import Certificate
        from app.services.certificate_sync_service import read_source_member
        from pathlib import Path
        import io

        dispositivo = Device.query.filter_by(numero=numero).first()
        cert = Certificate.query.filter_by(id=certificate_id).first()
        if not dispositivo or not cert or cert.device_id != dispositivo.id:
            return ("Certificado não encontrado.", 404)
        if not cert.arquivo:
            return ("Este certificado não possui arquivo.", 404)

        partes = cert.arquivo.replace("\\", "/").split("/")
        upload_root = Path(app.config["UPLOAD_FOLDER"]).resolve()
        arquivo_local = upload_root / Path(*partes)
        mime_map = {".pdf": "application/pdf", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}
        extensao = Path(partes[-1]).suffix.lower()
        nome = cert.nome_arquivo or partes[-1]
        if arquivo_local.is_file():
            return send_from_directory(str(arquivo_local.parent), arquivo_local.name, mimetype=mime_map.get(extensao, "application/octet-stream"), as_attachment=True, download_name=nome)

        recuperado = read_source_member(cert.source_path, cert.source_key)
        if recuperado:
            data, source_ext = recuperado
            return send_file(io.BytesIO(data), mimetype=mime_map.get(source_ext, "application/octet-stream"), as_attachment=True, download_name=nome)
        return ("Arquivo do certificado não encontrado.", 404)


    # ========================================================
    # INSTRUMENTOS
    # ========================================================

    @app.route(
        "/instruments"
    )
    def instruments_page():

        return render_template(
            "admin/instruments.html"
        )


    # ========================================================
    # CALIBRAÇÕES
    # ========================================================

    @app.route(
        "/calibrations",
        methods=["GET"]
    )
    def calibrations_page():

        return render_template(
            "admin/calibrations.html"
        )

    @app.route("/reports")
    def reports_page():

        return render_template(
            "admin/reports.html"
        )

    @app.route("/certificates")
    def certificates_page():
    
        return render_template(
            "admin/certificates.html"
        )

    @app.route("/notifications")
    def notifications_page():
        return render_template("admin/notifications.html")


    @app.route("/settings")
    def settings_page():

        return render_template(
            "admin/settings.html"
        )


    return app