from flask import Blueprint, jsonify, request
from app.database.database import db
from app.models.notification import Notification
from app.services.notification_service import verificar_alertas_e_enviar, testar_email

notifications = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@notifications.get("")
def listar():
    limit = min(max(int(request.args.get("limit", 50)), 1), 200)
    items = Notification.query.order_by(Notification.created_at.desc()).limit(limit).all()
    counts = {
        "total": Notification.query.count(),
        "pendentes": Notification.query.filter(Notification.status.in_(["pending", "error"])).count(),
        "enviadas": Notification.query.filter_by(status="sent").count(),
    }
    return jsonify({"success": True, "notifications": [n.to_dict() for n in items], "counts": counts})


@notifications.post("/check")
def check():
    try:
        return jsonify(verificar_alertas_e_enviar())
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 500


@notifications.post("/test-email")
def test_email():
    try:
        testar_email()
        return jsonify({"success": True, "message": "E-mail de teste enviado com sucesso."})
    except Exception as exc:
        return jsonify({"success": False, "message": str(exc)}), 400


@notifications.post("/<int:notification_id>/retry")
def retry(notification_id):
    item = Notification.query.get_or_404(notification_id)
    item.status = "pending"
    item.error = None
    db.session.commit()
    return jsonify({"success": True, "message": "Notificação colocada novamente na fila."})
