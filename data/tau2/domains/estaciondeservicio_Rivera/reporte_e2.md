# Reporte del dominio estaciondeservicio_Rivera

Nombre: Diego Eduardo Rivera Rodriguez

## 1. Resumen del dominio

El dominio `estaciondeservicio_Rivera` simula un bot de atencion al cliente B2B para una estacion de servicio que recibe y procesa solicitudes de delivery de combustible para empresas. El agente atiende consultas de stock, registro de clientes, pedidos de combustible y lubricantes, cambios de metodo de pago, pagos, facturacion virtual, reclamos, cancelaciones y escalamiento a asesores humanos.

Entidades principales:

- Cliente: empresa con RUC, contacto, telefono, correo, direccion fiscal, direcciones de entrega y correo de facturacion.
- Item: producto disponible, como combustible o lubricante, con precio, unidad de medida y stock.
- Orden: pedido de delivery con cliente, producto, cantidad, fecha programada, metodo de pago y estados de pedido/pago.
- Metodo de pago: efectivo, transferencia bancaria o linea de credito.
- Pago: transaccion registrada contra una orden.
- Factura virtual: estado de emision y correo de envio.
- Reclamo: caso asociado a un cliente y, opcionalmente, una orden.
- Verificacion SMS: codigo de validacion para operaciones sensibles.

Resumen de policy:

- Los pedidos de combustible deben respetar stock, minimo de galones y anticipacion.
- Las acciones de escritura requieren confirmacion explicita del usuario.
- Las operaciones sensibles configuradas con SMS requieren enviar codigo, leerlo con la herramienta del usuario y verificarlo antes de continuar.
- Si el codigo SMS es incorrecto, no se ejecuta la operacion sensible ni se reintenta salvo pedido explicito del usuario.
- Los pagos deben realizarse en una sola transaccion completa y con el metodo seleccionado para la orden.
- Las cancelaciones solo proceden sobre ordenes pendientes y dentro de las reglas del dominio.
- Si la politica no permite resolver el caso o el usuario pide atencion humana, se transfiere a un asesor.

## 2. Archivos de simulacion usados

- Corrida total inicial incompleta: `data/simulations/simulacion_estaciondeservicio_Rivera_pass9_Incompleta.json`
- Corrida parcial corregida: `data/simulations/rivera_tasks_corregidas_pass5_v2.json`
- Corridas posteriores de corroboracion: `data/simulations/rivera_tasks_corregidas_pass5_v4.json` y `data/simulations/rivera_tasks_corregidas_pass5_v5.json`
- Corrida final focalizada sobre las 3 tareas mas fragiles: `data/simulations/rivera_peores3_pass10_v1.json`
- Seleccion guardada de las 10 tareas mas dificiles: `data/tau2/domains/estaciondeservicio_Rivera/top10_tareas_dificiles.json`
- Prompt experimental 1: `data/tau2/domains/estaciondeservicio_Rivera/prompts/policy_exp1.md`
- Prompt experimental 2: `data/tau2/domains/estaciondeservicio_Rivera/prompts/policy_exp2.md`

Nota importante: la corrida total `pass9` quedo incompleta respecto al objetivo original de pass^10. Por estabilidad, limites de Gemma/Google AI Studio y tiempo de ejecucion, no todas las tareas llegaron al mismo K: algunas tienen 6 intentos y otras 5. Aun asi, esta corrida sirve como diagnostico porque cubre todas las tareas 0-21 e identifica claramente los casos con peor reward. La corrida parcial `pass5_v2` se ejecuto despues sobre las tareas que tuvieron reward 0 en esa corrida inicial.

## 2.1 Seleccion de las 10 tareas mas dificiles

Ademas de las metricas por simulacion, se hizo una seleccion estructural de las 10 tareas mas dificiles del dominio. La idea no fue mirar solo el reward historico, sino combinar:

- historial de fallas o fragilidad en simulaciones previas
- cantidad de herramientas involucradas
- cantidad de pasos dependientes
- necesidad de grounding con tools antes de confirmar
- uso de verificacion SMS o identidad
- sensibilidad al orden de ejecucion y a restricciones de policy

Las 10 tareas seleccionadas se guardaron en `top10_tareas_dificiles.json` para poder ejecutarlas mas adelante sin volver a reconstruir la lista.

