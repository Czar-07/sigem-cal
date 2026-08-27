from pathlib import Path
import re
import pandas as pd

SUPPORTED_EXTENSIONS = {".xlsx", ".xlsm", ".xls"}

def validar_caminho_excel(caminho: str | Path) -> Path:
    path = Path(caminho).expanduser().resolve()
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Formato de Excel não suportado: {path.suffix}")
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo Excel não encontrado: {path}")
    return path

def carregar_planilha(caminho: str | Path, header: int = 1) -> pd.DataFrame:
    path = validar_caminho_excel(caminho)
    df = pd.read_excel(path, header=header)
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .map(lambda x: re.sub(r"\s+", " ", x))
    )
    return df

def obter_info_excel(caminho: str | Path) -> dict:
    path = validar_caminho_excel(caminho)
    stat = path.stat()
    return {
        "path": str(path),
        "name": path.name,
        "size": stat.st_size,
        "modified_at": stat.st_mtime,
    }
