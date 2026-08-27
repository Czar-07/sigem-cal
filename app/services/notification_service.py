# ============================================================
# SIGEM CAL — IMPORTAÇÃO DO EXCEL + NOTIFICAÇÕES
# ============================================================
import os
import ssl
import smtplib
from datetime import date, datetime
from email.message import EmailMessage
from html import escape

import pandas as pd

from app.models.device import Device
from app.models.notification import Notification
from app.models.setting import Setting
from app.database.database import db


def converter_data(valor):
    if pd.isna(valor):
        return None
    try:
        return pd.to_datetime(valor).date()
    except Exception:
        return None


def converter_texto(valor):
    if pd.isna(valor):
        return None
    texto = str(valor).strip()
    return None if texto.lower() in {"nan", "none", "nat"} else texto


def importar(df):
    df = df.dropna(how="all")
    inseridos = atualizados = ignorados = 0

    for _, row in df.iterrows():
        numero = converter_texto(row.get("Nº DISPOSITIVO (DC)"))
        if not numero:
            ignorados += 1
            continue

        dados = {
            "descricao": converter_texto(row.get("DESCRIÇÃO")),
            "cliente": converter_texto(row.get("CLIENTE")),
            "part_number": converter_texto(row.get("PART NUMBER")),
            "ultima_calibracao": converter_data(row.get("ÚLTIMA CALIBRAÇÃO")),
            "proxima_calibracao": converter_data(row.get("PRÓXIMA CALIBRAÇÃO")),
            "certificado2025": converter_texto(row.get("CERTIFICADO 2025")),
            "certificado2026": converter_texto(row.get("CERTIFICADO 2026")),
            "condicao": converter_texto(row.get("CONDIÇÃO")),
            "status": converter_texto(row.get("STATUS")),
        }

        dispositivo = Device.query.filter_by(numero=numero).first()
        if dispositivo is None:
            db.session.add(Device(numero=numero, **dados))
            inseridos += 1
            continue

        alterado = False
        for campo, novo_valor in dados.items():
            if getattr(dispositivo, campo) != novo_valor:
                setattr(dispositivo, campo, novo_valor)
                alterado = True
        if alterado:
            atualizados += 1

    db.session.commit()
    return {"inseridos": inseridos, "atualizados": atualizados, "ignorados": ignorados}


def _setting(chave, default=None):
    setting = Setting.query.filter_by(chave=chave, ativo=True).first()
    return setting.get_value() if setting else default


def _smtp_config():
    recipients = _setting("notifications.recipients", "")
    recipient_list = [x.strip() for x in str(recipients or "").replace(";", ",").split(",") if x.strip()]
    return {
        "enabled": bool(_setting("notifications.email_enabled", False)),
        "host": _setting("notifications.smtp_host", os.getenv("SMTP_HOST", "")),
        "port": int(_setting("notifications.smtp_port", os.getenv("SMTP_PORT", "587")) or 587),
        "username": _setting("notifications.smtp_username", os.getenv("SMTP_USERNAME", "")),
        "password": os.getenv("SMTP_PASSWORD") or _setting("notifications.smtp_password", ""),
        "sender": _setting("notifications.smtp_sender", os.getenv("SMTP_SENDER", "")),
        "recipients": recipient_list,
        "tls": bool(_setting("notifications.smtp_tls", True)),
        "ssl": bool(_setting("notifications.smtp_ssl", False)),
    }


def _send_email(subject, html_body, text_body):
    cfg = _smtp_config()
    if not cfg["enabled"]:
        raise RuntimeError("Envio de e-mail está desativado.")
    if not cfg["host"] or not cfg["recipients"]:
        raise RuntimeError("Configure servidor SMTP e destinatários.")
    sender = cfg["sender"] or cfg["username"]
    if not sender:
        raise RuntimeError("Configure o remetente do e-mail.")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(cfg["recipients"])
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")

    if cfg["ssl"]:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=20, context=ssl.create_default_context()) as smtp:
            if cfg["username"]:
                smtp.login(cfg["username"], cfg["password"])
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as smtp:
            smtp.ehlo()
            if cfg["tls"]:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if cfg["username"]:
                smtp.login(cfg["username"], cfg["password"])
            smtp.send_message(msg)