| Orden | Tarea | Descripcion breve | Por que se considera dificil |
|---|---:|---|---|
| 1 | 6 | Cambio de metodo de pago y pago total. | Usa 6 herramientas y exige flujo encadenado: SMS, cambio de metodo, pago exacto y consulta final de estado. |
| 2 | 20 | Cancelacion con verificacion SMS. | Combina SMS, validacion temporal de cancelacion y una accion sensible sobre la orden. |
| 3 | 16 | Actualizacion de datos del cliente. | Requiere identidad valida, SMS y escritura correcta de multiples campos del cliente. |
| 4 | 21 | Rechazo por codigo SMS incorrecto. | Caso adversarial: el agente debe verificar, rechazar y no ejecutar la accion sensible. |
| 5 | 18 | Registro de reclamo. | Depende de interpretar bien el motivo, escribir en DB y luego confirmar con grounding en tools. |
| 6 | 2 | Nueva direccion mas registro de orden. | Tiene dos escrituras dependientes: primero direccion autorizada, luego orden completa y valida. |
| 7 | 13 | Registro de metodo de pago mas orden. | Coordina creacion de metodo de pago y creacion de orden, con coherencia entre ambas entidades. |
| 8 | 12 | Pago total en efectivo. | Exige monto exacto, una sola transaccion y confirmacion posterior del estado del pago. |
| 9 | 4 | Pedido de lubricante asociado. | La validez depende de una orden de combustible previa que cumpla restricciones del dominio. |
| 10 | 1 | Registro de cliente nuevo. | Es sensible a confirmacion explicita, momento de escritura y cierre prematuro de la conversacion. |

Lectura de esta seleccion:

- Las tareas `6`, `16`, `20` y `21` son las mas exigentes porque combinan acciones sensibles con SMS y varias etapas obligatorias.
- Las tareas `2`, `4`, `12` y `13` exigen razonamiento transaccional: no basta una sola tool, hay que respetar dependencias y restricciones del dominio.
- Las tareas `1` y `18` muestran que incluso una sola escritura puede ser dificil cuando el reward depende del momento exacto de confirmar, del grounding posterior o de la normalizacion semantica.

## 3. Resultados de la corrida total incompleta

Archivo: `simulacion_estaciondeservicio_Rivera_pass9_Incompleta.json`

Resumen: 120 simulaciones, 83 exitosas, 37 fallidas.

Esta corrida debe leerse como una corrida diagnostica incompleta, no como una medicion pass^10 final uniforme. La tabla separa primero las tareas que fallaron para que sea mas facil ver que casos se corrigieron despues.

### 3.1 Tareas con falla en la corrida total

| Tarea | Descripcion breve | pass^K observado | % de falla |
|---|---|---:|---:|
| 1 | Registro de cliente nuevo. | 0/6 | 100.0% |
| 6 | Cambio de metodo de pago y pago total. | 0/6 | 100.0% |
| 12 | Pago total en efectivo. | 0/5 | 100.0% |
| 16 | Actualizacion de datos de cliente. | 0/5 | 100.0% |
| 18 | Registro de reclamo. | 0/5 | 100.0% |
| 20 | Cancelacion con verificacion SMS. | 0/5 | 100.0% |
| 21 | Rechazo por codigo SMS incorrecto. | 0/5 | 100.0% |

### 3.2 Tareas que pasaron en la corrida total

| Tarea | Descripcion breve | pass^K observado | % de falla |
|---|---|---:|---:|
| 0 | Consulta de combustibles y stock. | 6/6 | 0.0% |
| 2 | Orden con nueva direccion autorizada. | 6/6 | 0.0% |
| 3 | Consulta de estado de orden. | 6/6 | 0.0% |
| 4 | Pedido de lubricante asociado. | 6/6 | 0.0% |
| 5 | Cancelacion dentro de ventana permitida. | 6/6 | 0.0% |
| 7 | Rechazo por minimo de galones. | 6/6 | 0.0% |
| 8 | Rechazo de pago parcial. | 6/6 | 0.0% |
| 9 | Solicitud con informacion incompleta. | 6/6 | 0.0% |
| 10 | Escalamiento a asesor humano. | 5/5 | 0.0% |
| 11 | Reprogramacion demasiado tarde. | 5/5 | 0.0% |
| 13 | Registro de pago y orden valida. | 5/5 | 0.0% |
| 14 | Consulta directa de stock. | 5/5 | 0.0% |
| 15 | Busqueda de cliente por RUC. | 5/5 | 0.0% |
| 17 | Emision de factura virtual. | 5/5 | 0.0% |
| 19 | Rechazo por metodo de pago distinto. | 5/5 | 0.0% |

## 4. Resultados de la corrida parcial pass5

Archivo: `rivera_tasks_corregidas_pass5_v2.json`

