from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker

from config import Config


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

SQLITE_PATH = BASE_DIR / "instance" / "sigem.db"

SQLITE_URL = f"sqlite:///{SQLITE_PATH.as_posix()}"

POSTGRES_URL = Config.SQLALCHEMY_DATABASE_URI


# Ordem importante por causa das Foreign Keys
TABLES = [
    "devices",
    "certificates",
    "notifications",
    "settings",
    "sync_log",
]


# ============================================================
# ENGINES
# ============================================================

print("=" * 70)
print("SIGEM-CAL — MIGRAÇÃO SQLITE → POSTGRESQL")
print("=" * 70)

print()
print("SQLite:")
print(SQLITE_PATH)

print()
print("PostgreSQL:")
print(POSTGRES_URL)

print()


sqlite_engine = create_engine(
    SQLITE_URL,
    future=True,
)

postgres_engine = create_engine(
    POSTGRES_URL,
    future=True,
)


# ============================================================
# TESTE DAS CONEXÕES
# ============================================================

print("Testando SQLite...")

with sqlite_engine.connect() as conn:
    result = conn.execute(text("SELECT 1")).scalar()
    print("  OK:", result)


print("Testando PostgreSQL...")

with postgres_engine.connect() as conn:
    result = conn.execute(text("SELECT 1")).scalar()
    print("  OK:", result)


# ============================================================
# METADATA
# ============================================================

sqlite_metadata = MetaData()

postgres_metadata = MetaData()


print()
print("Lendo estrutura do SQLite...")

sqlite_metadata.reflect(
    bind=sqlite_engine,
    only=TABLES,
)

print("Lendo estrutura do PostgreSQL...")

postgres_metadata.reflect(
    bind=postgres_engine,
    only=TABLES,
)


# ============================================================
# CRIAR TABELAS NO POSTGRESQL
# ============================================================

print()
print("Garantindo que as tabelas existam no PostgreSQL...")

postgres_metadata.create_all(
    postgres_engine,
)

print("OK.")


# ============================================================
# CONTAGEM ORIGINAL
# ============================================================

print()
print("Contagem no SQLite:")

source_counts = {}

with sqlite_engine.connect() as conn:

    for table_name in TABLES:

        table = sqlite_metadata.tables[table_name]

        count = conn.execute(
            text(f'SELECT COUNT(*) FROM "{table_name}"')
        ).scalar()

        source_counts[table_name] = count

        print(
            f"  {table_name}: {count}"
        )


# ============================================================
# MIGRAÇÃO
# ============================================================

print()
print("=" * 70)
print("INICIANDO MIGRAÇÃO")
print("=" * 70)


with sqlite_engine.connect() as sqlite_conn:

    with postgres_engine.begin() as postgres_conn:

        # ----------------------------------------------------
        # Desabilita temporariamente as constraints
        # ----------------------------------------------------

        print()
        print("Limpando PostgreSQL...")

        # Ordem reversa para evitar FK
        for table_name in reversed(TABLES):

            postgres_conn.execute(
                text(
                    f'TRUNCATE TABLE "{table_name}" '
                    f'RESTART IDENTITY CASCADE'
                )
            )

        print("PostgreSQL limpo.")

        # ----------------------------------------------------
        # Copiar cada tabela
        # ----------------------------------------------------

        for table_name in TABLES:

            print()
            print(f"Migrando: {table_name}")

            source_table = sqlite_metadata.tables[table_name]

            target_table = postgres_metadata.tables[table_name]

            rows = sqlite_conn.execute(
                source_table.select()
            ).mappings().all()

            print(
                f"  Registros encontrados: {len(rows)}"
            )

            if not rows:
                print("  Nenhum registro.")
                continue

            # ------------------------------------------------
            # Inserção em lotes
            # ------------------------------------------------

            batch_size = 250

            for start in range(
                0,
                len(rows),
                batch_size,
            ):

                batch = rows[
                    start:start + batch_size
                ]

                postgres_conn.execute(
                    target_table.insert(),
                    [
                        dict(row)
                        for row in batch
                    ],
                )

                print(
                    f"  Inseridos: "
                    f"{min(start + batch_size, len(rows))}"
                    f"/{len(rows)}"
                )

            print(
                f"  ✓ {table_name} concluída."
            )


# ============================================================
# CORRIGIR SEQUÊNCIAS DO POSTGRESQL
# ============================================================

print()
print("=" * 70)
print("CORRIGINDO SEQUÊNCIAS")
print("=" * 70)


with postgres_engine.begin() as conn:

    for table_name in TABLES:

        try:

            result = conn.execute(
                text(
                    f'''
                    SELECT setval(
                        pg_get_serial_sequence(
                            '"{table_name}"',
                            'id'
                        ),
                        COALESCE(
                            (
                                SELECT MAX(id)
                                FROM "{table_name}"
                            ),
                            1
                        ),
                        (
                            SELECT COUNT(*) > 0
                            FROM "{table_name}"
                        )
                    )
                    '''
                )
            )

            value = result.scalar()

            print(
                f"  {table_name}: sequência = {value}"
            )

        except Exception as e:

            print(
                f"  {table_name}: "
                f"sequência não ajustada "
                f"({e})"
            )


# ============================================================
# VERIFICAÇÃO
# ============================================================

print()
print("=" * 70)
print("VERIFICANDO MIGRAÇÃO")
print("=" * 70)


success = True

with postgres_engine.connect() as conn:

    for table_name in TABLES:

        count = conn.execute(
            text(
                f'SELECT COUNT(*) FROM "{table_name}"'
            )
        ).scalar()

        expected = source_counts[table_name]

        if count == expected:

            print(
                f"  ✓ {table_name}: "
                f"{count}/{expected}"
            )

        else:

            success = False

            print(
                f"  ✗ {table_name}: "
                f"{count}/{expected}"
            )


# ============================================================
# RESULTADO
# ============================================================

print()

if success:

    print("=" * 70)
    print("✓ MIGRAÇÃO CONCLUÍDA COM SUCESSO")
    print("=" * 70)

else:

    print("=" * 70)
    print("✗ ATENÇÃO: EXISTEM DIFERENÇAS")
    print("=" * 70)


print()
print("O SQLite original NÃO foi alterado.")
print()