"""Watcher do Excel e sincronização do SIGEM CAL."""
from __future__ import annotations

import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.services.calibration_service import carregar_planilha
from app.services.notification_service import importar
from app.services.sync_service import incrementar_versao
from app.services.notification_service import verificar_alertas_e_enviar


class ExcelSyncService:
    """Coordena uma sincronização por vez."""

    def __init__(self, flask_app, excel_path: str | Path):
        self.app = flask_app
        self.excel_path = Path(excel_path).resolve()
        self._lock = threading.Lock()

    def sincronizar(self):
        if not self._lock.acquire(blocking=False):
            print("[EXCEL] Sincronização já está em andamento.")
            return None

        try:
            if not self.excel_path.exists():
                print(f"[EXCEL] Arquivo não encontrado: {self.excel_path}")
                return None

            print(f"[EXCEL] Lendo: {self.excel_path}")
            df = carregar_planilha(str(self.excel_path))
            resultado = importar(df) or {"inseridos": 0, "atualizados": 0}

            inseridos = resultado.get("inseridos", 0)
            atualizados = resultado.get("atualizados", 0)

            if inseridos or atualizados:
                nova_versao = incrementar_versao(source="excel")
                print(
                    f"[EXCEL] Concluído: {inseridos} inseridos, "
                    f"{atualizados} atualizados, versão {nova_versao}."
                )
            else:
                print("[EXCEL] Nenhuma alteração nos dados.")

            return resultado
        except Exception as exc:
            print(f"[EXCEL] Erro na sincronização: {exc}")
            return None
        finally:
            self._lock.release()


class _ExcelEventHandler(FileSystemEventHandler):
    def __init__(self, watcher: "ExcelWatcher"):
        self.watcher = watcher

    def _process(self, path):
        candidate = Path(path).resolve()
        if candidate != self.watcher.excel_path:
            return
        try:
            mtime = candidate.stat().st_mtime_ns
        except FileNotFoundError:
            return
        if mtime == self.watcher.last_mtime:
            return

        self.watcher.last_mtime = mtime
        time.sleep(self.watcher.save_delay)
        with self.watcher.app.app_context():
            self.watcher.sync.sincronizar()

    def on_modified(self, event):
        if not event.is_directory:
            self._process(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self._process(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self._process(event.dest_path)


class ExcelWatcher:
    """Monitora a planilha operacional sem misturar isso ao entrypoint Flask."""

    def __init__(self, flask_app, excel_path, save_delay: float = 2.0):
        self.app = flask_app
        self.excel_path = Path(excel_path).resolve()
        self.save_delay = save_delay
        self.last_mtime = None
        self.observer = None
        self.sync = ExcelSyncService(flask_app, self.excel_path)

    def start(self):
        if not self.excel_path.exists():
            print(f"[EXCEL] Arquivo não encontrado: {self.excel_path}")
            return None

        self.last_mtime = self.excel_path.stat().st_mtime_ns

        with self.app.app_context():
            self.sync.sincronizar()
            try:
                verificar_alertas_e_enviar()
            except Exception as exc:
                print(f"[NOTIFICAÇÕES] Verificação inicial falhou: {exc}")

        self.observer = Observer()
        self.observer.daemon = True
        self.observer.schedule(
            _ExcelEventHandler(self),
            str(self.excel_path.parent),
            recursive=False,
        )
        self.observer.start()
        print(f"[EXCEL] Watcher ativo: {self.excel_path}")
        return self.observer

    def stop(self):
        if not self.observer:
            return
        self.observer.stop()
        self.observer.join(timeout=5)
        self.observer = None
        print("[EXCEL] Watcher encerrado.")
