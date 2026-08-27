from app import create_app
from app.database.database import db

# =========================================================
# IMPORTANTE:
# Importar TODOS os modelos antes do db.create_all()
# =========================================================

from app.models.device import Device
from app.models.certificate import Certificate
from app.models.setting import Setting
from app.models.calibration import Calibration
from app.models.sync_log import SyncLog
from app.models.notification import Notification
from app.models.user import User


# =========================================================
# CRIAR APLICAÇÃO
# =========================================================

app = create_app()


# =========================================================
# CRIAR TABELAS
# =========================================================

with app.app_context():

    db.create_all()

    print("Banco criado com sucesso!")
    print("Tabela devices: OK")
    print("Tabela certificates: OK")
    print("Tabela settings: OK")
