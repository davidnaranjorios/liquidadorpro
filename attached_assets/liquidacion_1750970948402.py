# liquidacion.py
# Clase principal del motor de liquidación

from datetime import datetime
from tasas import cargar_tasas, calcular_tasa, obtener_tasa_base
from ipc import cargar_ipc, obtener_incremento_ipc_compuesto
from reglas import calcular_intereses, calcular_sancion, aplicar_proporciones

class MotorLiquidacion:
    def __init__(self, valor_inicial, fecha_vencimiento, tipo_liquidacion, anio_liquidacion, tipo_proporcion, proporciones_dict):
        self.valor_inicial = valor_inicial
        self.fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%d/%m/%Y')
        self.tipo_liquidacion = tipo_liquidacion
        self.anio_liquidacion = anio_liquidacion
        self.tipo_proporcion = tipo_proporcion
        self.proporciones_dict = proporciones_dict

        self.saldo_impuesto = valor_inicial
        self.saldo_intereses = 0.0
        self.saldo_sancion = 0.0
        self.pagos = []  # Lista de pagos procesados

    def procesar_pago(self, fecha_pago_str, monto):
        fecha_pago = datetime.strptime(fecha_pago_str, '%d/%m/%Y')
        dias_mora = (fecha_pago - self.fecha_vencimiento).days
        dias_mora = max(dias_mora, 0)

        # Intereses
        tasa_dian = obtener_tasa_base(fecha_pago)
        interes_calculado = calcular_intereses(self.saldo_impuesto, tasa_dian, dias_mora)

        # Sancion actualizada si cambia de año
        anio_pago = fecha_pago.year
        self.saldo_sancion = calcular_sancion(
            self.saldo_sancion,
            self.tipo_liquidacion,
            self.anio_liquidacion,
            anio_pago,
            obtener_incremento_ipc_compuesto
        )

        self.saldo_intereses = interes_calculado

        # Aplicar proporciones al monto del pago
        asignacion = aplicar_proporciones(monto, self.tipo_proporcion, self.proporciones_dict)

        # Actualizar saldos
        self.saldo_impuesto = max(0.0, self.saldo_impuesto - asignacion['impuesto'])
        self.saldo_intereses = max(0.0, self.saldo_intereses - asignacion['intereses'])
        self.saldo_sancion = max(0.0, self.saldo_sancion - asignacion['sancion'])

        # Reconfigurar valor inicial con el nuevo saldo de impuesto
        self.valor_inicial = self.saldo_impuesto

        # Registrar el pago
        self.pagos.append({
            'fecha_pago': fecha_pago_str,
            'monto': monto,
            'asignacion': asignacion,
            'intereses_calculados': interes_calculado,
            'saldo_impuesto': self.saldo_impuesto,
            'saldo_intereses': self.saldo_intereses,
            'saldo_sancion': self.saldo_sancion
        })

    def resumen(self):
        return {
            'saldo_impuesto': self.saldo_impuesto,
            'saldo_intereses': self.saldo_intereses,
            'saldo_sancion': self.saldo_sancion,
            'pagos': self.pagos
        }

    @staticmethod
    def inicializar_datos(ruta_tasas, ruta_ipc):
        cargar_tasas(ruta_tasas)
        cargar_ipc(ruta_ipc)
