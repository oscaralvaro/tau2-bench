# Hallazgos acumulados E1-E4 - Sanita Irigoin

## 1. Descripcion del dominio y las tareas

Sanita Irigoin es un dominio de atencion y ventas para insumos agricolas orientados al cultivo de arroz. El agente atiende consultas sobre fertilizantes, herbicidas y plaguicidas; verifica stock; recomienda productos segun diagnostico de suelo; procesa pedidos; aplica reglas de pago; verifica identidad por SMS para operaciones sensibles; y escala a un humano cuando el caso esta fuera del alcance.

El dominio contiene 25 tareas. Cubren consultas simples, creacion de pedidos, pago al contado, credito, productos sin stock, recomendaciones, consultas de pedidos, solicitudes fuera de dominio, presion del usuario, prompt injection, cambio de opinion, verificacion SMS y operaciones masivas. La entrega E4 se concentro en las 10 tareas de menor senal del baseline E3: 2, 3, 5, 13, 15, 16, 21, 22, 23 y 24.

Simulaciones reales usadas para este analisis:

- E1: `sim_baseline_pass1.json`, 25 simulaciones pass^1.
- E2: `sim_baseline_pass5.json`, 125 simulaciones pass^5.
- E3/E4 A: `sim_e4_A_baseline.json`, 50 simulaciones sobre el subconjunto E4.
- E4 B: `sim_e4_B_headers_k3.json`, 50 simulaciones.
- E4 C: `sim_e4_C_fixed_k3.json`, 50 simulaciones.
- E4 D: `sim_e4_D_best_think.json`, 50 simulaciones.

Total considerado en E1-E4: 350 simulaciones reales, contando las condiciones E4 y los archivos historicos usados como comparacion. Para la tabla de evolucion se usa el mismo subconjunto de 10 tareas de E4.

## 2. Evolucion del agente a lo largo de las entregas

E1 uso pass^1, por lo que no es directamente comparable con E2-E4. E2, E3 y E4 usan pass^5. En la tabla, para E2-E4 reporto el numero de tareas que pasaron 5/5 sobre las 10 tareas E4; entre parentesis incluyo rewards brutos.

| Entrega | Cambio principal | Metrica | Resultado | Delta vs E3 |
|---------|------------------|---------|-----------|-------------|
| E1 | Baseline inicial | pass^1 | 9/10 en el subconjunto E4 | - |
| E2 | Politica y prompt inicial con pass^5 | pass^5 | 7/10 tareas 5/5; 35/50 rewards | - |
| E3 | Prompt engineering para cambio de opinion y SMS | pass^5 | 9/10 tareas 5/5; 45/50 rewards | - |
| E4 | RAG `fixed_200`, k=3 | pass^5 | 8/10 tareas 5/5; 48/50 rewards | -1 tarea perfecta vs E3 |

La lectura principal es que E4 no supera a E3 en estabilidad perfecta, pero si mejora dos puntos importantes del subconjunto: tarea 21 sube de 1/5 a 4/5 con `fixed_200`, y tarea 22 sube de 4/5 a 5/5. Al mismo tiempo, RAG introduce una pequena perdida en tarea 5, donde C baja de 5/5 a 4/5.

## 3. Categorias de fallo mas frecuentes

### TOOL_ARGUMENT_ERROR

El modelo usa argumentos que no coinciden con el contrato de las herramientas. Es el fallo mas claro en tareas de pedido porque `create_order` distingue `metodo_pago` de `estado_pago`: `metodo_pago` debe ser `efectivo` o `transferencia`, y `estado_pago` debe ser `al contado`, `credito` o `cuotas`.

Ejemplo real de D, tarea 3:

```text
assistant TOOL create_order:
{"user_id":"U003","metodo_pago":"credito","producto_id":"P002","cantidad":5,"estado_pago":"pendiente"}
tool:
{"error":"Metodo de pago invalido. Use 'efectivo' o 'transferencia'."}
assistant TOOL create_order:
{"user_id":"U003","metodo_pago":"transferencia","producto_id":"P002","cantidad":5,"estado_pago":"pendiente"}
tool:
{"error":"Estado de pago invalido. Use 'al contado', 'credito' o 'cuotas'."}
termination_reason: max_steps
```

