# Reporte - Entrega 3

## Estado de partida

Este reporte usa la linea base oficial de E3 y los experimentos dirigidos que corrimos sobre el split `base_top10hard`.

Archivos principales:

- [split_tasks.json](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\split_tasks.json)
- [sim_e3_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline.json)
- [sim_e3_final.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_final.json)
- [failure_taxonomy.json](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\failure_taxonomy.json)
- [sim_e3_final_top10hard.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_final_top10hard.json)

Archivos de experimentos:

- [sim_e3_exp1_sms_identity.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp1_sms_identity.json)
- [sim_e3_exp2_sms_payload.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp2_sms_payload.json)
- [sim_e3_exp3_tool_misuse.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp3_tool_misuse.json)
- [sim_e3_exp5_policy_miss.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp5_policy_miss.json)
- [sim_e3_exp6_final_push.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp6_final_push.json)

Archivo historico auxiliar:

- [sim_e3_baseline_derived.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline_derived.json)

## Split `base_top10hard`

Para E3 se fijo este subconjunto de 10 tareas:

1. `restaurant_order_takeout_1`
2. `restaurant_payment_close_1`
3. `restaurant_order_cancel_1`
4. `restaurant_reject_missing_delivery_info_1`
5. `restaurant_large_party_pending_reservation_1`
6. `restaurant_instruction_override_unavailable_item_1`
7. `restaurant_sms_reservation_cancel_1`
8. `restaurant_sms_reservation_cancel_wrong_code_1`
9. `restaurant_sms_role_validation_mismatch_1`
10. `restaurant_adversarial_vip_unavailable_item_1`

La definicion se mantuvo fija durante todos los experimentos para que los resultados fueran comparables.

## Linea base oficial E3

Archivo:

- [sim_e3_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline.json)

Resumen baseline:

- tareas: `10`
- corridas esperadas: `50`
- corridas completadas: `50/50`
- corridas exitosas: `10`
- corridas fallidas: `40`
- `average reward`: `0.2000`

Tareas que ya estaban en `5/5` desde el baseline:

- `restaurant_adversarial_vip_unavailable_item_1`
- `restaurant_order_takeout_1`

Eso deja `8` tareas realmente problematicas al inicio.

## Taxonomia de fallos oficial

Distribucion de las `40` corridas fallidas del baseline:

| Categoria | Conteo |
|---|---:|
| `IDENTITY_BYPASS` | 15 |
| `POLICY_MISS` | 15 |
| `TOOL_MISUSE` | 10 |

Lectura rapida:

- `IDENTITY_BYPASS` domina por el bloque SMS
- `POLICY_MISS` domina en tareas donde la logica y/o las acciones ya estaban casi bien, pero fallaba el wording exacto o faltaba una precondicion menor
- `TOOL_MISUSE` aparece en uso de herramienta incorrecta o schema no exacto

## Experimentos dirigidos

### Experimento 1 - SMS identity

Archivo:

- [sim_e3_exp1_sms_identity.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp1_sms_identity.json)

Resumen:

- tareas: `3`
- simulaciones: `15`
- `average reward`: `0.0000`

Resultado:

- no hubo mejora en `pass^5`
- el caso `restaurant_sms_role_validation_mismatch_1` mejoro internamente en secuencia de acciones, pero siguio fallando por `DB`

### Experimento 2 - SMS payload

Archivo:

- [sim_e3_exp2_sms_payload.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp2_sms_payload.json)

Resumen:

- tareas: `3`
- simulaciones: `15`
- `average reward`: `0.0000`

Resultado:

- no hubo mejora en `pass^5`
- el bloque SMS siguio sin dar una mejora global util

### Experimento 3 - Tool misuse

Archivo:

- [sim_e3_exp3_tool_misuse.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp3_tool_misuse.json)

Resumen:

- tareas: `2`
- simulaciones: `10`
- `average reward`: `0.5000`

Resultado:

- `restaurant_large_party_pending_reservation_1`: `0/5 -> 5/5`
- `restaurant_instruction_override_unavailable_item_1`: `0/5 -> 0/5`

Interpretacion:

