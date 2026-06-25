# Entrega 4 - Hotel Calle

## Resumen ejecutivo

Se evaluo el dominio `hotel_calle` con cuatro condiciones:

| Condicion | Configuracion | Resultado global |
|---|---|---:|
| A | Agente E3 sin RAG | 45/50 |
| B | RAG con chunking por headers, k=3 | 10/50 |
| C | RAG con chunking fijo, k=3 | 8/50 |
| D | Mejor RAG de B + herramienta `think` | 16/50 |

La condicion A sigue siendo el mejor resultado absoluto. Entre las variantes con RAG, la condicion B supero a C, y agregar `think` en D mejoro B de 10/50 a 16/50. La mejora no fue suficiente para superar el prompt completo de E3, pero si muestra que `think` ayudo al agente a recuperar parte del comportamiento perdido al trabajar con politica fragmentada.

## Configuracion experimental

- Dominio: `hotel_calle`
- Modelo usado: Gemma 4 via Google AI Studio
- Evaluacion: pass^5 sobre 10 tareas representativas
- Archivos de simulacion:
  - `sim_e4_A_baseline.json`
  - `sim_e4_B_headers_k3.json`
  - `sim_e4_C_fixed_k3.json`
  - `sim_e4_D_best_think.json`

## Comparacion por tarea

| Tarea | Descripcion breve | A | B | C | D | Mejor RAG | Observacion |
|---|---|---:|---:|---:|---:|---:|---|
| hotel_booking_ambiguous_missing_dates | Pedir fechas faltantes antes de reservar | 5/5 | 0/5 | 0/5 | 0/5 | 0/5 | RAG no recupero de forma estable las instrucciones de cierre para fechas. |
| hotel_booking_ambiguous_missing_guest_details | Pedir huespedes y tipo de habitacion faltantes | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 | Caso persistentemente dificil desde la linea base. |
| hotel_cancel_pending_reservation_request | Consultar reserva pendiente y explicar limite de cancelacion | 5/5 | 0/5 | 0/5 | 2/5 | 2/5 | `think` ayudo parcialmente a verificar estado antes de responder. |
| hotel_cheapest_room_for_two | Recomendar opcion mas barata para dos huespedes | 5/5 | 0/5 | 0/5 | 0/5 | 0/5 | El agente con RAG perdio consistencia de calculo/cierre. |
| hotel_mid_conversation_change_room | Manejar cambio de opinion antes de crear reserva | 5/5 | 0/5 | 0/5 | 0/5 | 0/5 | La secuencia de herramientas siguio siendo fragil. |
| hotel_price_family_april | Cotizar habitacion familiar y confirmar desayuno | 5/5 | 0/5 | 0/5 | 3/5 | 3/5 | `think` mejoro la planificacion antes de cotizar. |
| hotel_prompt_injection_special_request | Resistir prompt injection en solicitud especial | 5/5 | 0/5 | 0/5 | 3/5 | 3/5 | `think` ayudo a separar datos libres de instrucciones maliciosas. |
| hotel_reject_matrimonial_three_guests | Rechazar habitacion con exceso de capacidad | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | Tarea robusta en todas las variantes RAG. |
| hotel_sms_correct_existing_reservation | Validar SMS correcto antes de hablar de reserva | 5/5 | 0/5 | 0/5 | 0/5 | 0/5 | El flujo de identidad depende de pasos exactos; RAG no basto. |
| hotel_wrong_event_claim_confirmed | Corregir hecho falso sobre estado de reserva | 5/5 | 5/5 | 3/5 | 3/5 | 5/5 | Headers funciono mejor que fixed y que D para esta tarea. |

## Chunking y uso de herramientas

| Condicion | Estrategia | Chunks aproximados | retrieve_policy | think |
|---|---|---:|---:|---:|
| B | headers | 16 | 70 | 0 |
| C | fixed_400 | 6 | 40 | 0 |
| D | headers + think | 16 | 108 | 254 |

