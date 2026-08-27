from sqlalchemy import inspect, text
from app.database.database import db


def ensure_device_columns():
    inspector = inspect(db.engine)
    if "devices" not in inspector.get_table_names():
        return
    existing = {c["name"] for c in inspector.get_columns("devices")}
    additions = {
        "observacoes": "TEXT",
        "certificado2024": "VARCHAR(255)",
    }
    with db.engine.begin() as conn:
        for name, sql_type in additions.items():
            if name not in existing:
                conn.execute(text(f'ALTER TABLE devices ADD COLUMN "{name}" {sql_type}'))