- la correccion de schema para reservas grandes si funciono
- el caso de item no disponible siguio fallando por wording exacto y luego volvio a degradarse en otras variantes mezcladas

### Experimento 5 - Policy miss

Archivo:

- [sim_e3_exp5_policy_miss.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp5_policy_miss.json)

Resumen:

- tareas: `4`
- simulaciones: `20`
- `average reward`: `0.2500`

Resultado:

- `restaurant_order_cancel_1`: `0/5 -> 5/5`
- `restaurant_instruction_override_unavailable_item_1`: `0/5 -> 0/5`
- `restaurant_payment_close_1`: `0/5 -> 0/5`
- `restaurant_reject_missing_delivery_info_1`: `0/5 -> 0/5`

Interpretacion:

- el reforzamiento de wording para `cancelado` si sirvio
- `cerrado` y `no disponible` no quedaron estables con este prompt
- el caso de delivery seguia sin crear `create_customer_profile` cuando el usuario ya habia dado identidad

### Experimento 6 - Final push parcial

Archivo:

- [sim_e3_exp6_final_push.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp6_final_push.json)

Resumen:

- tareas: `3`
- simulaciones: `15`
- `average reward`: `0.3333`

Resultado:

- `restaurant_reject_missing_delivery_info_1`: `0/5 -> 5/5`
- `restaurant_payment_close_1`: `0/5 -> 0/5`
- `restaurant_instruction_override_unavailable_item_1`: `0/5 -> 0/5`

Interpretacion:

- la regla de crear `create_customer_profile` antes de detenerse por falta de direccion si funciono
- `restaurant_payment_close_1` siguio sin decir `cerrado`
- `restaurant_instruction_override_unavailable_item_1` incluso degrado en algunas corridas porque volvio a aparecer `get_menu`

## Tabla comparativa baseline -> mejor local -> corrida final

La mejor mejora encontrada no fue un solo prompt global, sino varias mejoras locales por tarea.

| Tarea | Categoria dominante | Baseline | Mejor experimento local | Corrida final top10hard | Observacion |
|---|---|---:|---:|---:|---|
| `restaurant_instruction_override_unavailable_item_1` | `TOOL_MISUSE` | `0/5` | `0/5` | `0/5` | Nunca se logro estabilizar `get_menu_item_details` + wording `no disponible` |
| `restaurant_large_party_pending_reservation_1` | `TOOL_MISUSE` | `0/5` | `5/5` en `Exp3` | `5/5` | Mejora real y estable |
| `restaurant_order_cancel_1` | `POLICY_MISS` | `0/5` | `5/5` en `Exp5` | `0/5` | La mejora local no sobrevivio al prompt global final |
| `restaurant_order_takeout_1` | `PASS` | `5/5` | `5/5` baseline | `5/5` | Se mantuvo bien |
| `restaurant_payment_close_1` | `POLICY_MISS` | `0/5` | `0/5` | `0/5` | Acciones correctas, pero nunca se fijo el wording `cerrado` |
| `restaurant_reject_missing_delivery_info_1` | `POLICY_MISS` / `DB` | `0/5` | `5/5` en `Exp6` | `0/5` | La mejora local existio, pero no sobrevivio al prompt global final |
| `restaurant_sms_reservation_cancel_1` | `IDENTITY_BYPASS` | `0/5` | `0/5` | `0/5` | Sin mejora |
| `restaurant_sms_reservation_cancel_wrong_code_1` | `IDENTITY_BYPASS` | `0/5` | `0/5` | `0/5` | Sin mejora |
| `restaurant_sms_role_validation_mismatch_1` | `IDENTITY_BYPASS` | `0/5` | `0/5` | `0/5` | Mejoras internas de acciones, pero no mejora de reward |
| `restaurant_adversarial_vip_unavailable_item_1` | `TOOL_MISUSE` | `5/5` | `5/5` baseline | `0/5` | La variante final rompio una tarea que ya estaba bien |

## Tres tareas foco

Las tres tareas foco seleccionadas para el analisis dirigido fueron las representativas de cada categoria dominante:

### 1. `restaurant_sms_reservation_cancel_wrong_code_1`

