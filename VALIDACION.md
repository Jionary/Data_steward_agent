# Validación del proyecto

Validado con Python 3.12 en Linux durante la preparación del entregable.

- Instalación de dependencias con `uv sync --python 3.12`: correcta; versiones conservadas en `uv.lock`.
- `python demo.py`: 8 incidencias, 7 filas afectadas de 8 (87.5%).
- `uv run --locked --python 3.12 python -m unittest discover -s tests -v`: **10 pruebas correctas**.
- Las pruebas de reglas cubren el ejemplo, datos válidos, CSV sin filas, cambios en el catálogo JSON, edad no numérica, columna ausente y perfil de vacíos.
- Las pruebas del agente usan respuestas simuladas y herramientas reales. Comprueban las tres llamadas, la conclusión prematura, llamadas repetidas y herramientas desconocidas.
- Creación de `ChatOllama` y enlace de las tres herramientas con `bind_tools`: correcta, sin llamar al modelo.
- Los JSON en `ejemplos/` se generaron con la demo determinista; no son respuestas de un LLM.

**Pendiente de comprobar en la computadora de entrega:** ejecutar `agente.py` con Ollama y `llama3.1:latest`. No se afirma una prueba de extremo a extremo con un modelo real ni una prueba ejecutada en Windows. El modelo puede producir errores o no concluir; el prototipo conserva ese límite explícitamente.

El proyecto aún no tiene una URL pública de GitHub. El README explica cómo publicarlo y obtener el enlace de entrega.
