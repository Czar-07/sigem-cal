import pandas as pd
import re

def carregar_planilha(caminho):
    df = pd.read_excel(caminho, header=1)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace("\n", " ", regex=False)
        .map(lambda x: re.sub(r"\s+", " ", x))
    )

    print("Colunas encontradas:")
    print(df.columns.tolist())

    return df