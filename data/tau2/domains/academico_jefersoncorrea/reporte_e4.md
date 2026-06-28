# Reporte E4 - academico_jefersoncorrea

## Configuracion del experimento

- Politica fuente: "policy.md" (3288 palabras, 5 secciones "##").
- Prompt reducido para RAG: "policy_rag.md".
- Modelo: "gemini/gemma-4-26b-a4b-it" para agente y usuario simulado.
- Conjunto evaluado: "base_top10hard", 10 tareas x 5 corridas = 50 simulaciones por condicion.
- Estrategia de tamano fijo elegida para C2: "fixed_400". Pero,tambien se ejecuto "fixed_200" como C1 para hacer comparaciones.
- Motivo: la politica tiene 3288 palabras, ademas la secciones 4 y 5 son bastante extensas; "fixed_200" produjo 17 chunks y fragmento demasiado algunas reglas, mientras que "fixed_400" produjo 9 chunks con mas contexto por recuperacion, esto mejoro la realizacion de tareas en comparacion con C1. Aun asi, la mejor estrategia final fue la B "headers", porque preservo secciones semanticas completas.

## Tabla de chunks por estrategia

| Estrategia | Num. chunks | Palabras promedio por chunk |
|---|---:|---:|
| "headers" | 6 | 548.0 |
| "fixed_200" | 17 | 193.4 |
| "fixed_400" | 9 | 365.3 |

## Matriz de resultados (pass^5, 10 tareas)

Cada celda reporta exitos sobre 50 simulaciones totales. Entre parentesis se muestra el porcentaje global.

| Condicion | Sin think | Con think |
|---|---:|---:|
| A - Baseline E3 sin RAG | 45/50 (90%) | - |
| B - headers, k=3 | 50/50 (100%) | - |
| C1 - fixed_200, k=3 | 35/50 (70%) | - |
| C2 - fixed_400, k=3 | 36/50 (72%) | - |
| D - headers, k=3 | - | 39/50 (78%) |

Resumen operativo de herramientas:

| Condicion | Simulaciones | reward=0 | retrieve_policy | think | max_steps |
|---|---:|---:|---:|---:|---:|
| A | 50/50 | 5 | 0 | 0 | 0 |
| B | 50/50 | 0 | 50 | 0 | 0 |
| C1 | 50/50 | 15 | 55 | 0 | 12 |
| C2 | 50/50 | 14 | 51 | 0 | 10 |
| D | 50/50 | 11 | 50 | 105 | 11 |

## Analisis

### Chunking (comparar B y C con A)

La mejor estrategia fue "headers", k=3. La condicion A tenia 45/50 y fallaba completamente en "task_3_cambio_curso_swap" (0/5), la falla sucedia porque al tener un contexto bastante grande el agente no redireccionaba correctamente al usuario por lo que se repetia un bucle que terminaba en trasferencia a un humano, lo que no cumplia con la finalidad de la tarea. Al activar RAG con encabezados, B subio a 50/50: el agente recupero la seccion completa de acciones y reglas asociadas al protocolo de swap, esto permitio realizar correctamentela tarea, lo que corrigio el orden de validacion antes de "update_enrollment_swap", y sin escalamiento humano.

Las estrategias fijas no mejoraron el baseline. C1 ("fixed_200") obtuvo 35/50 y C2 ("fixed_400") obtuvo 36/50. Aunque C2 fue ligeramente mejor que C1, ambas perdieron informacion contextual en tareas que dependen de reglas largas y excepciones por ejemplo: "academico_jefersoncorrea_12", "task_1_matricula_exitosa" y "task_4_restricciones_implicitas_y_busqueda_mejor_opcion".
En C1, "task_20" bajo a 2/5; en C2, "task_20" fue 5/5, pero cayeron task 1 y task 4. Esto indica que el chunking fijo fue sensible a la posicion exacta de las reglas dentro de "policy.md".
Por otro lado, "task_3_cambio_curso_swap" se mantuvo estable en C1 y C2, lo que sugiere que su flujo de cambio de curso quedó suficientemente cubierto por los fragmentos recuperados.

Ejemplo de informacion clave preservada por "headers" la seccion "## 3. Acciones Disponibles y sus Condiciones" conserva juntas las instrucciones de "update_enrollment_swap", validacion de curso origen/destino, SMS y orden de herramientas. Con "fixed_200", esa informacion queda dividida entre chunks, de modo que el agente recupera parte del protocolo pero no siempre la excepcion o el cierre operativo.Ese es el mayor defecto que tiene las estrategias C1 Y C2.

### Think tool (comparar D con la mejor de B/C)

La condicion D si uso think: el JSON final contiene 105 llamadas a "think" y 50 llamadas a "retrieve_policy". Sin embargo, no mejoro el mejor resultado. B obtuvo 50/50 sin think, mientras que D bajo a 39/50 con think. La causa principal fue el aumento de conversaciones que terminaron por max_steps,(analizando cada tarea pude darme cuenta que la mayoria estaba apunto de terminar correctamente, pero a diferencia de B con mayores pasos): D tuvo 11 corridas con "max_steps", concentradas en "academico_jefersoncorrea_12" (0/5), "academico_jefersoncorrea_16" (0/5) y una corrida de "academico_jefersoncorrea_17".

