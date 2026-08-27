"""Monitor periódico de alertas e notificações."""
from __future__ import annotations

import threading

from app.models.setting import Setting
from app.services.notification_service import verificar_alertas_e_enviar


class NotificationMonitor:
    def __init__(self, flask_app):
        self.app = flask_app
        self.stop_event = threading.Event()
        self.thread = None

    def _interval_seconds(self) -> int:
        try:
            with self.app.app_context():
                setting = Setting.query.filter_by(
                    chave="notifications.check_interval_minutes",
                    ativo=True,
                ).first()
                minutes = int(setting.get_value() if setting else 30)
                return max(5, minutes) * 60
        except Exception:
            return 30 * 60

    def _worker(self):
        while not self.stop_event.is_set():
            try:
                with self.app.app_context():
                    result = verificar_alertas_e_enviar()
                    if result.get("sent") or result.get("created"):
                        print(f"[NOTIFICAÇÕES] {result}")
            except Exception as exc:
                print(f"[NOTIFICAÇÕES] Erro: {exc}")

            self.stop_event.wait(self._interval_seconds())

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._worker,
            name="sigem-notification-monitor",
            daemon=True,
        )
        self.thread.start()
        print("[NOTIFICAÇÕES] Monitor automático iniciado.")

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3)
        self.thread = None
