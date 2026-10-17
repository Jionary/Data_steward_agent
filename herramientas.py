"""Las tres herramientas que puede elegir el agente."""
import json
from langchain_core.tools import tool
from calidad import leer_reglas, leer_datos, perfilar, validar, guardar_json


@tool
def consultar_reglas() -> str:
    """Lee reglas.json: campos, tipos de validación, severidades y acciones sugeridas."""
    return json.dumps(leer_reglas(), ensure_ascii=False)


@tool
def perfilar_datos() -> str:
    """Describe clientes.csv: filas, columnas, valores vacíos y valores distintos."""
    columnas, filas = leer_datos()
    return json.dumps(perfilar(columnas, filas), ensure_ascii=False)


@tool
def validar_calidad() -> str:
    """Aplica reglas.json a clientes.csv y guarda reportes/reporte_calidad.json con incidencias y filas."""
    columnas, filas = leer_datos()
    reporte = validar(columnas, filas, leer_reglas())
    guardar_json("reporte_calidad.json", reporte)
    return json.dumps(reporte, ensure_ascii=False)


HERRAMIENTAS = [consultar_reglas, perfilar_datos, validar_calidad]
