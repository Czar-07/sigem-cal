from sqlalchemy import inspect, text
from app.database.database import db


def migrate_certificates():
    """Non-destructive migration for certificate auto-sync fields."""
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if "certificates" not in tables:
        return
    cols = {c["name"] for c in inspector.get_columns("certificates")}
    additions = {
        "source_key": "VARCHAR(500)",
        "source_hash": "VARCHAR(64)",
        "source_type": "VARCHAR(20)",
        "source_path": "VARCHAR(500)",
    }
    for name, typ in additions.items():
        if name not in cols:
            db.session.execute(text(f"ALTER TABLE certificates ADD COLUMN {name} {typ}"))
    # Existing installations may have device_id NOT NULL. SQLite cannot alter
    # that constraint cheaply; certificates without a matching device are
    # therefore not inserted until the device exists. The normal SIGEM import
    # remains unaffected.
    # Unique source key makes repeated syncs deterministic.
    indexes = {idx.get("name") for idx in inspector.get_indexes("certificates")}
    if "uq_CERTIFICATES_FOLDER_key" not in indexes:
        db.session.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_CERTIFICATES_FOLDER_key ON certificates(source_key)"))
    db.session.commit()