Evolucion: los docstrings de E3 ayudaron a reducir errores de producto_id, pero E4 muestra que los argumentos de pago siguen siendo fragiles. Think identifico el error, pero no siempre corrigio todo antes de agotar pasos.

### PRODUCT_ID_MISS

El agente a veces usa el nombre comercial del producto donde la herramienta exige el ID interno. Este fue el problema central de la tarea 21 en el baseline. Ejemplo real de A, tarea 21:

```text
assistant TOOL check_stock: {"producto_id":"NPK 20-20-20"}
tool: {"error":"Producto 'NPK 20-20-20' no encontrado."}
assistant:
Lo siento, no pude encontrar el producto "NPK 20-20-20"... podrias proporcionarme el codigo del producto?
user:
No tengo el codigo del producto...
assistant TOOL escalate_to_human:
{"motivo":"El cliente desea comprar NPK 20-20-20 pero no conoce el codigo del producto..."}
```

Evolucion: E4 C mejora mucho este caso. Con `fixed_200`, tarea 21 pasa de 1/5 en A a 4/5. Un trial exitoso recupera el flujo correcto: ante el cambio a NPK 20-20-20, llama `check_stock(producto_id="P002")` y luego `create_order(producto_id="P002")`.

### LOOP_OR_MAX_STEPS

Algunas fallas no ocurren porque el agente desconozca la politica, sino porque se demora demasiado: hace consultas repetidas a RAG, pregunta confirmaciones adicionales o reintenta herramientas con argumentos parcialmente corregidos. En B, tarea 13 falla con `termination_reason: max_steps` despues de varias llamadas a `retrieve_policy` intentando encontrar catalogo e IDs.

Ejemplo real de B, tarea 13:

```text
assistant TOOL retrieve_policy: {"query":"todos los productos disponibles y sus IDs"}
tool: ## Proceso de Atencion ... ## Ejemplo Few-Shot ...
assistant TOOL retrieve_policy: {"query":"lista de IDs de productos"}
tool: ## Regla de Cambio de Opinion ... ## Checklist Interno ...
termination_reason: max_steps
```

Evolucion: `fixed_200` reduce esta categoria frente a `headers`, pero no la elimina. La condicion D incluso empeora algunos casos porque las llamadas `think` consumen pasos adicionales.

### POLICY_RETRIEVAL_GAP

RAG puede recuperar texto relevante pero incompleto. La politica mezcla catalogo, procesos, excepciones y ejemplos few-shot. Con `headers`, el agente a veces recibe secciones utiles pero no la combinacion completa para actuar. Esto explica por que B tiene 6/10 tareas perfectas mientras C sube a 8/10.

Evolucion: `fixed_200` parece mejor porque incluye ventanas mas largas y mezcla reglas cercanas. Para este dominio pequeno, los chunks de 200 palabras dan suficiente contexto sin perder demasiada precision.

### SMS_FLOW_DELAY

El flujo SMS requiere varios pasos: identificar usuario, verificar que corresponde una operacion sensible, enviar codigo, pedirlo, verificarlo y solo despues crear pedido. E3 ya habia mejorado este flujo, y E4 C lo estabilizo en tarea 22: 5/5. Sin embargo, cuando se combina con errores de pago o confirmaciones, todavia puede contribuir a `max_steps`.

Ejemplo real de D, tarea 3:

```text
assistant TOOL send_sms_code: {"user_id":"U003"}
tool: {"mensaje":"Codigo SMS enviado al usuario U003.","codigo_enviado":"885192"}
assistant TOOL verify_sms_code: {"codigo":"885192","user_id":"U003"}
tool: {"verificado":"True",...}
assistant TOOL create_order: ... argumentos de pago invalidos ...
```

El SMS se ejecuta bien, pero el pedido falla despues por argumentos incorrectos.

## 4. Comportamiento especifico de Gemma 4 en el dominio