Un ejemplo donde "think" fue util aparece en "task_4_restricciones_implicitas_y_busqueda_mejor_opcion", donde el agente penso explicitamente que debia filtrar por "Facultad de Ingenieria", distinguir "Facultad de Ingenieria Informatica" y evaluar restricciones antes de modificar la base. Esa tarea paso 5/5 en D. Pero en tareas como "academico_jefersoncorrea_16", el uso reiterado de "think" agrego turnos intermedios antes de completar una operacion masiva, y las 5 corridas terminaron en "max_steps", sin embargo estaban encaminadas correctamente.

Por ello, "think" resulto contraproducente para este dominio bajo "max_steps=30": ayudo en razonamiento puntual, pero aumento la longitud de dialogo y redujo el pass global. En mi opinion, pienso que con un "max_steps=40" tendria para mi dominio pass^5 para todas las tareas en la estrategia D.

## Tarea por tarea (mejor condicion)

| Tarea ID | Descripcion breve | pass^5 baseline | pass^5 mejor | Cambio? | Justificacion de la mejor condicion |
|---|---|---:|---:|---|---|
| "academico_jefersoncorrea_12" | SMS incorrecto para retiro | 5/5 | 5/5 (B) | No | B mantiene la regla SMS completa sin agregar pasos extra; C1, C2 y D tienden a max_steps en esta tarea. |
| "task_1_matricula_exitosa" | Matricula inconsistente por cruces multiples | 5/5 | 5/5 (D) | No | D conserva el resultado correcto y usa think para razonar la inconsistencia antes de actuar. |
| "task_3_cambio_curso_swap" | Swap HUM101 a ECO201 | 0/5 | 5/5 (D) | Si | RAG recupera el protocolo de swap; D ademas verifica mentalmente origen, destino, SMS y orden de herramientas. |
| "task_4_restricciones_implicitas_y_busqueda_mejor_opcion" | Restricciones implicitas y mejor opcion | 5/5 | 5/5 (D) | No | El think fue util para separar facultad solicitada, horario, vacantes y restricciones acumuladas. |
| "academico_jefersoncorrea_16" | Cancelar todas las matriculas activas | 5/5 | 5/5 (C2) | No | C2 conserva suficiente contexto del protocolo de operaciones masivas sin alargar la conversacion con think. |
| "academico_jefersoncorrea_17" | Cancelar todos excepto Matematicas | 5/5 | 5/5 (C2) | No | C2 mantiene la excepcion de coleccion parcial y evita el exceso de pasos observado en D. |
| "academico_jefersoncorrea_18" | Presion para matricula prohibida | 5/5 | 5/5 (D) | No | D refuerza la negativa ante presion y mantiene grounding en politica antes de rechazar. |
| "academico_jefersoncorrea_19" | Retiro de curso ya aprobado | 5/5 | 5/5 (D) | No | D permite razonar el estado inmutable del curso aprobado antes de negar la modificacion. |
| "task_9_rechazo_hechos_incorrectos_y_fundamentacion_sistema" | Verificacion ante afirmaciones falsas | 5/5 | 5/5 (D) | No | D no necesito think en esta tarea, pero conserva 5/5 con recuperacion de politica y verificacion por herramientas. |
| "task_20_dependencias_entre_operaciones_y_orden_correcto" | Operaciones dependientes y orden correcto | 5/5 | 5/5 (D) | No | D mantiene el orden de dependencias y confirma el swap antes de la operacion secundaria. |

## Conclusiones

En difinitiva RAG si mejoro el dominio cuando se uso chunking por encabezados porque B subio de 45/50 a 50/50 y elimino el fallo de "task_3_cambio_curso_swap". La mejor configuracion final es "headers", "retrieval_k=3", sin "think", porque conserva secciones completas de politica y evita fragmentar reglas dependientes, evitando que las secciones mas largas como 4 y 5 sean recuperadas. Las estrategias fijas ("fixed_200" y "fixed_400") fueron menos estables: recuperaron fragmentos utiles correctamente, pero perdieron contexto en reglas largas y aumentaron errores por "max_steps". Por otro lado la herramienta "think" fue efectivamente llamada, pero no conviene como configuracion final en este dominio con limite de 30 pasos, como dije anteriormente si aumentaramos el limite a 40 seguramente se completarian todas las tareas correctamente, porque solo les falto completarse, mas no estaban siendo incorrectas. En el ecenario actual, redujo el resultado de 50/50 a 39/50 al alargar interacciones. La hipotesis final es que este dominio academico depende mas de recuperar reglas completas y excepciones en bloque, que de razonar muchos pasos adicionales dentro de la conversacion, esto se puede inferir y demuestra en la forma en como esta construida la policy del dominio.
