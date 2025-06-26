# reglas.py
# Módulo para reglas de negocio del motor de liquidación

def calcular_intereses(valor_inicial, tasa, dias):
    """
    Cálculo de intereses de mora simple:
    intereses = valor_inicial * tasa * (dias / 365)
    """
    return round(valor_inicial * tasa * (dias / 365), 2)


def calcular_sancion(saldo_sancion, tipo_liquidacion, anio_liquidacion, anio_pago, obtener_incremento):
    """
    Actualiza la sancion según el tipo de liquidación:
    - Si es "privada": solo se actualiza a partir del año subsiguiente.
    - Si es "oficial": se actualiza desde el año siguiente.

    El incremento se calcula con capitalización compuesta usando IPC.
    """
    if tipo_liquidacion.lower() == "privada":
        anio_base = anio_liquidacion + 2
    else:  # oficial
        anio_base = anio_liquidacion + 1

    if anio_pago >= anio_base:
        incremento = obtener_incremento(anio_liquidacion, anio_pago)
        return round(saldo_sancion * (1 + incremento), 2)
    else:
        return saldo_sancion


def aplicar_proporciones(monto_pago, tipo_proporcion, proporciones_dict):
    """
    Asigna el monto del pago según el tipo de proporción definido.
    proporciones_dict debe contener:
    {
        "Proporción 1: Impuesto mayor": (p_imp, p_int, p_sanc),
        "Proporción 2: Interes mayor": (p_imp, p_int, p_sanc),
        "Proporción 3: Sanción mayor": (p_imp, p_int, p_sanc)
    }

    Devuelve un diccionario con valores asignados a cada rubro.
    """
    if tipo_proporcion not in proporciones_dict:
        raise ValueError("Tipo de proporción no reconocido")

    p_imp, p_int, p_sanc = proporciones_dict[tipo_proporcion]
    return {
        "impuesto": round(monto_pago * p_imp, 2),
        "intereses": round(monto_pago * p_int, 2),
        "sancion": round(monto_pago * p_sanc, 2)
    }