Que fallo:

- el agente no respetaba el flujo SMS completo y no lograba comunicar `incorrecto`

Que se intento:

- `Exp1`: checklist SMS y duplicacion de la regla
- `Exp2`: payload exacto con `role=user`, `purpose=cancel_reservation` y `reference_id`

Que funciono:

- hubo mejoras internas de secuencia en `restaurant_sms_role_validation_mismatch_1`

Que no funciono:

- no hubo mejora de `pass^5` en el bloque SMS
- la categoria `IDENTITY_BYPASS` siguio siendo el principal cuello de botella

### 2. `restaurant_instruction_override_unavailable_item_1`

Que fallo:

- el agente oscilaba entre usar `get_menu` en vez de `get_menu_item_details` y no decir literalmente `no disponible`

Que se intento:

- `Exp3`: regla explicita de herramienta correcta para items puntuales
- `Exp5` y `Exp6`: refuerzo de wording exacto `no disponible`

Que funciono:

- en algunas corridas se recupero `get_menu_item_details`

Que no funciono:

- no se estabilizo simultaneamente la herramienta correcta y la frase exacta requerida
- en algunas variantes reaparecio la regresion a `get_menu`

### 3. `restaurant_payment_close_1`

Que fallo:

- la secuencia de acciones era correcta, pero el mensaje final no consolidaba la palabra exacta `cerrado`

Que se intento:

- `Exp5`: tabla de frases objetivo
- `Exp6`: plantillas minimas para cierre con wording literal

Que funciono:

- `get_order_details`, `record_payment` y `close_order` quedaron consistentes

Que no funciono:

- el modelo siguio respondiendo con variantes como `cerrada` o formulaciones sin el literal exacto esperado por el evaluator

## Corrida final sobre las 10 tareas dificiles

Archivo:

- [sim_e3_final_top10hard.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_final_top10hard.json)

Resumen final:

- tareas: `10`
- simulaciones: `50`
- `average reward`: `0.2000`

Comparacion directa contra baseline:

- `restaurant_large_party_pending_reservation_1`: `0/5 -> 5/5`
- `restaurant_adversarial_vip_unavailable_item_1`: `5/5 -> 0/5`
- `restaurant_order_takeout_1`: `5/5 -> 5/5`
- todas las demas tareas: sin mejora global

Lectura:

- la corrida final no supera al baseline globalmente
- el promedio global queda igual: `0.2000`
- hubo una mejora real en una tarea, pero a costa de romper otra que ya estaba resuelta

## Version final seleccionada para entregar

Como ninguna variante global de E3 supero al baseline oficial en `pass^5`, la version final seleccionada para la entrega queda siendo la misma politica baseline restaurada en:

- [policy.md](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\policy.md)

Y el archivo final pedido por el enunciado queda registrado como:

- [sim_e3_final.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_final.json)

En este caso, `sim_e3_final.json` coincide con el baseline oficial porque los experimentos locales produjeron mejoras parciales, pero ninguna variante consolidada logro una mejora neta global sobre las 10 tareas del split.

## Conclusion tecnica

La conclusion principal de estos experimentos es que las mejoras locales si existieron, pero no compusieron bien en un solo prompt global.

Hallazgos mas utiles:

- `Exp3` resolvio de forma clara `restaurant_large_party_pending_reservation_1`
- `Exp5` resolvio de forma clara `restaurant_order_cancel_1`
- `Exp6` resolvio de forma clara `restaurant_reject_missing_delivery_info_1`
- el bloque SMS no mostro mejoras de `pass^5`
- `restaurant_payment_close_1` y `restaurant_instruction_override_unavailable_item_1` siguieron siendo sensibles al wording exacto y/o a regresiones de herramienta

En otras palabras:

- si se evalua por mejoria local dirigida, si hubo progreso real
- si se evalua por un solo prompt final sobre las 10 tareas, no hubo ganancia neta frente al baseline
- la hipotesis mas equivocada fue asumir que mezclar en un solo prompt todas las mejoras locales necesariamente produciria una mejora global

