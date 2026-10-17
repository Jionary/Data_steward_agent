"""Prueba la ejecución de herramientas con respuestas simuladas, sin un LLM real."""
import contextlib
import io
import unittest
from unittest.mock import patch
from langchain_core.messages import AIMessage
from agente import ejecutar


def llamada(nombre, identificador):
    return {"name": nombre, "args": {}, "id": identificador, "type": "tool_call"}


class ModeloSimulado:
    def __init__(self, respuestas):
        self.respuestas = iter(respuestas)
        self.invocaciones = 0

    def bind_tools(self, herramientas):
        self.nombres = [h.name for h in herramientas]
        return self

    def invoke(self, mensajes):
        self.invocaciones += 1
        return next(self.respuestas)


class PruebasAgente(unittest.TestCase):
    def correr(self, modelo, max_pasos=6):
        with contextlib.redirect_stdout(io.StringIO()):
            with patch("herramientas.guardar_json"):
                return ejecutar(modelo, "Audita los clientes.", max_pasos=max_pasos)

    def test_ejecuta_las_tres_herramientas_y_concluye(self):
        modelo = ModeloSimulado([
            AIMessage(content="", tool_calls=[llamada("consultar_reglas", "a")]),
            AIMessage(content="", tool_calls=[llamada("perfilar_datos", "b")]),
            AIMessage(content="", tool_calls=[llamada("validar_calidad", "c")]),
            AIMessage(content="Resumen de prueba, no generado por un LLM real."),
        ])
        resultado = self.correr(modelo)
        self.assertEqual(resultado["estado"], "completo")
        self.assertEqual(len(resultado["llamadas"]), 3)
        self.assertEqual(resultado["llamadas"][-1]["resultado"]["total_incidencias"], 8)

    def test_respuesta_prematura_no_se_declara_completa(self):
        modelo = ModeloSimulado([AIMessage(content="Todo está bien.")] * 2)
        resultado = self.correr(modelo, max_pasos=2)
        self.assertEqual(resultado["estado"], "incompleto")
        self.assertEqual(modelo.invocaciones, 2)

    def test_repeticion_no_repite_ejecucion_de_la_herramienta(self):
        modelo = ModeloSimulado([
            AIMessage(content="", tool_calls=[llamada("consultar_reglas", "a")]),
            AIMessage(content="", tool_calls=[llamada("consultar_reglas", "b")]),
        ])
        resultado = self.correr(modelo, max_pasos=2)
        self.assertFalse(resultado["llamadas"][0]["error"])
        self.assertTrue(resultado["llamadas"][1]["error"])
        self.assertEqual(resultado["estado"], "incompleto")

    def test_herramienta_desconocida_se_reporta_sin_ejecutarla(self):
        modelo = ModeloSimulado([
            AIMessage(content="", tool_calls=[llamada("borrar_clientes", "a")]),
        ])
        resultado = self.correr(modelo, max_pasos=1)
        self.assertTrue(resultado["llamadas"][0]["error"])
        self.assertEqual(resultado["estado"], "incompleto")


if __name__ == "__main__":
    unittest.main()
