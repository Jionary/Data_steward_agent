"""Demostración determinista SIN LLM: no representa una ejecución del agente."""
import json
from calidad import leer_datos, leer_reglas, perfilar, validar, guardar_json


def main():
    reglas = leer_reglas()
    columnas, filas = leer_datos()
    perfil = perfilar(columnas, filas)
    reporte = validar(columnas, filas, reglas)
    guardar_json("perfil.json", perfil)
    destino = guardar_json("reporte_calidad.json", reporte)
    print("DEMO SIN LLM: ejecución directa de funciones, sin decisiones del modelo.")
    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    print(f"\nReporte: {destino}")


if __name__ == "__main__":
    main()
