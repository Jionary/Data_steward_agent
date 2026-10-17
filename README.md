# Primer agente Data Steward

Prototipo académico que revisa un CSV de clientes ficticios usando **Ollama, LangChain y tres herramientas con `@tool`**. Las reglas de calidad están en un JSON editable. El agente consulta las herramientas y propone acciones; no modifica los datos originales.

## Qué demuestra

- Un modelo local que solicita llamadas reales a herramientas.
- Tres funciones decoradas con `@tool` en `herramientas.py`.
- Reglas externas en `reglas.json`; no dependen de que el modelo haga bien las cuentas.
- Evidencias por regla, columna y fila del CSV.
- Una conclusión en español generada por el modelo y un límite de seis pasos.

| Herramienta | Qué hace | Resultado |
| --- | --- | --- |
| `consultar_reglas` | Lee el JSON | Criterios, severidad y acciones sugeridas |
| `perfilar_datos` | Describe el CSV | Filas, columnas, vacíos y valores distintos |
| `validar_calidad` | Aplica las reglas | Incidencias y `reportes/reporte_calidad.json` |

## Instalación en Windows / PowerShell

Requisitos: `uv` y Ollama instalados. Ejecuta los comandos desde esta carpeta, que es un proyecto independiente del repositorio del curso.

```powershell
uv python install 3.12
uv sync --python 3.12
Copy-Item .env.example .env
ollama pull llama3.1:latest
```

Mantén Ollama ejecutándose. El modelo debe estar instalado en la misma instancia indicada por `OLLAMA_HOST`. No necesitas claves de OpenAI, Google ni Tavily para este ejercicio. El archivo `.env` está excluido de Git.

Las dependencias se mantienen en la familia 0.3 de LangChain para que el proyecto sea cercano al ejercicio del curso. `uv.lock` fija las versiones cuando está incluido; usa `uv sync --locked --python 3.12` para reproducir exactamente esas versiones.

## Ejecutar el agente real

```powershell
uv run --python 3.12 python agente.py
```

También puedes cambiar la petición:

```powershell
uv run --python 3.12 python agente.py --pregunta "Revisa los clientes y explica qué problemas atenderías primero. Usa las tres herramientas."
```

El modelo usa `bind_tools` para recibir la descripción de las herramientas y elegir sus llamadas. El bucle en `agente.py` ejecuta las funciones solicitadas y devuelve sus resultados como `ToolMessage`. Esto es un agente con llamadas nativas a herramientas; no utiliza el prompt ReAct del Hub ni necesita descargarlo.

En la terminal deben verse líneas como `[Herramienta solicitada] validar_calidad`. Una ejecución se marca como `completo` solo después de ejecutar exitosamente las tres herramientas y recibir una conclusión del modelo. Esto verifica la cobertura de herramientas, no garantiza que el texto del modelo sea correcto.

Los resultados se guardan en:

- `reportes/reporte_calidad.json`: evidencia calculada por Python.
- `reportes/ejecucion_agente.json`: llamadas, argumentos, errores y respuesta generada.
- `reportes/respuesta_agente.txt`: conclusión del modelo.

Estos archivos se sobrescriben al repetir una ejecución exitosa. Un archivo previo puede seguir existiendo si una ejecución posterior falla: revisa la salida de la terminal y las fechas de los archivos. No se ejecuta código generado por el modelo.

## Probar las reglas sin modelo

```powershell
python demo.py
python -m unittest discover -s tests -p test_calidad.py -v
```

Si `python` no se reconoce, usa `uv run --python 3.12 python demo.py`. El script `demo.py` solo usa la biblioteca estándar. Es una auditoría determinista, **no una ejecución del agente**: no hay un modelo eligiendo herramientas.

Para ejecutar todas las pruebas, incluyendo las del bucle del agente con respuestas simuladas y herramientas reales, instala las dependencias y usa `uv run --python 3.12 python -m unittest discover -s tests -v`.

Resultado esperado del CSV incluido:

| Métrica | Resultado |
| --- | ---: |
| Filas de clientes | 8 |
| Incidencias | 8 |
| Filas con incidencias | 7 |
| Filas con incidencias (%) | 87.5 |
| Severidad alta / media / baja | 3 / 4 / 1 |

Las dos filas con ID `C002` se marcan como duplicadas. Por eso dos incidencias corresponden a un mismo valor duplicado. La fila CSV 1 es el encabezado; las incidencias comienzan a numerarse desde la fila 2.

| Regla | Filas CSV | Hallazgo |
| --- | --- | --- |
| R02 | 3 y 6 | ID `C002` repetido |
| R03 | 4 | Nombre vacío |
| R04 | 7 | Email vacío |
| R05 | 3 | Formato de email inválido |
| R06 | 5 y 8 | Edad fuera de 18 a 100 |
| R07 | 9 | Toluca no está en el catálogo del ejercicio |

