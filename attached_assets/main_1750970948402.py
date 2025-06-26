# liquidacion.py
from datetime import datetime
import pandas as pd
import math

# --- Cargar tasas ---
df_tasas = pd.read_csv('/mnt/data/tasas_dian.csv', sep=';', dayfirst=True)
df_tasas.columns = ['fecha_inicio', 'fecha_fin', 'tasa']
df_tasas['fecha_inicio'] = pd.to_datetime(df_tasas['fecha_inicio'], dayfirst=True)
df_tasas['fecha_fin'] = pd.to_datetime(df_tasas['fecha_fin'], dayfirst=True)
df_tasas['tasa'] = df_tasas['tasa'].str.replace('%', '').str.replace(',', '.').astype(float) / 100

# --- Cargar IPC ---
df_ipc = pd.read_csv('/mnt/data/ipc.csv', encoding='latin1', sep=';')
df_ipc.columns = ['anio', 'tasa']
df_ipc['tasa'] = df_ipc['tasa'].str.replace('%', '').str.replace(',', '.').astype(float) / 100

def obtener_tasa(fecha):
    fila = df_tasas[(df_tasas['fecha_inicio'] <= fecha) & (df_tasas['fecha_fin'] >= fecha)]
    return fila.iloc[0]['tasa'] if not fila.empty else 0.0

def incremento_ipc_compuesto(anio_inicio, anio_fin):
    if anio_fin <= anio_inicio:
        return 0.0
    tasas = df_ipc[(df_ipc['anio'] > anio_inicio) & (df_ipc['anio'] <= anio_fin)]['tasa']
    acumulado = 1.0
    for tasa in tasas:
        acumulado *= (1 + tasa)
    return acumulado - 1

def redondear_mas(valor):
    return int(math.ceil(valor / 1000.0)) * 1000

class MotorLiquidacion:
    def __init__(self, data):
        self.nit = data['nit']
        self.razon_social = data['razon_social']
        self.concepto = data['concepto']
        self.anio = data['anio']
        self.periodo = data['periodo']
        self.valor_inicial = data['valor_inicial']
        self.saldo_impuesto = data['valor_inicial']
        self.saldo_sancion = data['valor_sancion']
        self.origen_sancion = data['origen_sancion']
        self.fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%d/%m/%Y')
        self.fecha_presentacion_sancion = datetime.strptime(data['fecha_presentacion_sancion'], '%d/%m/%Y')
        self.tipo_norma = data['tipo_norma']
        self.pagos = data['pagos']

        self.saldo_intereses = 0.0
        self.historial = []

    def procesar(self):
        anio_liquidacion = self.fecha_presentacion_sancion.year
        ultimo_anio_actualizado = anio_liquidacion

        for pago in self.pagos:
            fecha_pago = datetime.strptime(pago['fecha'], '%d/%m/%Y')
            monto_pago = pago['valor']
            dias_mora = max(0, (fecha_pago - self.fecha_vencimiento).days)
            tasa = obtener_tasa(fecha_pago)

            intereses = round(self.saldo_impuesto * tasa * dias_mora / 365)
            self.saldo_intereses = intereses

            # Actualizar sanción por IPC
            if fecha_pago.year > ultimo_anio_actualizado:
                if (self.origen_sancion.lower() == 'privada' and fecha_pago.year > anio_liquidacion + 1) or \
                   (self.origen_sancion.lower() == 'oficial' and fecha_pago.year > anio_liquidacion):
                    incremento = incremento_ipc_compuesto(ultimo_anio_actualizado, fecha_pago.year)
                    self.saldo_sancion = round(self.saldo_sancion * (1 + incremento))
                    ultimo_anio_actualizado = fecha_pago.year

            total_deuda = self.saldo_impuesto + self.saldo_intereses + self.saldo_sancion
            factor = round(round(monto_pago * 100 / total_deuda, 4) / 100, 4)

            vi, inte, sanc = self.saldo_impuesto, self.saldo_intereses, self.saldo_sancion
            if vi > inte:
                tipo_proporcion = "Proporción 1: Impuesto mayor" if vi > sanc else "Proporción 3: Sanción mayor"
            else:
                tipo_proporcion = "Proporción 2: Interes mayor" if inte > sanc else "Proporción 3: Sanción mayor"

            if tipo_proporcion == "Proporción 1: Impuesto mayor":
                intereses_pago = redondear_mas(factor * self.saldo_intereses)
                sancion_pago = redondear_mas(factor * self.saldo_sancion)
                impuesto_pago = monto_pago - intereses_pago - sancion_pago if monto_pago < total_deuda else vi

            elif tipo_proporcion == "Proporción 2: Interes mayor":
                impuesto_pago = redondear_mas(factor * self.saldo_impuesto)
                sancion_pago = redondear_mas(factor * self.saldo_sancion)
                intereses_pago = monto_pago - impuesto_pago - sancion_pago if monto_pago < total_deuda else inte

            else:
                impuesto_pago = redondear_mas(factor * self.saldo_impuesto)
                intereses_pago = redondear_mas(factor * self.saldo_intereses)
                sancion_pago = monto_pago - impuesto_pago - intereses_pago if monto_pago < total_deuda else sanc

            # Actualizar saldos
            self.saldo_impuesto = max(0, self.saldo_impuesto - impuesto_pago)
            self.saldo_intereses = max(0, self.saldo_intereses - intereses_pago)
            self.saldo_sancion = max(0, self.saldo_sancion - sancion_pago)

            self.historial.append({
                'fecha_pago': fecha_pago.strftime('%d/%m/%Y'),
                'tipo_proporcion': tipo_proporcion,
                'factor_proporcionalidad': factor,
                'impuesto_proporcion': impuesto_pago,
                'intereses_proporcion': intereses_pago,
                'sancion_proporcion': sancion_pago,
                'impuesto_saldo': self.saldo_impuesto,
                'intereses_saldo': self.saldo_intereses,
                'sancion_saldo': self.saldo_sancion
            })

    def resumen(self):
        return self.historial
