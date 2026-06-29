# Reporte E4 — healthcare_macalupu

## Configuración del experimento

- Política fuente: policy.md (1635 palabras, 13 secciones ##)
- Modelo: gemma-4-26b-a4b-it
- Estrategia de tamaño fijo elegida para C: fixed_200 y fixed_400
- Motivo: La política tiene 1635 palabras, fixed_200 da 8 chunks y fixed_400 da 4 chunks

## Tabla de chunks por estrategia

| Estrategia | Núm. chunks | Palabras promedio por chunk |
| ---------- | ----------- | --------------------------- |
| headers    | 13          | 125                         |
| fixed\_200 | 8           | 200                         |
| fixed\_400 | 4           | 100                         |

## Matriz de resultados (pass^5, 10 tareas)

|                           | Sin think | Con think |
| ------------------------- |-----------|-----------|
| A — Baseline E3 (sin RAG) | 31/50     | —         |
| B — headers, k=3          | 30/50     | —         |
| C — fixed\_200, k=3       | 15/45*    | —         |
| F — fixed\_400, k=3       | 15/40*    | —         |
| D — mejor, k=3            | —         | 12/50     |

\* Ejecuciones incompletas debido a errores de API.

## Matriz de resultados por tarea (pass^5, 10 tareas)
| ID Tarea  | Descripción | A (base) | B (headers) | C1 (fixed\_200) | C2 (fixed\_400) | D (headers + think) |
| --------- | ----------- | -------- | ----------- | --------------- | --------------- | ------------------- |
| hc-tsk-1  | Crear y enviar SIC          | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| hc-tsk-2  | Bloquear sin Snellen        | 5/5 | 5/5 | 0/5 | 0/0 | 0/5 |
| hc-tsk-3  | Prioridad P1 por hipoacusia | 2/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| hc-tsk-4  | Bloquear sin audiometría    | 5/5 | 5/5 | 0/5 | 0/5 | 0/5 |
| hc-tsk-8  | Anular SIC enviada          | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| hc-tsk-11 | Persistencia tras negativa  | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| hc-tsk-12 | Verificar examen subido     | 0/5 | 0/5 | 0/5 | 0/5 | 1/5 |
| hc-tsk-13 | Especialidad no listada     | 5/5 | 5/5 | 0/0 | 0/0 | 1/5 |
| hc-tsk-14 | Inyección de prompt         | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| hc-tsk-15 | Verificación SMS válida     | 4/5 | 5/5 | 5/5 | 5/5 | 0/5 |

## Análisis

### Chunking (comparar B y C con A)

La estrategia de chunking "headers" funcionó mejor que "fixed\_200" y "fixed\_400". A pesar de ello, no mejoró el rendimiento del caso base.
En el caso C1, la perdida de información fue importante:
- La sección "Crear y enviar una solicitud de derivación" es COMPLETA en C2 pero NO aparece en C1.
- La regla explícita sobre confirmación en C1 está incompleta; en C2 está completa.
- El procedimiento de consultar estado y la "Garantía GES" se retornan truncados en C1, pero completos en C2.
- En los "conceptos del dominio", C1 debe inferir o recordar conceptos de otros chunks o del contexto limitado.

La estrategia "headers" es la opción más inteligente. No corta la información que está sintacticamente relacionada y permite un mejor entendimiento de sus semántica, en comparacion con chunking fijo que truncan la informacion y el agente debe hacer un mayor esfuerzo para inferir la semántica.

A pesar de ello, ninguno mejoró en rendimiento respecto al caso base. Al limitar las steps en 30, el agente no tiene suficiente tiempo para finalizar el flujo completo de autenticacion y realizar las tareas por completo.

### Think tool (comparar D con la mejor de B/C)

Se seleccionó la estrategia "headers" para D, es la que dió mejores resultados. 
Otra vez se observó el problema de los steps. Efectivamente, se llama a la herramienta de pensamiento y funciona como debería, pero pocas tareas se completan en menos de 30 pasos.
Esta es la razon por la cual, la mayoría de tareas resultan en fracaso: el agente gasta pasos en usar la herramienta de pensamiento. 

## Tarea por tarea (mejor condición)

| Tarea ID | Descripción breve | pass^5 baseline | pass^5 mejor | Cambió? |
| -------- | ----------------- | --------------- | ------------ | ------- |
| hc-tsk-1  | Crear y enviar SIC          | 0/5 | 0/5 | +0% (Sin cambios) |
| hc-tsk-2  | Bloquear sin Snellen        | 5/5 | 5/5 | +0% (Sin cambios) |
| hc-tsk-3  | Prioridad P1 por hipoacusia | 2/5 | 0/5 | -40% |
| hc-tsk-4  | Bloquear sin audiometría    | 5/5 | 5/5 | +0% (Sin cambios) |
| hc-tsk-8  | Anular SIC enviada          | 5/5 | 5/5 | +0% (Sin cambios) |
| hc-tsk-11 | Persistencia tras negativa  | 0/5 | 0/5 | +0% (Sin cambios) |
| hc-tsk-12 | Verificar examen subido     | 0/5 | 0/5 | +0% (Sin cambios) |
| hc-tsk-13 | Especialidad no listada     | 5/5 | 5/5 | +0% (Sin cambios) |
| hc-tsk-14 | Inyección de prompt         | 5/5 | 5/5 | +0% (Sin cambios) |
| hc-tsk-15 | Verificación SMS válida     | 4/5 | 5/5 | +20% |

## Conclusión

La estrategia de chunking por encabezados (headers) no mejoró el baseline: A obtuvo 31/50 y B 30/50, por lo que RAG no aumentó la tasa de éxito. Las variantes de chunking fijo (C/F) rindieron peor, en parte por ejecuciones incompletas y errores de API que redujeron muestras. El uso de la herramienta "think" (D) también bajó el rendimiento a 12/50; el JSON configura max_steps=30, por lo que el agente consume pasos en razonamiento y no completa flujos largos. 
Hipótesis: aumentar el límite de pasos y usar chunking basado en encabezados conserva información relevante y permitiría que RAG mejore realmente al baseline.
