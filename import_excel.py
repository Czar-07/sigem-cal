import os
from app import create_app
from app.services.calibration_service import carregar_planilha
from app.services.notification_service import importar

app = create_app()

with app.app_context():
    caminho = app.config["EXCEL_PATH"]
    print(f"Lendo Excel: {caminho}")
    df = carregar_planilha(caminho)
    print("\nCOLUNAS ENCONTRADAS:")
    print(df.columns.tolist())
    importar(df)
    print("Importação concluída.")
