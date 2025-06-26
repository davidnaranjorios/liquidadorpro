# ipc.py
# Módulo para el manejo del IPC y la actualización de sanciones

import pandas as pd

# Cargar archivo de IPC (debe cargarse desde la clase principal)
df_ipc = None

def cargar_ipc(ruta_csv):
    global df_ipc
    df_ipc = pd.read_csv(ruta_csv, encoding='latin1', sep=';')
    df_ipc.columns = ['año', 'tasa']
    df_ipc['tasa'] = df_ipc['tasa'].str.replace('%', '').str.replace(',', '.').astype(float) / 100

def obtener_incremento_ipc_compuesto(año_inicio, año_objetivo):
    """
    Calcula el incremento acumulado por IPC usando capitalización compuesta
    desde `año_inicio + 1` hasta `año_objetivo`, ambos inclusive.

    Nota: No se aplica IPC en el mismo año en que se hace el pago.
    """
    global df_ipc
    if df_ipc is None:
        raise ValueError("El IPC no ha sido cargado. Usa cargar_ipc().")

    if año_objetivo <= año_inicio:
        return 0.0

    df_rango = df_ipc[(df_ipc['año'] > año_inicio) & (df_ipc['año'] <= año_objetivo)]
    acumulado = 1.0
    for tasa in df_rango['tasa']:
        acumulado *= (1 + tasa)

    incremento = acumulado - 1
    return round(incremento, 6)
