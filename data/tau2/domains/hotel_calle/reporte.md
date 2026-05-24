# Reporte - Hotel Calle Entrega 2

## Configuracion

- Dominio: hotel_calle
- Modelo agente: gemini/gemma-4-31b-it
- Modelo usuario: gemini/gemma-4-26b-a4b-it
- Evaluador NL: gemini/gemma-4-26b-a4b-it para tareas con `NL_ASSERTION`
- Metrica final: pass^10 por tarea
- Nota: completar esta tabla con los JSON reales generados en `simulations/`.

## Estado parcial de corridas

Se esta organizando la evidencia en 10 corridas. Cada corrida debe cubrir las 20 tareas una vez. Por inestabilidad de la API de Google/Gemma, algunas corridas se completan por partes y se documentan en manifest.

- Manifest parcial Corrida 1: `simulations_manifest_round_01.csv`
- Cobertura actual Corrida 1: 20/20 tareas completas
- Resultado Corrida 1: 12/20 tareas exitosas
- Faltan en Corrida 1: ninguna
- Manifest parcial Corrida 2: `simulations_manifest_round_02.csv`
- Cobertura actual Corrida 2: 20/20 tareas completas
- Resultado Corrida 2: 11/20 tareas exitosas
- Faltan en Corrida 2: ninguna
- Manifest parcial Corrida 3: `simulations_manifest_round_03.csv`
- Cobertura actual Corrida 3: 20/20 tareas completas
- Resultado Corrida 3: 13/20 tareas exitosas
- Faltan en Corrida 3: ninguna
- Nota tecnica: las tareas 11 a 20 incluyen `NL_ASSERTION`, por lo que deben evaluarse con `EvaluationType.ALL_WITH_NL_ASSERTIONS`.

## Tabla de resultados pass^10

| Tarea | Descripcion breve | pass^10 | % de falla |
|---|---|---:|---:|
| Pendiente | Ejecutar simulaciones finales con Gemma | Pendiente | Pendiente |

## Analisis de las 3 tareas con peor rendimiento

Pendiente de completar despues de ejecutar las 10 pasadas por tarea. Para cada tarea se debe indicar:

- falla tipica observada;
- tecnicas de prompt engineering probadas;
- metrica antes/despues;
- conclusion sobre que funciono y que no.

## Experimentos de prompt engineering

Registrar aqui al menos 5 tecnicas, con referencia a los archivos en `prompts/` y `simulations/`.

## Conclusion general

Pendiente de completar con resultados reales de Gemma.