## Cambiar una regla y comprobarlo

Agrega `"Toluca"` al arreglo `valores` de la regla R07 en `reglas.json`, guarda y vuelve a ejecutar `python demo.py`. El total pasa de **8 a 7 incidencias**. No necesitas cambiar el código Python. Las pruebas que verifican el ejemplo original esperan las reglas originales.

Las reglas de formato, rango, catálogo y unicidad omiten valores vacíos. Para que un campo sea obligatorio, agrega una regla de tipo `obligatorio` para esa columna. La coincidencia con catálogos distingue mayúsculas y acentos. Al leer el CSV se quitan espacios al principio y al final solo en memoria.

## LangSmith opcional

En `.env`, cambia o agrega:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=TU_CLAVE
LANGSMITH_PROJECT=data-steward-clientes
```

Vuelve a ejecutar el agente y abre ese proyecto en [LangSmith](https://smith.langchain.com/). Se registran las llamadas del modelo y las herramientas; como el bucle del agente es Python propio, pueden aparecer como ejecuciones separadas. Los resultados de herramientas incluyen datos del CSV y se envían a LangSmith al activar el rastreo. El ejemplo solo usa datos ficticios. Para cuentas fuera de GCP US configura también el endpoint de tu región según la documentación.

## Límites de esta primera versión

- El modelo puede equivocarse, repetir herramientas o alcanzar el límite sin concluir. El estado será `incompleto` y podrás inspeccionar la evidencia disponible.
- Se admiten como máximo seis respuestas del modelo y una ejecución por herramienta; no hay reintentos automáticos de herramientas fallidas. El timeout por petición de Ollama es de 180 segundos, no un límite total de ejecución.
- No es un sistema completo de gobierno de datos: faltan responsables reales, catálogo empresarial, aprobación de cambios e historial de auditorías.
- El formato de email no confirma que el correo exista. El catálogo y las edades son supuestos del ejercicio.
- Solo revisa `data/clientes.csv` y `reglas.json`. No hace búsquedas web, no corrige datos ni inventa valores faltantes.
- El motor de reglas y el bucle con respuestas simuladas pueden probarse sin descargar el modelo. La ejecución real de Llama debe comprobarse en una computadora con Ollama disponible; los resultados de simulación no son respuestas reales de Llama.

## Subir a GitHub y entregar un enlace

Opción desde el navegador:

1. Descomprime este proyecto y prueba el agente.
2. Ve a [github.com/new](https://github.com/new), crea un repositorio llamado `data-steward-agent` y elige la visibilidad que permita revisarlo a tu profesor.
3. En el repositorio, selecciona **Add file → Upload files** (o **uploading an existing file** si está vacío).
4. Sube los archivos del proyecto con `README.md` en la raíz. **No subas `.env`, `.venv`, `__pycache__` ni reportes con datos privados.** La carga desde navegador no aplica automáticamente `.gitignore`. Incluye `.env.example`, `.gitignore`, `.python-version`, los archivos Python, `reglas.json`, `pyproject.toml`, `uv.lock` si está incluido, `data/` y `tests/`.
5. Confirma con **Commit changes** y copia la URL del repositorio que aparece en el navegador. Ese es el enlace de entrega.

También puedes subirlo con Git desde la carpeta del proyecto. Crea primero un repositorio vacío en GitHub. Sustituye `TU_USUARIO` por tu usuario real:

```powershell
git init
git add .
git status
git commit -m "Primer agente Data Steward con tres herramientas y reglas JSON"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/data-steward-agent.git
git push -u origin main
```

Antes de confirmar el commit, revisa en `git status` que no haya claves ni archivos ajenos al proyecto. No incluyas el ZIP completo como único archivo del repo: el código debe poder leerse directamente.

## Explicación breve para presentar

> Hice una primera versión de un agente Data Steward que revisa la calidad de un CSV de clientes. Las reglas están en un JSON y tiene tres herramientas con el decorador `@tool`: consultar reglas, perfilar datos y validar calidad. Ollama solicita las herramientas y usa sus resultados para redactar una conclusión y proponer acciones. Los conteos los calcula Python y cada incidencia conserva la regla y la fila como evidencia. No corrige datos automáticamente. El modelo todavía puede equivocarse, por eso incluyo un límite de pasos y un modo de demostración para comprobar las reglas por separado.

## Referencias

- [LangChain: herramientas y decorador tool](https://docs.langchain.com/oss/python/langchain/tools).
- [Integración de Ollama y llamadas a herramientas](https://docs.langchain.com/oss/python/integrations/chat/ollama).
- [Rastreo de LangChain con LangSmith](https://docs.langchain.com/langsmith/trace-with-langchain).

Los datos de ejemplo fueron creados para esta práctica; no representan personas reales.
