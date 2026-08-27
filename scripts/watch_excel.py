import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app import create_app
from app.services.calibration_service import carregar_planilha
from app.services.notification_service import importar
from app.services.sync_service import incrementar_versao

app = create_app()
EXCEL_PATH = Path(app.config["EXCEL_PATH"]).resolve()
ultima_modificacao = None

def sincronizar_excel():
    print(f"\nLendo Excel: {EXCEL_PATH}")
    df = carregar_planilha(EXCEL_PATH)
    resultado = importar(df)
    if resultado.get("inseridos", 0) or resultado.get("atualizados", 0):
        nova_versao = incrementar_versao(source="excel")
        print(f"Nova versão: {nova_versao}")
    else:
        print("Nenhuma alteração nos dados.")
    return resultado

class ExcelHandler(FileSystemEventHandler):
    def processar(self, caminho):
        global ultima_modificacao
        if Path(caminho).resolve() != EXCEL_PATH:
            return
        try:
            modificacao = EXCEL_PATH.stat().st_mtime_ns
        except FileNotFoundError:
            return
        if modificacao == ultima_modificacao:
            return
        ultima_modificacao = modificacao
        print("\nALTERAÇÃO NO EXCEL DETECTADA")
        time.sleep(2)
        try:
            with app.app_context():
                sincronizar_excel()
        except Exception as erro:
            print(f"ERRO NA SINCRONIZAÇÃO: {erro}")

    def on_modified(self, event):
        if not event.is_directory:
            self.processar(event.src_path)

def main():
    global ultima_modificacao
    print("=" * 48)
    print("SIGEM CAL — EXCEL WATCHER")
    print("=" * 48)
    print(f"Arquivo monitorado: {EXCEL_PATH}")
    if not EXCEL_PATH.exists():
        print("ERRO: arquivo Excel não encontrado.")
        print("Defina EXCEL_PATH no .env com o caminho completo do arquivo.")
        sys.exit(1)

    ultima_modificacao = EXCEL_PATH.stat().st_mtime_ns
    with app.app_context():
        sincronizar_excel()

    observer = Observer()
    observer.schedule(ExcelHandler(), str(EXCEL_PATH.parent), recursive=False)
    observer.start()
    print("WATCHER ATIVO — monitorando alterações no Excel.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
