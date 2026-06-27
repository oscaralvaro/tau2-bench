# Hallazgos acumulados E1-E4 - Divemotor Santiago

Autor: Santiago Nunez Arcaya

## 1. Descripcion del dominio y las tareas

El dominio representa la atencion comercial de Divemotor Santiago para clientes personales y empresariales. El agente consulta vehiculos, valida presupuesto y stock, crea cotizaciones y ejecuta operaciones sensibles como aprobar cotizaciones, crear pedidos y cancelar pedidos. Estas acciones modifican una base estructurada y por eso deben apoyarse en herramientas y verificacion de identidad.

El conjunto evoluciono de 10 tareas iniciales a 20 tareas. Los escenarios incorporan consultas, cotizaciones, pedidos, presion emocional, afirmaciones falsas, prompt injection, operaciones parciales, solicitudes fuera de alcance y verificacion SMS correcta e incorrecta.

Entrega 4 reutiliza diez tareas dificiles de E3: 1, 3, 7, 10, 11, 12, 14, 15, 18 y 19. El objetivo fue evaluar si un agente con RAG y una herramienta `think` podia corregir los fallos observados previamente.

## 2. Evolucion del agente a lo largo de las entregas

E1 uso una evaluacion inicial de dominio, por lo que no es directamente comparable con pass^5. Las comparaciones mas limpias son E3 y E4 sobre el mismo subconjunto de diez tareas.

| Entrega | Cambio principal | Metrica usada | Resultado sobre subconjunto E4 |
| --- | --- | --- | ---: |
| E1 | Dominio, datos, herramientas y tareas iniciales | pass^1 | No comparable directamente |
| E2 | Tareas adversarias, SMS y prompt engineering | pass^5 | No recalculado aqui sobre el mismo subconjunto |
| E3 | Taxonomia de fallos e iteraciones del prompt | pass^5 | 30/50 |
| E4-B | RAG por encabezados, k=3 | pass^5 | 31/50 |
| E4-C | RAG por chunks `fixed_200`, k=3 | pass^5 | 30/50 |
| E4-D | RAG por encabezados + `think` | pass^5 | 24/50 |

La mejor condicion de E4 fue B. La mejora agregada sobre E3 fue de 1 corrida sobre 50, aunque por tarea se observan cambios importantes.

## 3. Categorias de fallo mas frecuentes

### Sobre-ejecucion de flujo comercial

En E3 varias tareas fallaban porque el agente avanzaba mas alla de lo pedido. Por ejemplo, despues de cotizar podia intentar SMS, aprobacion o pedido. E4 con RAG ayudo en tareas como la 3 y la 14 cuando recupero reglas que separaban "aprobar cotizacion" de "crear pedido".

Evidencia de E4:

- Tarea 3: A fallo 0/5; B y C lograron 5/5.
- Tarea 14: A fallo 0/5; B y C lograron 5/5.

### Fragilidad ante identidad, rol y SMS

Las tareas 11 y 15 empeoraron con RAG. El baseline las resolvia 5/5, pero B, C y D terminaron 0/5. Esto indica que recuperar politica no basta cuando el agente debe manejar datos de identidad, rol, codigo correcto o codigo incorrecto sin alargar demasiado la conversacion.

Evidencia de E4:

- Tarea 11: A 5/5; B 0/5; C 0/5; D 0/5.
- Tarea 15: A 5/5; B 0/5; C 0/5; D 0/5.

### Prompt injection y persistencia del usuario

La tarea 12 fue el caso mas costoso durante la ejecucion. Con B solo paso 1/5; con C y D fue 0/5. En C se tuvo que recuperar la tarea por separado porque las conversaciones se extendian hasta `max_steps`.

La falla no fue aceptar directamente la instruccion maliciosa, sino quedarse en un flujo largo de aclaraciones, busquedas o verificaciones sin cerrar la respuesta requerida por la tarea.

### Uso excesivo de `think`

D agrego `think` sobre la mejor estrategia B, pero bajo de 31/50 a 24/50. Hubo 214 llamadas a `think` y 26 terminaciones por `max_steps`. Esto sugiere que, en este dominio, `think` sirvio como registro de razonamiento pero no como mejora de desempeno.

## 4. Comportamiento especifico de Gemma 4 en el dominio

Gemma 4 mostro dos patrones relevantes:

1. Puede corregir fallos si recupera una regla muy concreta. Esto se vio en tareas 3, 7 y 14, donde B paso de 0/5 a 5/5 frente al baseline.
2. Puede perder eficiencia cuando tiene demasiadas herramientas o pasos intermedios. Esto se vio en D, donde `think` aumento la cantidad de turnos y produjo mas `max_steps`.

Ejemplos reales de consultas `retrieve_policy` registradas en E4:

- "Cuales son los requisitos para aprobar una cotizacion?"
- "Es posible realizar pedidos especiales de vehiculos que no estan en el catalogo o sugerir vehiculos similares?"
- "Que debo hacer si un cliente quiere aprobar una cotizacion pero no tiene el ID de la cotizacion, solo su ID de cliente?"

Ejemplo real de uso de `think` en D:

- El agente enumero que el cliente queria cotizar, que encontro el vehiculo `v1`, que necesitaba `cliente_id` y que debia comprobar presupuesto y stock antes de crear la cotizacion.

Ese tipo de pensamiento fue util para auditar la conversacion, pero no evito los fallos de cierre en tareas largas.

## 5. Recomendaciones para una siguiente iteracion

- Mantener RAG por encabezados como estrategia base, porque fue la mejor condicion observada.
- No usar `think` de forma obligatoria en cada flujo. Conviene limitarlo a operaciones sensibles o casos con dependencias reales.
- Agregar reglas de cierre mas directas: despues de cumplir la accion exacta, responder y detenerse.
- Reforzar tareas 11, 12, 15 y 19 con instrucciones especificas o ejemplos, porque fueron fallos persistentes bajo RAG.
- Evitar recuperar demasiados fragmentos si no son necesarios. Mas recuperacion no implico mejor resultado: C hizo 71 llamadas a `retrieve_policy`, pero no supero a B.

## 6. Resumen final

La entrega 4 confirma que RAG mejora algunos errores de conocimiento o recuperacion de politica, pero tambien introduce nuevos riesgos de longitud y sobre-procedimiento. En Divemotor Santiago, la mejor configuracion fue RAG por encabezados con `k=3` y sin `think`, con 31/50. La herramienta `think` debe tratarse como ayuda de depuracion o razonamiento puntual, no como mejora automatica de rendimiento.