Gemma 4 31B puede seguir politicas operativas y usar herramientas, pero es sensible a contratos estrictos. Cuando la accion requiere mapear lenguaje natural a argumentos exactos, los errores se concentran en IDs, pago y estados. En tarea 21, el baseline A muestra que el modelo no siempre convierte "NPK 20-20-20" a `P002`; usa el nombre comercial en `check_stock` y termina escalando a humano. Con RAG `fixed_200`, ese problema mejora porque la ventana recuperada suele incluir la regla de catalogo o el ejemplo few-shot de cambio de opinion.

Primer ejemplo concreto: cambio de opinion. En C, tarea 21, el agente responde correctamente:

```text
user:
En realidad, en vez de Urea 46%, quiero NPK 20-20-20...
assistant TOOL check_stock:
{"producto_id":"P002"}
tool:
{"producto_id":"P002","stock_actual":"30","disponible":"True"}
assistant TOOL create_order:
{"producto_id":"P002","user_id":"U001","estado_pago":"al contado","metodo_pago":"efectivo","cantidad":3}
```

Segundo ejemplo concreto: razonamiento con think. En D, tarea 2, el agente llama:

```text
assistant TOOL retrieve_policy:
{"query":"pedido de Urea 46% al contado"}
assistant TOOL think:
{"thought":"The user wants to order 3 units of Urea 46%... product ID P001... check stock... explicit confirmation... SMS verification is not required."}
```

Este uso es correcto: think organiza el procedimiento antes de crear el pedido. Sin embargo, el resultado agregado de D no supera a C. Hubo 79 llamadas a `think`, 63 a `retrieve_policy`, y 34/50 simulaciones usaron think al menos una vez, pero D quedo en 7/10 tareas perfectas frente a 8/10 de C. La conclusion es que Gemma 4 puede razonar explicitamente, pero el razonamiento no garantiza adherencia perfecta a esquemas de herramientas.

En conversaciones de mas de 10 turnos, Gemma tiende a hacer pasos adicionales de seguridad. Eso es positivo para evitar pedidos sin confirmacion, pero puede producir loops o `max_steps`, sobre todo cuando ya hubo un error de herramienta. Para produccion, no basta con prompt/RAG: se necesitan validadores o wrappers que conviertan pagos e IDs a valores validos antes de llamar herramientas de escritura.

## 5. Recomendaciones para un sistema de produccion

Gemma 4 no es suficientemente confiable para operar sin supervision humana en todo el dominio. Puede automatizar consultas informativas, verificacion de stock, pedidos simples al contado y flujos SMS cuando el producto y metodo de pago estan claros. No deberia operar sin guardrails en pedidos a credito, cambios de opinion, productos sin stock, operaciones masivas o casos donde un error de herramienta podria crear un pedido incorrecto.

Para produccion, recomendaria:

- Mantener RAG `fixed_200` o una estrategia similar, porque mejora los casos dificiles sin requerir meter toda la politica en el prompt.
- Agregar validacion programatica de argumentos antes de `create_order`: mapear `metodo_pago` y `estado_pago` a enums validos, rechazar combinaciones imposibles y pedir aclaracion si faltan datos.
- Agregar una capa deterministica de catalogo: resolver nombres como "Urea 46%" y "NPK 20-20-20" a `P001` y `P002` antes de que el LLM elija argumentos.
- Mantener SMS como precondicion dura para credito y pedidos de mas de 8 unidades; no depender solo del prompt.
- Escalar automaticamente cuando una herramienta devuelve dos errores consecutivos o cuando la conversacion se acerca al limite de pasos.

Umbrales recomendados:

- Consultas informativas: minimo 4/5 por tarea.
- Pedidos simples al contado: 5/5 antes de automatizar sin supervision.
- Credito, SMS, cambios de producto y operaciones masivas: 5/5 con validadores externos, no solo con LLM.

La mejor condicion E4 fue C (`fixed_200`, k=3), con 8/10 tareas perfectas y 48/50 rewards. Aun asi, el baseline E3 tuvo 9/10 tareas perfectas. Por tanto, RAG fue util para corregir puntos especificos, pero no reemplaza prompt engineering ni validaciones de herramientas en un sistema real.