Resumen: 35 simulaciones, 35 exitosas, 0 fallidas.

Esta corrida se hizo solo sobre las tareas que fallaron en la corrida total incompleta. El objetivo fue comprobar si los ajustes de tareas, policy, tools y evaluacion corregian esos casos dificiles.

| Tarea | Descripcion breve | pass^5 | % de falla |
|---|---|---:|---:|
| 1 | Registro de cliente nuevo. | 5/5 | 0.0% |
| 6 | Cambio de metodo de pago y pago total. | 5/5 | 0.0% |
| 12 | Pago total en efectivo. | 5/5 | 0.0% |
| 16 | Actualizacion de datos de cliente. | 5/5 | 0.0% |
| 18 | Registro de reclamo. | 5/5 | 0.0% |
| 20 | Cancelacion con verificacion SMS. | 5/5 | 0.0% |
| 21 | Rechazo por codigo SMS incorrecto. | 5/5 | 0.0% |

## 4.1 Corridas de corroboracion posteriores

Despues de `pass5_v2` se lanzaron nuevas corridas parciales para verificar estabilidad. Estas corridas no sustituyen la evidencia principal de `pass5_v2`, pero si sirvieron para detectar fragilidades residuales:

- `pass5_v4`: 34/35 rewards. La unica falla fue la tarea 18, donde la accion correcta se ejecuto pero el DB check se rompio por una variacion textual del motivo y la descripcion del reclamo.
- `pass5_v5`: aparecieron fallas puntuales en las tareas 1, 6 y 18. La revision de trazas mostro tres causas concretas: cierre prematuro del usuario antes del `register_client`, ausencia de `sms_policy` en el `initial_state` de la tarea 6 y variaciones semanticas en el texto del reclamo de la tarea 18.

Estas corridas adicionales fueron utiles porque mostraron que la mejora no dependia solo del prompt: tambien habia que fortalecer la definicion de tareas y la normalizacion del dominio.

## 4.2 Metricas agregadas de corroboracion (`v2` + `v4` + `v5`)

Para tener una segunda lectura de estabilidad, se consolidaron las tres corridas parciales posteriores sobre las tareas originalmente fallidas. En total, cada una de estas tareas tiene 15 intentos acumulados en este bloque de corroboracion.

Archivos usados:

- `rivera_tasks_corregidas_pass5_v2.json`
- `rivera_tasks_corregidas_pass5_v4.json`
- `rivera_tasks_corregidas_pass5_v5.json`

| Tarea | Descripcion breve | pass acumulado | % de falla |
|---|---|---:|---:|
| 18 | Registro de reclamo. | 13/15 | 13.3% |
| 1 | Registro de cliente nuevo. | 14/15 | 6.7% |
| 6 | Cambio de metodo de pago y pago total. | 14/15 | 6.7% |
| 12 | Pago total en efectivo. | 15/15 | 0.0% |
| 16 | Actualizacion de datos de cliente. | 15/15 | 0.0% |
| 20 | Cancelacion con verificacion SMS. | 15/15 | 0.0% |
| 21 | Rechazo por codigo SMS incorrecto. | 15/15 | 0.0% |

Lectura de esta tabla:

- La tarea mas fragil en las corridas de corroboracion fue la 18, por sensibilidad del DB check a variaciones del texto del reclamo.
- Las tareas 1 y 6 quedaron cerca de estabilidad total, pero aun mostraron una falla puntual cada una en `v5`.
- Las tareas 12, 16, 20 y 21 quedaron completamente estables en los 15 intentos acumulados.

## 4.3 Corrida final focalizada sobre las 3 tareas mas fragiles

Archivo: `rivera_peores3_pass10_v1.json`

Con base en la tabla agregada de corroboracion, se tomo como tareas mas fragiles a `18`, `1` y `6`. Luego de aplicar los ajustes finales sobre tasks, tools y prompt, se ejecuto una corrida focalizada pass^10 solo sobre esas tres tareas.

| Tarea | Descripcion breve | pass^10 | % de falla |
|---|---|---:|---:|
| 1 | Registro de cliente nuevo. | 10/10 | 0.0% |
| 6 | Cambio de metodo de pago y pago total. | 10/10 | 0.0% |
| 18 | Registro de reclamo. | 10/10 | 0.0% |

Lectura de esta tabla:

- La tarea 1 quedo estabilizada despues de impedir el cierre prematuro del usuario simulado antes de la confirmacion final del registro.
- La tarea 6 quedo estabilizada despues de reinstalar el `sms_policy`, la sesion del usuario y la obligacion de confirmar el pago mediante `get_payment_status`.
- La tarea 18 quedo estabilizada despues de canonizar motivo y descripcion del reclamo y de reforzar la confirmacion posterior con grounding en tools.

## 5. Analisis de peores casos y mejoras

Las tareas con peor rendimiento en la corrida total inicial fueron 1, 6, 12, 16, 18, 20 y 21, todas con 0% de exito en esa corrida. La corrida parcial `pass5_v2` se centro en esas tareas y obtuvo 5/5 en cada una.

Tarea 6: cambio de metodo de pago y pago completo.

Falla observada: el flujo era sensible porque el cambio de metodo de pago podia requerir verificacion adicional y luego debia continuar con el pago total y la consulta de estado. Si el agente omitia parte del flujo, el DB check no coincidia.

Mejora aplicada: se hizo explicito el flujo de SMS, se agregaron datos de cliente/RUC en la tarea y se ajustaron los expected actions para incluir `send_sms_verification_code`, `revisar_sms_de_verificacion`, `verify_sms_code`, `update_order_payment_method`, `make_payment` y `get_payment_status`.

Resultado: paso de 0/6 en la corrida total inicial a 5/5 en la corrida parcial.

Tarea 16: actualizacion sensible de datos del cliente.

Falla observada: la actualizacion de telefono y correo de facturacion es una accion sensible. El modelo podia ejecutar la actualizacion sin representar completamente el flujo de SMS o podia generar variaciones en el motivo del SMS que afectaban la comparacion de DB.

Mejora aplicada: se configuro la politica SMS en el estado inicial, se agrego sesion de usuario para recibir el codigo, se hizo explicito el flujo de lectura del SMS y se robustecio la comparacion para que el texto interno `reason` del SMS no afecte el reward cuando el flujo de negocio es correcto.

Resultado: paso de 0/5 en la corrida total inicial a 5/5 en la corrida parcial.

Tarea 21: codigo SMS incorrecto.

Falla observada: el caso es adversarial porque el usuario entrega un codigo incorrecto. El agente debia rechazar la operacion y no actualizar datos. Si reintentaba automaticamente o seguia con la escritura, fallaba la politica y el DB check.

Mejora aplicada: se agrego una regla explicita al policy para no reintentar en la misma conversacion salvo pedido del usuario, se ajustaron instrucciones del usuario para no corregir el codigo y se modifico la tool para marcar el challenge como expirado cuando el codigo es invalido.

Resultado: paso de 0/5 en la corrida total inicial a 5/5 en la corrida parcial.

Ajustes finales despues de las corridas de corroboracion:

- Tarea 1: se reforzo `task_instructions` para que el usuario simulado no cierre la conversacion solo por confirmar, sino que espere el mensaje final de registro exitoso.
- Tarea 6: se corrigio el `initial_state` para incluir `sms_policy` y `user_data.session`, y se reforzo en policy que la confirmacion del pago debe consultar `get_payment_status`.
- Tarea 18: se fortalecio la normalizacion del tool `register_claim` para mapear variantes como "la entrega llego mas tarde de lo esperado" al motivo canonico `Entrega tardia`, y se fijaron instrucciones mas especificas para el motivo y la descripcion.

Resultado de estos ajustes finales:

- En `rivera_peores3_pass10_v1.json`, las tres tareas mas fragiles (`1`, `6` y `18`) alcanzaron `10/10`.

## 6. Tecnicas de mejora utilizadas

La mejora se trabajo como una serie de experimentos sobre las tareas con peor reward. No todos los cambios fueron solamente texto en `policy.md`: varias tecnicas de prompt engineering se aplicaron tambien en la redaccion de `task_instructions`, en la estructura del flujo esperado y en las descripciones de tools, porque esos textos forman parte del contexto que recibe Gemma durante la simulacion.

