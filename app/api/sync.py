from pathlib import Path
from datetime import datetime
import shutil
from flask import Blueprint, jsonify, current_app, request
from werkzeug.utils import secure_filename

from app.services.sync_service import obter_estado, incrementar_versao
from app.services.calibration_service import carregar_planilha
from app.services.notification_service import importar, verificar_alertas_e_enviar
from app.services.excel_service import obter_info_excel

sync = Blueprint("sync", __name__, url_prefix="/api/sync")
ALLOWED = {".xlsx"}


@sync.route("/version", methods=["GET"])
def version():
    try:
        return jsonify({"success": True, **obter_estado()})
    except Exception:
        return jsonify({"success": False, "message": "Erro ao consultar a sincronização."}), 500


def _executar_sync(path, source):
    info = obter_info_excel(path)
    df = carregar_planilha(path)
    resultado = importar(df)
    versao = incrementar_versao(source=source)
    alertas = verificar_alertas_e_enviar()
    return {
        "success": True,
        "version": versao,
        "file": info,
        "resultado": resultado,
        "alertas": alertas,
        "sync": obter_estado(),
    }


@sync.route("/run", methods=["POST"])
def run_sync():
    try:
        path = current_app.config["EXCEL_PATH"]
        return jsonify(_executar_sync(path, "excel"))
    except Exception as erro:
        return jsonify({"success": False, "message": str(erro)}), 500


@sync.route("/upload", methods=["POST"])
def upload_excel():
    try:
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Selecione um arquivo Excel."}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"success": False, "message": "O arquivo selecionado é inválido."}), 400

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED:
            return jsonify({"success": False, "message": "Formato inválido. Use um arquivo .xlsx."}), 400

        safe_name = secure_filename(file.filename) or "controle_calibracao.xlsx"
        target = Path(current_app.config["EXCEL_PATH"]).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + ".uploading")

        file.save(temp)
        # Valida antes de substituir o Excel ativo.
        df = carregar_planilha(temp)
        if df.empty:
            raise ValueError("A planilha não possui registros para importação.")

        if target.exists():
            backup_dir = target.parent / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_name = f"{target.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{target.suffix}"
            shutil.copy2(target, backup_dir / backup_name)
        temp.replace(target)
        resultado = importar(df)
        versao = incrementar_versao(source="manual_upload")
        alertas = verificar_alertas_e_enviar()

        return jsonify({
            "success": True,
            "message": f"Excel '{safe_name}' importado com sucesso.",
            "version": versao,
            "file": obter_info_excel(target),
            "resultado": resultado,
            "alertas": alertas,
            "sync": obter_estado(),
        })
    except Exception as erro:
        try:
            if 'temp' in locals() and temp.exists():
                temp.unlink()
        except Exception:
            pass
        return jsonify({"success": False, "message": str(erro)}), 500