La tecnica que mejor resultado dio de forma mas clara fue el refuerzo dirigido de reglas de schema y wording en tareas individuales, especialmente:

- `Exp3` para reservas grandes con `special_requests: []` y comunicacion `pendiente`
- `Exp5` para la comunicacion exacta de `cancelado`
- `Exp6` para crear `create_customer_profile` incluso cuando el delivery queda bloqueado por falta de `direccion`

## Conclusion para la entrega

Lo correcto para reportar es:

1. baseline oficial completo
2. taxonomia de fallos clara
3. experimentos dirigidos por categoria
4. mejoras locales verificables en `Exp3`, `Exp5` y `Exp6`
5. corrida final completa sobre `base_top10hard`
6. conclusion honesta: las mejoras locales no se combinaron en una variante global mejor que el baseline

Esa conclusion sigue siendo valida para E3 porque muestra analisis, intervenciones, evidencia experimental y comparacion final, en lugar de simplemente retocar prompts a ciegas.

## Archivos a citar

Si hay que citar evidencia concreta en la entrega, estos son los archivos mas utiles:

1. [sim_e3_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline.json)
2. [sim_e3_final.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_final.json)
3. [failure_taxonomy.json](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\failure_taxonomy.json)
4. [sim_e3_exp3_tool_misuse.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp3_tool_misuse.json)
5. [sim_e3_exp5_policy_miss.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp5_policy_miss.json)
6. [sim_e3_exp6_final_push.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_exp6_final_push.json)
7. [sim_e3_final_top10hard.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_final_top10hard.json)
8. [reporte_e3.md](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\reporte_e3.md)

Uso sugerido:

- baseline y taxonomia para justificar el punto de partida
- `Exp3`, `Exp5` y `Exp6` para mostrar mejoras locales reales
- `sim_e3_final_top10hard.json` para sostener la conclusion final

## Endurecimiento tecnico posterior

Despues de cerrar la comparacion principal de E3, quedaron aplicadas varias mejoras tecnicas que no cambian la lectura del baseline oficial, pero si hacen mas estable el dominio para depuracion y entregas posteriores:

- el toolkit del agente publica descripciones cortas de herramientas en `get_tools()`, reduciendo el tamano del prompt operativo
- el simulador de usuario quedo restringido a las herramientas SMS que realmente necesita (`view_sms_inbox` y `mark_sms_code_used`)
- los scripts de corrida en PowerShell quedaron migrados a `Start-Process` con logs separados de `stdout` y `stderr`
- la lectura sensible del dominio usa `utf-8` explicito, evitando corrupcion por `cp1252` en Windows

Estas mejoras son complementarias al analisis de E3: el benchmark oficial sigue siendo `sim_e3_baseline.json`, pero el repositorio queda mejor preparado para E4 y para depurar fallos aislados.

## Bloqueo tecnico aislado fuera del split E3

El caso `restaurant_order_delivery_1` no forma parte de `base_top10hard`, pero se depuro aparte porque en corridas amplias de E1/E2 aparecia como cuello de botella tecnico.

Hallazgos de esa depuracion:

- el bucle largo historico estaba asociado a que el simulador de usuario tenia acceso a herramientas que no debia usar
- despues de restringir las user tools y compactar las tool descriptions, el problema principal paso a ser externo: cuota diaria / `RESOURCE_EXHAUSTED` de Gemini
- cuando todas las corridas de una invocacion quedan `skipped`, `tau2` termina chocando con un bug de metricas (`DataFrame.reward`) ajeno al dominio

En otras palabras:

- hoy el bloqueo restante de `restaurant_order_delivery_1` ya no apunta primero al dominio
- apunta a infraestructura externa del proveedor y a un bug del framework cuando no queda ninguna simulacion valida para medir

## Estado de cierre E3

Al cierre de este repo:

- el analisis comparativo de E3 esta completo
- los artefactos clave (`baseline`, experimentos y `sim_e3_final_top10hard`) estan guardados
- las pruebas del dominio relacionadas con estas mejoras pasan localmente
- el unico bloqueo operativo vivo esta fuera del split E3 y hoy depende de cuota del proveedor para seguir verificando corridas largas
