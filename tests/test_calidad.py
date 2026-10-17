import copy
import unittest
from calidad import leer_datos, leer_reglas, perfilar, validar


class PruebasCalidad(unittest.TestCase):
    def setUp(self):
        self.reglas = leer_reglas()
        self.columnas, self.filas = leer_datos()

    def test_ejemplo_con_incidencias_conocidas(self):
        reporte = validar(self.columnas, self.filas, self.reglas)
        self.assertEqual(reporte["total_filas"], 8)
        self.assertEqual(reporte["total_incidencias"], 8)
        self.assertEqual(reporte["filas_con_incidencias"], 7)
        self.assertEqual(reporte["porcentaje_filas_con_incidencias"], 87.5)
        self.assertEqual(reporte["incidencias_por_severidad"], {"alta": 3, "media": 4, "baja": 1})

    def test_fila_valida_y_vacio_no_es_exito(self):
        self.assertEqual(validar(self.columnas, [self.filas[0]], self.reglas)["estado"], "sin_incidencias")
        self.assertEqual(validar(self.columnas, [], self.reglas)["estado"], "sin_datos")

    def test_cambios_json_controlan_validacion(self):
        reglas = copy.deepcopy(self.reglas)
        next(r for r in reglas["reglas"] if r["id"] == "R07")["valores"].append("Toluca")
        self.assertEqual(validar(self.columnas, self.filas, reglas)["total_incidencias"], 7)

    def test_edad_no_numerica_y_decimal_no_son_validas(self):
        for valor in ["abc", "25.5", "NaN"]:
            fila = dict(self.filas[0], edad=valor)
            reporte = validar(self.columnas, [fila], self.reglas)
            self.assertEqual([i["regla_id"] for i in reporte["incidencias"]], ["R06"])

    def test_columna_ausente_se_reporta_una_sola_vez(self):
        columnas = [c for c in self.columnas if c != "email"]
        filas = [{k: v for k, v in f.items() if k != "email"} for f in self.filas]
        reporte = validar(columnas, filas, self.reglas)
        self.assertEqual(reporte["columnas_faltantes"], ["email"])
        self.assertEqual(sum(i["regla_id"] == "ESQUEMA" for i in reporte["incidencias"]), 1)

    def test_perfil_no_cuenta_vacios_como_valores_distintos(self):
        perfil = perfilar(self.columnas, self.filas)
        self.assertEqual(perfil["vacios_por_columna"]["email"], 1)
        self.assertEqual(perfil["valores_distintos_no_vacios"]["cliente_id"], 7)


if __name__ == "__main__":
    unittest.main()
