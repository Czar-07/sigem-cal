from pathlib import Path
import sys

# Adiciona a raiz do projeto ao PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.services.certificate_sync_service import synchronize_certificates


def main():
    app = create_app()

    with app.app_context():
        resultado = synchronize_certificates()

        print()
        print("=" * 70)
        print("SIGEM CAL — SINCRONIZAÇÃO DE CERTIFICADOS")
        print("=" * 70)

        print(f"Sucesso:          {resultado.get('success')}")
        print(f"Fonte:             {resultado.get('source', '-')}")
        print(f"Escaneados:        {resultado.get('scanned', 0)}")
        print(f"Importados:        {resultado.get('imported', 0)}")
        print(f"Atualizados:       {resultado.get('updated', 0)}")
        print(f"Sem alteração:     {resultado.get('unchanged', 0)}")
        print(f"Ignorados:         {len(resultado.get('ignored', []))}")
        print(f"Sem dispositivo:   {len(resultado.get('unmatched', []))}")
        print(f"Erros:             {len(resultado.get('errors', []))}")

        unmatched = resultado.get("unmatched", [])

        if unmatched:
            print()
            print("-" * 70)
            print("CERTIFICADOS SEM DISPOSITIVO")
            print("-" * 70)

            for item in unmatched:
                print(
                    f"DC: {item.get('dc', '-')}"
                    f" | Normalizado: {item.get('dc_normalizado', '-')}"
                    f" | Arquivo: {item.get('arquivo', '-')}"
                )

        errors = resultado.get("errors", [])

        if errors:
            print()
            print("-" * 70)
            print("ERROS")
            print("-" * 70)

            for item in errors:
                print(
                    f"Arquivo: {item.get('arquivo', '-')}\n"
                    f"Erro:    {item.get('erro', '-')}\n"
                )

        print("=" * 70)
        print()


if __name__ == "__main__":
    main()