import pandas as pd
import numpy as np

SHEET_URL =  "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8wYLuPNQKJ_pEnDgVl7olGzwNV762wVYAhxubQwtc5xXrWOaha12Ll_YrmvTTIbLwnaZ4UrL1Ukq1/pub?gid=0&single=true&output=csv"

def limpiar_nombres_columnas(df):
    df.columns = df.columns.str.strip()
    return df

def columnas_nulas(df):
    return df.loc[:, ~df.columns.str.startswith("Unnamed")]


def limpiar_clientes(df):
    df["Cliente"] = (df["Cliente"]
                    .str.replace(" Ltda", "", regex=False)
                    .str.replace(" S.A", "", regex = False)
                    .str.replace(" SAS", "", regex = False)
                    .str.replace(" SA", "", regex = False)
                    .str.replace(" sas", "", regex = False)
                    .str.replace(" Sas", "", regex = False)
                    .str.replace(".S", "", regex = False)
                    .str.replace(".", "", regex = False)
                    .str.strip())
    
    mapa = {
            "Alpina Productos Alimenticios": "Alpina",
            "Postobon": "Postobon",
            "Pepsicola Colombia": "Pepsi",
            "Contegral": "Grupo Bios",
            "Caja de Compensacion Familiar CaFAM": "CAFAM",
            "Coca Cola bebidas de Colombia": "Coca-Cola",
            "Compañia Nacional De Levaduras Levapan": "Levapan",
            "Belleza Express": "Bivien",
            "Embotelladoras Bepensa": "Bepensa"
    }
    df["Cliente Ajustado"] = df["Cliente"].map(mapa).fillna(df["Cliente"])
    df = df[df["Cliente"] != "Totales"]
    df = df.dropna(subset=["Cliente"])

    return df

def columnas_finales(df):
    # Seleccionar solo las columnas necesarias
    df = df[["Factura", "Fecha Emision  MM DD AAAA", "Concepto", "Cliente Ajustado", "Valor bruto"]]
    
    # Renombrar para que sea más fácil de usar
    df = df.rename(columns={
        "Fecha Emision  MM DD AAAA": "Fecha",
        "Cliente Ajustado": "Cliente",
        "Valor bruto": "Valor"
    })
    
    # Convertir fecha a solo fecha sin hora
    df["Fecha"] = pd.to_datetime(df["Fecha"], format="%d/%m/%Y", errors="coerce").dt.strftime("%Y-%m-%d")
    
    return df

def data_limpia():
    df = (
        pd.read_csv(SHEET_URL, skiprows=4)
        .pipe(limpiar_nombres_columnas)
        .pipe(columnas_nulas)
        .pipe(limpiar_clientes)
        .dropna(axis=0, subset=["Factura"])
        .pipe(columnas_finales)  
        .reset_index(drop=True)
    )
    return df