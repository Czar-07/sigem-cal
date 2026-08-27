"""Entrypoint do SIGEM CAL."""

from __future__ import annotations

import os

from app import create_app
from app.runtime import ExcelWatcher, NotificationMonitor


# ============================================================
# APLICAÇÃO WSGI
# ============================================================

application = create_app()


# ============================================================
# DESENVOLVIMENTO LOCAL
# ============================================================

def main():
    excel_watcher = ExcelWatcher(
        application,
        application.config["EXCEL_PATH"]
    )

    notification_monitor = NotificationMonitor(application)

    print("=" * 56)
    print("SIGEM CAL — Sistema Inteligente de Gestão")
    print("=" * 56)

    excel_watcher.start()
    notification_monitor.start()

    try:
        application.run(
            host=os.getenv("FLASK_HOST", "127.0.0.1"),
            port=int(os.getenv("FLASK_PORT", "5000")),
            debug=application.config.get("DEBUG", False),
            use_reloader=False,
        )

    except KeyboardInterrupt:
        print("\n[SIGEM] Encerramento solicitado.")

    finally:
        notification_monitor.stop()
        excel_watcher.stop()
        print("[SIGEM] Encerrado.")


if __name__ == "__main__":
    main()