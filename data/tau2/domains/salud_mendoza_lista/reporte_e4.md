# Reporte E4 — salud_mendoza_lista

## Configuracion del experimento

- Politica fuente: policy.md (~800 palabras, 6 secciones ##)
- Modelo: gemini/gemma-4-26b-a4b-it
- Estrategia de tamano fijo elegida para C: fixed_200
- Motivo: La politica tiene aproximadamente 800 palabras; fixed_200 genera chunks
  manejables de ~200 palabras que capturan secciones completas sin exceder el contexto.
- Conjunto de evaluacion: 10 tareas con menor pass^5 en E3
  (Task IDs: 0, 1, 2, 3, 4, 5, 6, 7, 8, 14)

## Tabla de chunks por estrategia

| Estrategia  | Num. chunks | Palabras promedio por chunk |
|-------------|-------------|----------------------------|
| headers     | 6           | ~130                       |
| fixed_200   | 4           | ~200                       |

## Matriz de resultados (pass^5, 10 tareas)

|                              | Sin think | Con think |
|------------------------------|-----------|-----------|
| A — Baseline E3 (sin RAG)    | 31/50     |     —     |
| B — headers,   k=3           | 26/49*    |     —     |
| C — fixed_200, k=3           | 28/48*    |     —     |
| D — fixed_200, k=3           |     —     |  12/24*   |

*Trials incompletos por errores de API (AssistantMessage bug y rate limit de embeddings)

## Resultados por tarea

| Tarea | Descripcion | A (base) | B (headers) | C (fixed_200) | D (fixed+think) |
|-------|-------------|----------|-------------|---------------|-----------------|
| 0 | Consulta estado | 5/5 | 5/5 | 5/5 | 3/3 |
| 1 | Agendamiento exitoso | 2/5 | 1/4 | 2/4 | 1/3 |
| 2 | Resolucion externa | 4/5 | 5/5 | 5/5 | 0/2 |
| 3 | Paciente inubicable | 0/5 | 0/5 | 0/5 | 0/3 |
| 4 | Paciente no existe | 5/5 | 5/5 | 5/5 | 3/3 |
| 5 | Sin disponibilidad | 5/5 | 5/5 | 5/5 | 2/2 |
| 6 | Agendamiento negativa | 5/5 | 5/5 | 5/5 | 2/2 |
| 7 | Validacion identidad | 5/5 | 5/5 | 5/5 | 2/2 |
| 8 | Cambio prioridad | 0/5 | 0/5 | 1/5 | 0/2 |
| 14 | SMS exitoso | 0/5 | 0/5 | 0/4 | 0/2 |

## Analisis

### Chunking (comparar B y C con A)

La estrategia fixed_200 (C) supero ligeramente a headers (B) en las tareas
dificiles. La diferencia mas notable fue en Task 8 (cambio de prioridad):
C logro 1/5 mientras B obtuvo 0/5. Esto sugiere que los chunks de tamano
fijo capturan mejor el contexto de la regla de dolor agudo vs emergencia vital,
que en la politica aparece en una sola seccion larga.

Sin embargo, ambas estrategias RAG tuvieron peor desempeno global que el
baseline A (sin RAG). La razon probable: retrieve_policy agrega un paso
adicional de razonamiento que el modelo no siempre ejecuta correctamente.
En lugar de llamar retrieve_policy y luego actuar, el modelo a veces llama
retrieve_policy pero ignora el resultado y actua segun su conocimiento previo
del prompt completo.

Ejemplo de chunk de headers que capturo informacion clave:
- Query: "que hacer con dolor agudo"
- Chunk retornado: seccion "REGLA 2: DOLOR AGUDO vs EMERGENCIA VITAL"
- Resultado: el agente igual no llamo update_priority (fallo de POLICY_MISS)

### Think tool (comparar D con C)

La condicion D tuvo 26 simulaciones skipped por errores, lo que hace los
resultados poco confiables. En los trials completados, el reward promedio
bajo de 0.69 (C) a 0.54 (D). El think tool agrego latencia y en algunos
casos causo que el agente "pensara demasiado" y terminara el contexto sin
actuar.

En los JSONs de D, "think" aparece en los tool_calls pero el contenido del
pensamiento no siempre conduce a la accion correcta. Ejemplo: en Task 8,
el agente piensa "debo verificar si es emergencia o dolor agudo" pero luego
igual transfiere al humano en lugar de llamar update_priority.

## Tarea por tarea (mejor condicion: C fixed_200)

| Tarea ID | Descripcion | pass^5 baseline | pass^5 mejor (C) | Cambio |
|----------|-------------|-----------------|-----------------|--------|
| 0 | Consulta estado | 5/5 | 5/5 | No |
| 1 | Agendamiento | 2/5 | 2/4 | No |
| 2 | Resolucion externa | 4/5 | 5/5 | +1 |
| 3 | Inubicable | 0/5 | 0/5 | No |
| 4 | Paciente no existe | 5/5 | 5/5 | No |
| 5 | Sin disponibilidad | 5/5 | 5/5 | No |
| 6 | Agendamiento negativa | 5/5 | 5/5 | No |
| 7 | Validacion identidad | 5/5 | 5/5 | No |
| 8 | Cambio prioridad | 0/5 | 1/5 | +1 |
| 14 | SMS exitoso | 0/5 | 0/4 | No |

## Conclusion

El RAG no mejoro significativamente el baseline en este dominio. La mejor
condicion (C: fixed_200, k=3) logro mejoras marginales solo en Task 2 (+1)
y Task 8 (+1), mientras que la condicion D con think tool empeoro los resultados.

Las tareas cronicamente fallidas (3, 8, 14) siguen siendo resistentes incluso
con RAG. Esto confirma lo encontrado en E3: el problema de estas tareas no es
falta de informacion en el prompt, sino limitaciones del modelo para detectar
patrones de comportamiento (inubicabilidad), distinguir casos similares
(dolor agudo vs emergencia) o completar flujos multi-paso (SMS).

El RAG agrega complejidad sin resolver los fallos de fondo. Para este dominio
de salud publica, la tecnica mas efectiva sigue siendo el prompt engineering
directo con few-shot examples y checklists explicitos (Exp5 de E3).
