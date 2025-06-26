# tasas.py
# Módulo para el manejo de tasas según la normativa DIAN

import pandas as pd
from datetime import datetime

# Cargar archivo de tasas (debe cargarse desde la clase principal)
df_tasas = None

def cargar_tasas(ruta_csv):
    global df_tasas
    df_tasas = pd.read_csv(ruta_csv, sep=';', dayfirst=True)
    df_tasas.columns = ['fecha_inicio', 'fecha_fin', 'tasa']
    df_tasas['fecha_inicio'] = pd.to_datetime(df_tasas['fecha_inicio'], dayfirst=True)
    df_tasas['fecha_fin'] = pd.to_datetime(df_tasas['fecha_fin'], dayfirst=True)
    df_tasas['tasa'] = df_tasas['tasa'].str.replace('%', '').str.replace(',', '.').astype(float) / 100


def obtener_tasa_base(fecha_objetivo):
    """
    Busca la tasa vigente para una fecha dada según el archivo de tasas DIAN.
    """
    global df_tasas
    if df_tasas is None:
        raise ValueError("Las tasas no han sido cargadas. Usa cargar_tasas().")

    fila = df_tasas[
        (df_tasas['fecha_inicio'] <= fecha_objetivo) &
        (df_tasas['fecha_fin'] >= fecha_objetivo)
    ]
    if not fila.empty:
        return fila.iloc[0]['tasa']
    return None


def calcular_tasa(fecha_str, tipo_tasa):
    """
    Calcula la tasa de acuerdo con el tipo de norma aplicada.

    Tipos soportados:
    - TASA DIAN
    - ART. 91 LEY 2277: Tasa DIAN * 0.5
    - ART 45 LEY 2155: ((Tasa DIAN + 0.02) / 1.5) * 0.2
    - ART 48 LEY 2155: (Tasa DIAN + 0.02) / 1.5
    - ART 120 LEY 2010: ((Tasa DIAN + 0.02) / 1.5) + 0.02
    """
    if tipo_tasa == "":
        return ""

    try:
        fecha = datetime.strptime(fecha_str, '%d/%m/%Y')
    except ValueError:
        return "Fecha inválida"

    tasa_base = obtener_tasa_base(fecha)
    if tasa_base is None:
        return "Tasa no encontrada"

    if tipo_tasa == "TASA DIAN":
        tasa = tasa_base
    elif tipo_tasa == "ART. 91 LEY 2277":
        tasa = tasa_base * 0.5
    elif tipo_tasa == "ART 45 LEY 2155":
        tasa = ((tasa_base + 0.02) / 1.5) * 0.2
    elif tipo_tasa == "ART 48 LEY 2155":
        tasa = (tasa_base + 0.02) / 1.5
    elif tipo_tasa == "ART 120 LEY 2010":
        tasa = ((tasa_base + 0.02) / 1.5) + 0.02
    else:
        return "Tipo de tasa no reconocido"

    return round(tasa, 4)
