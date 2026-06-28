# Reporte E4 - Dominio enosa_masias

## Configuracion del experimento
- Politica fuente: policy.md
- Modelo de agente: gemini/gemma-4-31b-it
- Modelo de usuario: gemini/gemma-4-26b-a4b-it
- Estrategia de tamano fijo elegida para la condicion C: fixed_200
- Motivo de eleccion: El documento de politicas de ENOSA tiene una estructura de secciones muy marcada. Se evaluo fixed_200 para contrastar que sucede cuando el framework RAG corta las reglas por limite de palabras en lugar de respetar la division semantica de los encabezados.

## Tabla de chunks por estrategia
| Estrategia | Num. chunks | Palabras promedio por chunk |
|------------|-------------|-----------------------------|
| headers    | 12          | 115                         |
| fixed_200  | 8           | 170                         |

## Matriz de resultados (Métrica pass^5, 10 tareas)

| Estrategia         | Sin think (Pass^5) | Con think (Pass^5)   |
|--------------------|--------------------|----------------------|
| A - Baseline E3    | 0.8980 | No aplica | ---------------------|
| B - Headers, k=3   | 0.7800 | No aplica | ---------------------|
| C - Fixed_200, k=3 | 0.3125 | No aplica | ---------------------|
| D - Headers, k=3   | ------ | No aplica | Abortado (Error 429) |

## Analisis de resultados
- Analisis de Chunking: Los resultados demuestran que la estrategia Headers (Condicion B) es ampliamente superior a Fixed_200 (Condicion C). La caida de rendimiento en C a 0.3125 se debe a que el corte arbitrario de 200 palabras dividio las reglas de validacion de identidad (pedir DNI o Suministro), provocando que el agente perdiera el contexto y realizara acciones prohibidas.
- Analisis de Think Tool y limites de infraestructura: La simulacion D tuvo que ser abortada forzosamente durante la tarea 15. El log del framework arrojo un error ClientError: 429 RESOURCE_EXHAUSTED. Esto ocurrio porque se alcanzo el limite estricto de 1000 requests por dia del modelo gemini-embedding-1.0 en la capa gratuita de Google AI Studio. Este es un hallazgo critico: implementar RAG multiplica el consumo de cuota por cada interaccion del chat, haciendo inviable su uso continuo sin una arquitectura de cache para embeddings o el paso a una capa de facturacion Pay-as-you-go.

## Desglose Tarea por Tarea (Comparacion Baseline vs Mejor Condicion RAG: B)
| Tarea ID | pass^5 baseline (A) | pass^5 mejor RAG (B) | Cambio    |
|----------|---------------------|----------------------|-----------|
| enosa_11 | 1.0000              | 0.8000               | Disminuyo |
| enosa_12 | 0.0000              | 0.2000               | Aumento   |
| enosa_13 | 1.0000              | 0.8000               | Disminuyo |
| enosa_14 | 1.0000              | 0.8000               | Disminuyo |
| enosa_15 | 1.0000              | 0.8000               | Disminuyo |

## Conclusion del experimento
La aplicacion de RAG estructurado por encabezados demostro ser el metodo de particion mas seguro para la base de conocimientos. Sin embargo, el Baseline absoluto sin RAG (0.8980) supero a la mejor implementacion con RAG (0.7800). Adicionalmente, el bloqueo por limites de cuota (429) revela que para politicas de tamano moderado, es mas eficiente inyectar el texto completo en el System Prompt que depender de llamadas externas a un modelo de embeddings.