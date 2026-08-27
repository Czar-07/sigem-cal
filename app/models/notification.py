from datetime import datetime
from app.database.database import db

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=True, index=True)
    type = db.Column(db.String(40), nullable=False, index=True)
    fingerprint = db.Column(db.String(180), unique=True, nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    due_date = db.Column(db.Date, nullable=True, index=True)
    days_remaining = db.Column(db.Integer, nullable=True)
    recipient = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = db.relationship("Device", backref=db.backref("notifications", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "device_id": self.device_id,
            "device": self.device.numero if self.device else None,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "days_remaining": self.days_remaining,
            "recipient": self.recipient,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
