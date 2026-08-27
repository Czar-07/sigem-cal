from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text, inspect


BASE_DIR = Path(__file__).resolve().parents[1]

SQLITE_URL = f"sqlite:///{(BASE_DIR / 'instance' / 'sigem.db').as_posix()}"

POSTGRES_URL = os.getenv("DATABASE_URL", "").strip()


if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = "postgresql://" + POSTGRES_URL[len("postgres://"):]


if not POSTGRES_URL:
    print("ERRO: DATABASE_URL não foi configurada.")
    print()
    print("No PowerShell:")
    print('$env:DATABASE_URL="postgresql://..."')
    sys.exit(1)


print("=" * 70)
print("SIGEM-CAL — MIGRAÇÃO SQLite → PostgreSQL")
print("=" * 70)
print()

print("SQLite:")
print(SQLITE_URL)

print()
print("PostgreSQL:")
print(POSTGRES_URL.split("@")[0] + "@***")

print()


sqlite_engine = create_engine(
    SQLITE_URL,
    future=True
)

postgres_engine = create_engine(
    POSTGRES_URL,
    future=True
)


# ============================================================
# TESTE SQLITE
# ============================================================

print("Testando SQLite...")

with sqlite_engine.connect() as conn:
    sqlite_tables = inspect(sqlite_engine).get_table_names()

print("Tabelas encontradas no SQLite:")

for table in sqlite_tables:
    print(f"  ✓ {table}")

print()


# ============================================================
# TESTE POSTGRESQL
# ============================================================

print("Testando PostgreSQL...")

with postgres_engine.connect() as conn:
    result = conn.execute(
        text("SELECT version()")
    )
    version = result.scalar()

print("PostgreSQL conectado:")
print(version)

print()


# ============================================================
# CRIAR TABELAS PELOS MODELS DO FLASK
# ============================================================

print("Carregando aplicação...")

sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.database.database import db


# Forçamos temporariamente a aplicação a utilizar PostgreSQL
app = create_app()

app.config["SQLALCHEMY_DATABASE_URI"] = POSTGRES_URL

db.session.remove()
db.engine.dispose()

# Criamos um engine PostgreSQL diretamente para evitar
# depender da configuração carregada anteriormente.
postgres_engine = create_engine(
    POSTGRES_URL,
    future=True
)

print("Criando estrutura do PostgreSQL...")

with app.app_context():

    # Os models já foram importados pela aplicação.
    db.metadata.create_all(postgres_engine)

print("✓ Estrutura criada.")

print()


# ============================================================
# IMPORTAÇÃO
# ============================================================

def get_rows(engine, table_name):

    with engine.connect() as conn:
        result = conn.execute(
            text(f'SELECT * FROM "{table_name}"')
        )

        columns = list(result.keys())
        rows = result.fetchall()

    return columns, rows


def insert_rows(
    engine,
    table_name,
    columns,
    rows
):

    if not rows:
        return 0

    quoted_columns = ", ".join(
        f'"{column}"'
        for column in columns
    )

    parameters = ", ".join(
        f":p{i}"
        for i in range(len(columns))
    )

    sql = text(
        f'''
        INSERT INTO "{table_name}"
        ({quoted_columns})
        VALUES ({parameters})
        '''
    )

    with engine.begin() as conn:

        for row in rows:

            params = {
                f"p{i}": value
                for i, value in enumerate(row)
            }

            conn.execute(
                sql,
                params
            )

    return len(rows)


# ============================================================
# ORDEM IMPORTANTE
# ============================================================

tables_order = [
    "devices",
    "certificates",
    "notifications",
    "settings",
    "sync_log",
]


print("=" * 70)
print("IMPORTANDO DADOS")
print("=" * 70)
print()


for table in tables_order:

    if table not in sqlite_tables:
        print(f"⚠ Tabela não encontrada: {table}")
        continue

    print(f"Importando: {table}")

    columns, rows = get_rows(
        sqlite_engine,
        table
    )

    print(f"  Registros SQLite: {len(rows)}")

    if not rows:
        print("  ✓ Nenhum registro.")
        print()
        continue

    imported = insert_rows(
        postgres_engine,
        table,
        columns,
        rows
    )

    print(
        f"  ✓ Importados: {imported}"
    )

    print()


# ============================================================
# AJUSTAR SEQUENCES DO POSTGRESQL
# ============================================================

print("=" * 70)
print("AJUSTANDO SEQUENCES")
print("=" * 70)
print()


sequence_tables = [
    "devices",
    "certificates",
    "notifications",
    "settings",
    "sync_log",
]


with postgres_engine.begin() as conn:

    for table in sequence_tables:

        try:

            conn.execute(
                text(
                    f'''
                    SELECT setval(
                        pg_get_serial_sequence(
                            '"{table}"',
                            'id'
                        ),
                        COALESCE(
                            (SELECT MAX(id) FROM "{table}"),
                            1
                        ),
                        true
                    )
                    '''
                )
            )

            print(
                f"✓ Sequence ajustada: {table}"
            )

        except Exception as exc:

            print(
                f"⚠ Não foi possível ajustar {table}: {exc}"
            )


# ============================================================
# CONFERÊNCIA
# ============================================================

print()
print("=" * 70)
print("CONFERÊNCIA")
print("=" * 70)
print()


for table in tables_order:

    if table not in sqlite_tables:
        continue

    with sqlite_engine.connect() as conn:

        sqlite_count = conn.execute(
            text(
                f'SELECT COUNT(*) FROM "{table}"'
            )
        ).scalar()

    with postgres_engine.connect() as conn:

        postgres_count = conn.execute(
            text(
                f'SELECT COUNT(*) FROM "{table}"'
            )
        ).scalar()

    status = (
        "✓ OK"
        if sqlite_count == postgres_count
        else "✗ DIFERENTE"
    )

    print(
        f"{table:20} "
        f"SQLite={sqlite_count:<8} "
        f"PostgreSQL={postgres_count:<8} "
        f"{status}"
    )


print()
print("=" * 70)
print("MIGRAÇÃO FINALIZADA")
print("=" * 70)