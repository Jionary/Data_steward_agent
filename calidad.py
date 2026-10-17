"""Motor de reglas: funciona con la biblioteca estándar, sin LLM ni APIs."""
import csv
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent


def leer_reglas(path=None):
    with Path(path or BASE / "reglas.json").open(encoding="utf-8") as archivo:
        reglas = json.load(archivo)
    tipos = {"obligatorio", "unico", "regex", "rango_entero", "catalogo"}
    ids = set()
    for regla in reglas["reglas"]:
        if regla["tipo"] not in tipos:
            raise ValueError(f"Tipo de regla no soportado: {regla['tipo']}")
        if regla["id"] in ids:
            raise ValueError(f"ID de regla duplicado: {regla['id']}")
        ids.add(regla["id"])
        if regla["tipo"] == "regex":
            re.compile(regla["patron"])
    return reglas


def leer_datos(path=None):
    with Path(path or BASE / "data" / "clientes.csv").open(
        newline="", encoding="utf-8-sig"
    ) as archivo:
        lector = csv.DictReader(archivo)
        columnas = lector.fieldnames or []
        if len(columnas) != len(set(columnas)):
            raise ValueError("El CSV contiene encabezados duplicados.")
        filas = []
        for numero, fila in enumerate(lector, start=2):
            if None in fila or any(valor is None for valor in fila.values()):
                raise ValueError(f"Registro {numero}: cantidad incorrecta de columnas.")
            filas.append({columna: valor.strip() for columna, valor in fila.items()})
    return columnas, filas


def perfilar(columnas, filas):
    return {
        "filas": len(filas),
        "columnas": columnas,
        "vacios_por_columna": {
            columna: sum(fila[columna] == "" for fila in filas)
            for columna in columnas
        },
        "valores_distintos_no_vacios": {
            columna: len({fila[columna] for fila in filas if fila[columna]})
            for columna in columnas
        },
    }


def validar(columnas, filas, configuracion):
    incidencias = []
    faltantes = [c for c in configuracion["columnas_requeridas"] if c not in columnas]
    for columna in faltantes:
        incidencias.append({
            "regla_id": "ESQUEMA", "fila_csv": None, "columna": columna,
            "valor": None, "severidad": "alta", "detalle": "Columna requerida ausente.",
            "accion_sugerida": "Solicitar la columna al responsable de la fuente.",
        })
    for regla in configuracion["reglas"]:
        columna = regla["columna"]
        if columna not in columnas:
            # Una sola incidencia de esquema para cada columna ausente.
            if columna not in faltantes:
                raise ValueError(f"La regla {regla['id']} refiere una columna ausente: {columna}")
            continue
        conteo = Counter(f[columna] for f in filas if f[columna])
        for numero, fila in enumerate(filas, start=2):
            valor = fila[columna]
            tipo = regla["tipo"]
            detalle = None
            if tipo == "obligatorio" and not valor:
                detalle = "Valor obligatorio vacío."
            elif tipo == "unico" and valor and conteo[valor] > 1:
                detalle = f"Valor duplicado: aparece {conteo[valor]} veces."
            elif tipo == "regex" and valor and re.fullmatch(regla["patron"], valor) is None:
                detalle = "El valor no cumple el formato definido."
            elif tipo == "rango_entero" and valor:
                try:
                    valido = regla["min"] <= int(valor) <= regla["max"]
                except ValueError:
                    valido = False
                if not valido:
                    detalle = f"Se requiere un entero entre {regla['min']} y {regla['max']}."
            elif tipo == "catalogo" and valor and valor not in regla["valores"]:
                detalle = "Valor fuera del catálogo permitido."
            if detalle:
                incidencias.append({
                    "regla_id": regla["id"], "fila_csv": numero, "columna": columna,
                    "valor": valor, "severidad": regla["severidad"], "detalle": detalle,
                    "accion_sugerida": regla["accion"],
                })
    filas_afectadas = {i["fila_csv"] for i in incidencias if i["fila_csv"] is not None}
    return {
        "dataset": configuracion["dataset"],
        "version_reglas": configuracion["version"],
        "total_filas": len(filas),
        "columnas_faltantes": faltantes,
        "total_incidencias": len(incidencias),
        "filas_con_incidencias": len(filas_afectadas),
        "porcentaje_filas_con_incidencias": round(100 * len(filas_afectadas) / len(filas), 2) if filas else 0,
        "estado": "sin_datos" if not filas else ("con_incidencias" if incidencias else "sin_incidencias"),
        "incidencias_por_severidad": dict(Counter(i["severidad"] for i in incidencias)),
        "incidencias": incidencias,
        "nota": "Las filas CSV incluyen el encabezado como fila 1. Se marca cada fila de un ID duplicado. Los valores vacíos se revisan con reglas obligatorio; las demás reglas los omiten. El porcentaje no incluye errores de esquema.",
    }


def guardar_json(nombre, contenido):
    destino = BASE / "reportes" / nombre
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino
