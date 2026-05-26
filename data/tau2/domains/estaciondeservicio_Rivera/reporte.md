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

Nota importante: la corrida total `pass9` quedo incompleta respecto al objetivo original de pass^10. Por estabilidad, limites de Gemma/Google AI Studio y tiempo de ejecucion, no todas las tareas llegaron al mismo K: algunas tienen 6 intentos y otras 5. Aun asi, esta corrida sirve como diagnostico porque cubre todas las tareas 0-21 e identifica claramente los casos con peor reward. La corrida parcial `pass5_v2` se ejecuto despues sobre las tareas que tuvieron reward 0 en esa corrida inicial.

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

## 6. Tecnicas de mejora utilizadas

La mejora se trabajo como una serie de experimentos sobre las tareas con peor reward. No todos los cambios fueron solamente texto en `policy.md`: varias tecnicas de prompt engineering se aplicaron tambien en la redaccion de `task_instructions`, en la estructura del flujo esperado y en las descripciones de tools, porque esos textos forman parte del contexto que recibe Gemma durante la simulacion.

| Experimento | Tecnica | Donde se aplico | Resultado observado |
|---|---|---|---|
| 1 | Revision de claridad y especificidad | Se reescribieron instrucciones ambiguas para incluir identificadores, RUC, monto exacto, metodo de pago y confirmaciones esperadas en `tasks.json`. | Las tareas 1, 6, 12, 16, 18, 20 y 21 pasaron de 0% en la corrida incompleta a 5/5 en `pass5_v2`. |
| 2 | Estructura de flujo antes de actuar | Los casos sensibles se redactaron como secuencias obligatorias: enviar SMS, leer SMS con user tool, verificar codigo y recien ejecutar la accion sensible. | Las tareas 6, 16, 20 y 21 pasaron a 5/5. |
| 3 | Duplicacion de reglas criticas | La regla de codigo SMS invalido se reforzo en `policy.md` y en la instruccion especifica de la task 21. | La task 21 paso a 5/5 sin actualizar datos cuando el codigo fue incorrecto. |
| 4 | Prompting defensivo contra acciones indebidas | Se hicieron explicitas las condiciones de no actuar: no pagar con metodo distinto, no pago parcial, no reintentar SMS invalido y no modificar DB sin datos suficientes. | Las tareas de rechazo y seguridad mantuvieron reward completo; la task 21 quedo corregida. |
| 5 | Normalizacion y tolerancia a variaciones del modelo | Se normalizaron fechas, motivos de reclamo/cancelacion y razones de SMS para que diferencias textuales no sustantivas no rompan el reward. | Las tareas 18, 20 y los flujos SMS dejaron de fallar por formato/metadatos. |
| 6 | Alineacion de evaluacion con herramientas | El evaluador sincroniza tools despues de acciones esperadas, igual que ocurre en una conversacion real. | Los DB checks de SMS quedaron alineados entre trayectoria real y gold environment. |

Tecnicas consideradas y no priorizadas:

- Few-shot learning: no se agregaron ejemplos largos porque aumentaban tokens y tiempo de ejecucion con Gemma; se prefirio claridad directa en policy y tasks.
- Chain-of-thought explicito: no se pidio razonamiento visible para evitar respuestas largas o incompatibles con tool calls.
- GEPA/meta prompting: se uso la idea de iterar, evaluar y conservar la variante que mejoraba metricas, pero no se incorporo una carpeta extensa de prompts intermedios para no inflar la entrega.

## 7. Conclusion

Gemma fue capaz de resolver bien la mayoria de tareas simples desde la corrida total inicial, especialmente consultas, rechazos por politica, busquedas y operaciones directas. Las fallas se concentraron en tareas con multiples pasos, verificacion SMS, cambios sensibles y comparaciones estrictas de DB.

La mejora mas efectiva fue reducir ambiguedad: especificar identificadores, ordenar los pasos de operaciones sensibles y reforzar reglas criticas en el policy. Tambien fue importante hacer robustas las herramientas frente a variaciones normales del modelo, porque en algunos casos el agente cumplia la intencion del negocio pero el reward fallaba por diferencias de formato o metadatos.

Con los cambios finales, la corrida parcial sobre las tareas problematicas obtuvo 35/35 rewards correctos, lo que muestra que los principales puntos de falla identificados en la corrida total inicial fueron corregidos.