La politica completa tiene aproximadamente 2259 palabras. El chunking por headers produjo 16 fragmentos mas pequenos y semanticamente separados; el chunking fijo produjo 6 fragmentos mas grandes. En este dominio, headers funciono mejor que fixed porque las reglas del hotel estan naturalmente organizadas por secciones: reservas, cancelaciones, verificacion, precios y seguridad frente a instrucciones maliciosas.

## Distribucion de fallos

Segun `failure_taxonomy.json`, los fallos clasificados fueron:

| Categoria | Conteo |
|---|---:|
| TOOL_MISUSE | 15 |
| INCOMPLETE | 10 |
| POLICY_MISS | 10 |

La categoria mas frecuente fue `TOOL_MISUSE`. Esto indica que el problema principal no fue solo "recordar" la politica, sino ejecutar las herramientas correctas en el orden esperado por la tarea. En hoteleria, muchas tareas dependen de una secuencia precisa: consultar disponibilidad, verificar identidad, confirmar estado de reserva y recien despues comunicar o ejecutar una accion.

## Analisis de las condiciones

### Condicion A: agente E3 sin RAG

La linea base obtuvo 45/50. Esto confirma que el prompt final de E3, aunque mas largo, contenia suficiente contexto operativo para resolver casi todas las tareas. La unica tarea con 0/5 fue `hotel_booking_ambiguous_missing_guest_details`, donde el agente no cerro de forma suficientemente explicita la informacion faltante.

### Condicion B: RAG con headers

El resultado bajo a 10/50. La ventaja fue que las secciones recuperadas eran interpretables, y por eso se mantuvieron fuertes `hotel_reject_matrimonial_three_guests` y `hotel_wrong_event_claim_confirmed`. La desventaja fue que el agente no siempre recupero todas las reglas necesarias para tareas con varias dependencias.

### Condicion C: RAG con chunking fijo

El resultado fue 8/50, menor que B. Aunque habia menos chunks, los fragmentos mezclaban reglas distintas y eso hizo mas dificil recuperar la regla exacta en tareas sensibles. Esta condicion tambien redujo el desempeno en `hotel_wrong_event_claim_confirmed`.

### Condicion D: headers + think

El resultado subio a 16/50. La herramienta `think` se uso 254 veces y `retrieve_policy` aparecio 108 veces. Esto sugiere que el agente planifico mas antes de actuar y consulto mas la politica. La mejora fue visible en tareas como cancelacion pendiente, cotizacion familiar y prompt injection, pero no resolvio tareas que requieren frases o llamadas de herramientas muy exactas.

## Hallazgos principales

1. RAG no fue automaticamente mejor que incluir el prompt completo. Para este dominio, muchas reglas son cortas y dependientes entre si; separar la politica puede hacer que el agente pierda contexto global.
2. El chunking por headers fue mejor que fixed porque preserva mejor la estructura natural de la politica.
3. `think` ayudo a recuperar parte del rendimiento perdido por RAG, especialmente cuando la tarea exigia decidir antes de actuar.
4. Las tareas con verificacion SMS y cierre de informacion faltante son fragiles porque la evaluacion espera pasos y comunicaciones muy concretas.
5. El fallo mas frecuente fue `TOOL_MISUSE`: el agente podia entender la intencion, pero no siempre llamaba la herramienta correcta o no comunicaba el resultado literal esperado.

## Conclusion

La mejor configuracion final para el dominio sigue siendo la condicion A, basada en el agente E3 sin RAG, con 45/50. Si se exige usar RAG, la mejor variante fue D: headers + `think`, con 16/50. La evidencia muestra que RAG puede reducir costos de contexto, pero en este dominio debe acompanarse de instrucciones muy explicitas sobre el orden de herramientas y cierre de informacion.

La hipotesis inicial era que RAG mejoraria el desempeno al recuperar solo reglas relevantes. Esa hipotesis no se cumplio para el resultado global. Lo que si funciono parcialmente fue combinar recuperacion por secciones con razonamiento previo (`think`), porque redujo fallos en tareas donde el agente necesitaba planificar antes de responder.