| Experimento | Tecnica del txt | Donde se aplico | Resultado observado |
|---|---|---|---|
| 1 | Revision de claridad y especificidad | Se probo en `prompts/policy_exp1.md` y luego se traslado a `tasks.json`: identificadores, RUC, monto exacto, metodo de pago, motivo canonico del reclamo y confirmaciones esperadas. | Las tareas 1, 6, 12, 16, 18, 20 y 21 pasaron de 0% en la corrida incompleta a 5/5 en `pass5_v2`. |
| 2 | Estructura del prompt por secciones | `prompts/policy_exp2.md` se reordeno con secciones de rol, reglas, defensa adversarial, checklist interno, flujo SMS y grounding final. | El flujo de acciones sensibles quedo mas consistente y legible para Gemma. |
| 3 | Plan generation before acting | En `policy_exp2.md` se agrego un checklist interno previo a toda escritura: identificar, revisar estado, validar politica, pedir confirmacion, verificar SMS y luego usar una sola tool. | Ayudo especialmente en tareas con pasos encadenados como 6, 16 y 20. |
| 4 | Duplicacion de reglas criticas | La regla de "codigo SMS invalido = no ejecutar accion sensible" se repitio explicitamente en `policy.md`, `policy_exp2.md` y la task 21. | La task 21 paso a 5/5 sin actualizar datos cuando el codigo fue incorrecto. |
| 5 | Prompting defensivo contra instrucciones indebidas y prompt injection | Se agregaron reglas para ignorar intentos de override del rol, afirmaciones de autoridad no verificadas e instrucciones incrustadas en texto libre. | El prompt final quedo alineado con los casos adversariales pedidos en el entregable, aunque no todos fueron re-simulados en esta etapa final. |
| 6 | Fundamentacion estricta en herramientas | Se reforzo que, si el usuario pide confirmar saldo, pago o detalle de reclamo, el agente debe usar `get_payment_status` o `get_claim_details` antes de responder. | Corrige fragilidad residual observada en la tarea 6 y fortalece la dimension 16. |
| 7 | Normalizacion y tolerancia a variaciones del modelo | Se normalizaron fechas, motivos de reclamo/cancelacion y razones de SMS para que diferencias textuales no sustantivas no rompan el reward. | Las tareas 18, 20 y los flujos SMS dejaron de fallar por formato/metadatos. |
| 8 | Alineacion de evaluacion con herramientas | El evaluador sincroniza tools despues de acciones esperadas, igual que ocurre en una conversacion real. | Los DB checks de SMS quedaron alineados entre trayectoria real y gold environment. |

Impacto directo sobre las 3 tareas mas fragiles:

- Tarea 1: mejoro con claridad/especificidad en la instruccion del usuario y con la regla de no cerrar la conversacion antes de la confirmacion final.
- Tarea 6: mejoro con estructura del flujo SMS, checklist previo a actuar y grounding obligatorio con `get_payment_status`.
- Tarea 18: mejoro con canonizacion semantica del reclamo, grounding con `get_claim_details` y mayor especificidad del motivo/descripcion en la task.

Tecnicas consideradas y no priorizadas:

- Few-shot learning: no se agregaron ejemplos largos porque aumentaban tokens y tiempo de ejecucion con Gemma; se prefirio claridad directa en policy y tasks.
- Chain-of-thought explicito: no se pidio razonamiento visible para evitar respuestas largas o incompatibles con tool calls.
- GEPA/meta prompting: se uso la idea de iterar, evaluar y conservar la variante que mejoraba metricas, pero no se incorporo una carpeta extensa de prompts intermedios para no inflar la entrega.

Relacion con las especificaciones del txt del curso:

- Se incorporo el flujo de verificacion SMS con `role validation` y tambien el caso de codigo incorrecto.
- Se dejaron reglas explicitas contra instrucciones que el agente no debe seguir y contra prompt injection en texto libre.
- Se documento el uso de al menos 5 tecnicas de prompt engineering con evidencia de donde se aplicaron.
- Se conservo `pass9` como corrida diagnostica incompleta y `pass5_v2` como evidencia principal de mejora sobre las tareas mas problematicas.

## 7. Conclusion

Gemma fue capaz de resolver bien la mayoria de tareas simples desde la corrida total inicial, especialmente consultas, rechazos por politica, busquedas y operaciones directas. Las fallas se concentraron en tareas con multiples pasos, verificacion SMS, cambios sensibles y comparaciones estrictas de DB.

La mejora mas efectiva fue reducir ambiguedad: especificar identificadores, ordenar los pasos de operaciones sensibles y reforzar reglas criticas en el policy. Tambien fue importante hacer robustas las herramientas frente a variaciones normales del modelo, porque en algunos casos el agente cumplia la intencion del negocio pero el reward fallaba por diferencias de formato o metadatos.

Con los cambios finales, la corrida parcial inicial sobre tareas problematicas obtuvo `35/35`, y la corrida final focalizada sobre las 3 tareas mas fragiles (`1`, `6` y `18`) obtuvo `30/30`. Esto muestra que los principales puntos de falla identificados en la corrida total inicial fueron corregidos y luego estabilizados en una validacion adicional pass^10.
