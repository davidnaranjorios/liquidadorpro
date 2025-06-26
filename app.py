
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import pandas as pd
import math
import os

app = Flask(__name__)

# --- Variables globales para datos ---
df_tasas = None
df_ipc = None

# --- Cargar datos ---
def cargar_datos():
    global df_tasas, df_ipc
    
    try:
        # Cargar tasas
        df_tasas = pd.read_csv('attached_assets/tasas_dian_1750970948403.csv', sep=';', dayfirst=True)
        df_tasas.columns = ['fecha_inicio', 'fecha_fin', 'tasa']
        df_tasas['fecha_inicio'] = pd.to_datetime(df_tasas['fecha_inicio'], dayfirst=True)
        df_tasas['fecha_fin'] = pd.to_datetime(df_tasas['fecha_fin'], dayfirst=True)
        df_tasas['tasa'] = df_tasas['tasa'].str.replace('%', '').str.replace(',', '.').astype(float) / 100
        
        # Cargar IPC (datos de ejemplo)
        df_ipc = pd.DataFrame({
            'anio': [2018, 2019, 2020, 2021, 2022, 2023, 2024],
            'tasa': [0.0318, 0.0360, 0.0161, 0.0515, 0.1312, 0.0921, 0.0565]
        })
        print("Datos cargados correctamente")
    except Exception as e:
        print(f"Error cargando datos: {e}")
        # Crear datos por defecto si no se pueden cargar
        df_tasas = pd.DataFrame({
            'fecha_inicio': [datetime(2018, 1, 1)],
            'fecha_fin': [datetime(2025, 12, 31)],
            'tasa': [0.15]
        })
        df_ipc = pd.DataFrame({
            'anio': [2018, 2019, 2020, 2021, 2022, 2023, 2024],
            'tasa': [0.0318, 0.0360, 0.0161, 0.0515, 0.1312, 0.0921, 0.0565]
        })

def obtener_tasa(fecha, tipo_tasa="TASA DIAN"):
    """Obtiene la tasa según el tipo especificado"""
    try:
        fila = df_tasas[(df_tasas['fecha_inicio'] <= fecha) & (df_tasas['fecha_fin'] >= fecha)]
        if fila.empty:
            return 0.15  # Tasa por defecto
        
        tasa_base = fila.iloc[0]['tasa']
        
        if tipo_tasa == "TASA DIAN":
            return tasa_base
        elif tipo_tasa == "ART. 91 LEY 2277":
            return tasa_base * 0.5
        elif tipo_tasa == "ART 45 LEY 2155":
            return ((tasa_base + 0.02) / 1.5) * 0.2
        elif tipo_tasa == "ART 48 LEY 2155":
            return (tasa_base + 0.02) / 1.5
        elif tipo_tasa == "ART 120 LEY 2010":
            return ((tasa_base + 0.02) / 1.5) + 0.02
        else:
            return tasa_base
    except Exception as e:
        print(f"Error obteniendo tasa: {e}")
        return 0.15

def incremento_ipc_compuesto(anio_inicio, anio_fin):
    try:
        if anio_fin <= anio_inicio:
            return 0.0
        tasas = df_ipc[(df_ipc['anio'] > anio_inicio) & (df_ipc['anio'] <= anio_fin)]['tasa']
        acumulado = 1.0
        for tasa in tasas:
            acumulado *= (1 + tasa)
        return acumulado - 1
    except Exception as e:
        print(f"Error calculando IPC: {e}")
        return 0.05

def redondear_mas(valor):
    return round(valor / 1000.0) * 1000

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
        self.fecha_vencimiento = datetime.strptime(data['fecha_vencimiento'], '%Y-%m-%d')
        self.fecha_presentacion_sancion = datetime.strptime(data['fecha_presentacion_sancion'], '%Y-%m-%d')
        self.tipo_norma = data['tipo_norma']
        self.pagos = data['pagos']

        self.saldo_intereses = 0.0
        self.historial = []

    def procesar(self):
        anio_liquidacion = self.fecha_presentacion_sancion.year
        ultimo_anio_actualizado = anio_liquidacion

        for pago in self.pagos:
            fecha_pago = datetime.strptime(pago['fecha'], '%Y-%m-%d')
            monto_pago = float(pago['valor'])
            tipo_tasa = pago.get('tipo_tasa', 'TASA DIAN')
            
            dias_mora = max(0, (fecha_pago - self.fecha_vencimiento).days)
            tasa = obtener_tasa(fecha_pago, tipo_tasa)

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
            if total_deuda == 0:
                factor = 0
            else:
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
                'tasa_aplicada': f"{tasa*100:.2f}%",
                'monto_pago': f"${monto_pago:,.0f}",
                'impuesto_proporcion': f"${impuesto_pago:,.0f}",
                'intereses_proporcion': f"${intereses_pago:,.0f}",
                'sancion_proporcion': f"${sancion_pago:,.0f}",
                'impuesto_saldo': f"${self.saldo_impuesto:,.0f}",
                'intereses_saldo': f"${self.saldo_intereses:,.0f}",
                'sancion_saldo': f"${self.saldo_sancion:,.0f}"
            })

    def resumen(self):
        return self.historial

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    try:
        data = request.json
        motor = MotorLiquidacion(data)
        motor.procesar()
        return jsonify(motor.resumen())
    except Exception as e:
        print(f"Error en cálculo: {e}")
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    cargar_datos()
    print("Iniciando servidor Flask en http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