def verificar_alertas_e_enviar():
    """Cria alertas de vencimento/atraso e envia um resumo sem duplicar eventos."""
    if not bool(_setting("notifications.enabled", True)) or not bool(_setting("notifications.calibration", True)):
        return {"success": True, "created": 0, "sent": 0, "skipped": True, "reason": "notificacoes_desativadas"}

    alert_days = max(1, int(_setting("notifications.expiration_days", _setting("calibration.alert_days", 30)) or 30))
    overdue_enabled = bool(_setting("calibration.overdue_enabled", True))
    today = date.today()
    pending = []

    for device in Device.query.all():
        due = device.proxima_calibracao
        if not due:
            continue
        days = (due - today).days
        if days < 0 and overdue_enabled:
            kind = "overdue"
            title = "Calibração vencida"
            message = f"O dispositivo {device.numero} está com a calibração vencida desde {due.strftime('%d/%m/%Y')}."
        elif 0 <= days <= alert_days:
            kind = "expiring"
            title = "Calibração próxima do vencimento"
            message = f"O dispositivo {device.numero} vence em {days} dia(s), em {due.strftime('%d/%m/%Y')}."
        else:
            continue

        fingerprint = f"{kind}:{device.id}:{due.isoformat()}"
        notification = Notification.query.filter_by(fingerprint=fingerprint).first()
        if notification:
            if notification.status == "sent":
                continue
        else:
            notification = Notification(
                device_id=device.id,
                type=kind,
                fingerprint=fingerprint,
                title=title,
                message=message,
                due_date=due,
                days_remaining=days,
                status="pending",
            )
            db.session.add(notification)
            pending.append(notification)

    db.session.commit()

    pending = [n for n in Notification.query.filter_by(status="pending").order_by(Notification.created_at.asc()).all()]
    if not pending:
        return {"success": True, "created": 0, "sent": 0, "pending": 0}

    cfg = _smtp_config()
    if not cfg["enabled"] or not cfg["recipients"] or not cfg["host"]:
        return {"success": True, "created": len(pending), "sent": 0, "pending": len(pending), "email_configured": False}

    overdue = [n for n in pending if n.type == "overdue"]
    expiring = [n for n in pending if n.type == "expiring"]

    def rows(items, overdue=False):
        if not items:
            return "<p style='color:#64748b'>Nenhum registro.</p>"
        html = ["<table style='width:100%;border-collapse:collapse;font-size:14px'>",
                "<tr><th style='text-align:left;padding:10px;border-bottom:1px solid #e2e8f0'>Dispositivo</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e2e8f0'>Cliente</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e2e8f0'>Vencimento</th>"
                "<th style='text-align:left;padding:10px;border-bottom:1px solid #e2e8f0'>Situação</th></tr>"]
        for n in items:
            d = n.device
            situation = f"{abs(n.days_remaining)} dia(s) em atraso" if overdue else f"{n.days_remaining} dia(s) restantes"
            html.append(f"<tr><td style='padding:10px;border-bottom:1px solid #f1f5f9'><b>{escape(d.numero if d else '-')}</b></td>"
                        f"<td style='padding:10px;border-bottom:1px solid #f1f5f9'>{escape(d.cliente if d and d.cliente else '-')}</td>"
                        f"<td style='padding:10px;border-bottom:1px solid #f1f5f9'>{n.due_date.strftime('%d/%m/%Y') if n.due_date else '-'}</td>"
                        f"<td style='padding:10px;border-bottom:1px solid #f1f5f9'>{escape(situation)}</td></tr>")
        html.append("</table>")
        return "".join(html)

    subject = f"SIGEM CAL | {len(overdue)} vencido(s) e {len(expiring)} próximo(s) do vencimento"
    html = f"""<html><body style='font-family:Arial,sans-serif;background:#f8fafc;padding:24px;color:#0f172a'>
    <div style='max-width:900px;margin:auto;background:white;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden'>
      <div style='padding:24px;background:#0f172a;color:white'><div style='font-size:12px;letter-spacing:.12em'>SIGEM CAL</div>
      <h1 style='margin:8px 0 0;font-size:24px'>Relatório de alertas de calibração</h1></div>
      <div style='padding:24px'><p>Monitoramento automático realizado em {today.strftime('%d/%m/%Y')}.</p>
      <h2 style='font-size:18px'>Calibrações vencidas ({len(overdue)})</h2>{rows(overdue, True)}
      <h2 style='font-size:18px;margin-top:28px'>Próximos vencimentos ({len(expiring)})</h2>{rows(expiring)}
      <p style='margin-top:28px;color:#64748b;font-size:12px'>Mensagem automática do SIGEM CAL. Consulte o sistema para detalhes e rastreabilidade.</p></div>
    </div></body></html>"""
    text = [f"SIGEM CAL — Alertas de calibração ({today.strftime('%d/%m/%Y')})", ""]
    for n in pending:
        d = n.device
        text.append(f"{n.title}: {d.numero if d else '-'} | vencimento {n.due_date.strftime('%d/%m/%Y') if n.due_date else '-'}")
    text_body = "\n".join(text)

    try:
        _send_email(subject, html, text_body)
        sent_at = datetime.utcnow()
        for n in pending:
            n.status = "sent"
            n.sent_at = sent_at
            n.recipient = ", ".join(cfg["recipients"])
            n.error = None
        db.session.commit()
        return {"success": True, "created": len(pending), "sent": len(pending), "pending": 0}
    except Exception as exc:
        for n in pending:
            n.status = "error"
            n.error = str(exc)[:1000]
        db.session.commit()
        return {"success": False, "created": len(pending), "sent": 0, "pending": len(pending), "error": str(exc)}


def testar_email():
    _send_email(
        "SIGEM CAL | Teste de configuração",
        "<html><body style='font-family:Arial'><h2>SIGEM CAL</h2><p>O envio de e-mail foi configurado e testado com sucesso.</p></body></html>",
        "SIGEM CAL — O envio de e-mail foi configurado e testado com sucesso."
    )
    return True
