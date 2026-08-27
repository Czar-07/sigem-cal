import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

_scheduler = None


def iniciar_scheduler(app):
    global _scheduler
    enabled = os.getenv("NOTIFICATION_SCHEDULER_ENABLED", "true").lower() in {"1", "true", "yes", "sim", "on"}
    if not enabled or _scheduler:
        return
    # Evita duplicidade do reloader do Flask em desenvolvimento.
    if app.debug and os.getenv("WERKZEUG_RUN_MAIN") != "true":
        return

    hour = int(os.getenv("NOTIFICATION_SCHEDULER_HOUR", "7"))
    minute = int(os.getenv("NOTIFICATION_SCHEDULER_MINUTE", "0"))
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo", daemon=True)

    def job():
        with app.app_context():
            from app.services.notification_service import verificar_e_enviar_alertas
            verificar_e_enviar_alertas()

    scheduler.add_job(job, CronTrigger(hour=hour, minute=minute), id="sigem_cal_notification_check", replace_existing=True, max_instances=1, coalesce=True)
    scheduler.start()
    _scheduler = scheduler
