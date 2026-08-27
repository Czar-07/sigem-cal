from datetime import date, datetime
from collections import Counter
from flask import Blueprint, jsonify
from app.models.setting import Setting

from app.models.device import Device
from app.models.notification import Notification
from app.models.sync_log import SyncLog

dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/api/dashboard", methods=["GET"])
def indicadores():
    dispositivos = Device.query.all()
    total = len(dispositivos)
    today = date.today()
    effective_status = Counter()
    condition_counter = Counter(str(d.condicao or "Não informado").strip() for d in dispositivos)
    client_counter = Counter(str(d.cliente or "Não informado").strip() for d in dispositivos)
    for d in dispositivos:
        raw = str(d.status or "").strip().upper()
        if raw == "INATIVO" or str(d.condicao or "").strip().upper() == "INATIVO":
            effective_status["INATIVO"] += 1
        elif d.proxima_calibracao and d.proxima_calibracao < today:
            effective_status["ATRASADO"] += 1
        elif raw == "DESENVOLVIMENTO":
            effective_status["DESENVOLVIMENTO"] += 1
        else:
            effective_status["CALIBRADO"] += 1

    calibrado = effective_status["CALIBRADO"]
    desenvolvimento = effective_status["DESENVOLVIMENTO"]
    atrasado = effective_status["ATRASADO"]
    inativo = effective_status["INATIVO"]
    ativos = max(total - inativo, 0)
    conformidade = round((calibrado / ativos) * 100, 2) if ativos else 0

    today = date.today()
    setting = Setting.query.filter_by(chave="notifications.expiration_days", ativo=True).first()
    try:
        alert_days = max(1, int(setting.get_value())) if setting else 30
    except Exception:
        alert_days = 30
    vencendo = 0
    vencidos = 0
    sem_data = 0
    month_labels = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    monthly = [0] * 12

    for d in dispositivos:
        due = d.proxima_calibracao
        if not due:
            sem_data += 1
            continue
        days = (due - today).days
        if days < 0:
            vencidos += 1
        elif days <= alert_days:
            vencendo += 1
        if due.year == today.year:
            monthly[due.month - 1] += 1

    sync = SyncLog.query.order_by(SyncLog.id.desc()).first()
    notification_pending = Notification.query.filter(Notification.status.in_(["pending", "error"])).count()
    notification_sent = Notification.query.filter_by(status="sent").count()

    return jsonify({
        "success": True,
        "total": total,
        "ativos": ativos,
        "calibrado": calibrado,
        "desenvolvimento": desenvolvimento,
        "atrasado": atrasado,
        "inativo": inativo,
        "conformidade": conformidade,
        "vencendo": vencendo,
        "vencidos": vencidos,
        "sem_data": sem_data,
        "status": {
            "calibrado": calibrado,
            "desenvolvimento": desenvolvimento,
            "atrasado": atrasado,
            "inativo": inativo
        },
        "condicoes": {
            "labels": list(condition_counter.keys())[:10],
            "data": list(condition_counter.values())[:10]
        },
        "clientes": {
            "labels": [x[0] for x in client_counter.most_common(10)],
            "data": [x[1] for x in client_counter.most_common(10)]
        },
        "calibracoes_por_mes": {"labels": month_labels, "data": monthly},
        "certificados": {
            "2025": sum(1 for d in dispositivos if d.certificado2025),
            "2026": sum(1 for d in dispositivos if d.certificado2026),
            "sem_2026": sum(1 for d in dispositivos if not d.certificado2026)
        },
        "notificacoes": {
            "pendentes": notification_pending,
            "enviadas": notification_sent
        },
        "sync": {
            "version": sync.version if sync else 1,
            "source": sync.source if sync else "system",
            "updated_at": sync.updated_at.isoformat() if sync and sync.updated_at else None
        },
        "atualizado_em": datetime.now().isoformat()
    })
