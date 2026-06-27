# Reporte E4 — Estación de Servicio Rivera

## Configuración del experimento

- Política fuente: policy.md (721 palabras, 5 secciones `##`)
- Modelo: gemini/gemma-4-26b-a4b-it
- Estrategia de tamaño fijo elegida para C: fixed_200
- Motivo: La politica presenta 721 palabras si se aplicaba un chunck 400 solo se iban a generar 2 chuncks, por lo que se iba a llamar, practicamente, a toda la politica. Es por esto, que se opto por un fixed_200, puesto que se ibana generar 4 chuncks lo que a su vez era mas comparable con el separador de headers que generaba 6 chuncks.
- Limite de pasos: B, C y D se ejecutaron con `max_steps=30`. A conserva `max_steps=200` porque es la simulacion E3 reutilizada, sin una ejecucion nueva, como indica el entregable.

## Tabla de chunks por estrategia

| Estrategia  | Núm. chunks | Palabras promedio por chunk |
|-------------|-------------|------------------------------|
| headers     | 6           | 120.2                        |
| fixed_200   | 4           | 180.2                        |

## Matriz de resultados (pass^5, 10 tareas)

|                            | Sin think | Con think |
|----------------------------|-----------|-----------|
| A — Baseline E3 (sin RAG)  | 45/50     | —         |
| B — headers,   k=3         | 45/50     | —         |
| C — fixed_200, k=3         | 45/50     | —         |
| D — mejor (headers), k=3   | —         | 20/50     |

## Análisis

### Chunking (comparar B y C con A)

B y C empatan exactamente: 45/50 cada una, y además fallan en la misma tarea (#6) con el mismo patrón en las cinco simulaciones. Para este dominio, la estrategia de chunking no marcó ninguna diferencia medible, a pesar de cortar a mitad de sección en lugar de respetar los encabezados. Se terminó recuperando la información necesaria igual de bien que headers en la práctica, probablemente porque retrieval_k=3 compensa los cortes imprecisos trayendo varios chunks adyacentes a la vez.

Sin embargo, sí cambió fue el total frente al baseline sin RAG: A también saca 45/50, pero la tarea que falla no es la misma. En A falla la tarea 13 (0/5), mientras que en B y C la tarea 13 pasa (5/5). Esto sugiere que retrieve_policy sí está cumpliendo su función cuando el agente necesita confirmar campos obligatorios de register_order, algo que no pasaba cuando se ingresaba la politica completa.

No obstante, RAG rompió la tarea 6 (cambio de método de pago), que en el baseline pasaba 5/5. Las cinco simulaciones de la tarea 6 en B y C terminan por max_steps, atascadas en un bucle donde el agente reenvía un código SMS y el usuario simulado insiste en que no lo recibió. En este caso el retrieve policy ha hecho que el agente recuerde el chunck en 3 ocaciones, esto sumado a que el cliente no ha recibido el SMS y que se han llamado a otras dos tools han hecho que la conversacion se haya extendido. En este caso se uso la simulacion sim_e4_b #46. Asi mismo, esto lo empeora el hecho que el agente no envia en una primera instancia el SMS sino que tiene que el cliente avisarle que no recibio nada para recien enviarlo, ademas el agente intenta realizar la actualizacion del metodo de pago sin tener el codigo SMS del cliente.

### Think tool (comparar D con la mejor de B/C)

En primer lugar, es importante definir, puesto que B y C fueron similares, que para esta simulacion D se eligio el chuncking por headers debido a que no corta a la mitad las frases y los chuncks tienen un contexto completo. 

Respecto a las simulaciones B y C se evidencio un bajon en el rendimiento de las tareas con el think. La simulacion D solo logro el exito en 20/50 de las tareas. Despues de leer algunas simulaciones la causa es clara el think sumo pasos lo que hizo que las simulaciones fallaran por max steps. Esto sucedio en el 60% de las simulaciones. Asi mismo, y en 5 de ellas aparece literalmente el mensaje "tuve un problema interno al procesar este turno, por favor repite el dato clave", lo que indica que el modelo también tuvo dificultades para generar una respuesta válida combinando think con el formato de tool-calling de Gemma.

En la tarea 2 se ve un caso drastico, el agente no falla pero se tiene un cierre forzado por los max steps. El agente logra sus acciones pero como el cierre no es el esperado no se obtiene el reward. En este caso el agente se queda en la pregunta: ¿Hay algo mas en lo que pueda ayudarlo? y se corta. 
Algo similar pasa en la task 13 ya que se queda incompleta, el think suma un paso mas lo que aumenta el numero de pasos en las tareas que ya estan justas, al llegar a 30 pasos esta tarea se corta y no se completa sin importar que el agente no haya tenido un error. Esto mismo pasa en la task 20. Sin embargo, en la tarea 13 tambien se puede observar un timeout, el agente envia un mensaje de `lo siento, he tenido un problema interno al procesar este turno`. Esto es fue una falta de respuesta del servidor. Posteriormente se retoma la conversacion desde ese punto y sigue hasta el max_steps.

Sin embargo, en la task 6 lo que sucede es que el agente tiene una alucinacion y no envia el SMS. Esto hace que se gasten pasos en pedir el SMS sin que el cliente lo tenga. Aqui se debe mejorar el policy para especificar que antes que el agente pida el codigo SMS este se asegure que lo haya enviado.



## Tarea por tarea (mejor condición)

| Tarea ID | Descripción breve | pass^5 baseline (A) | pass^5 mejor (B headers) | ¿Cambió? |

| 1        | Registro de cliente nuevo               | 5/5 | 5/5 | No |
| 2        | Nueva dirección + registro de orden     | 5/5| 5/5 | No |
| 4        | Pedido de lubricante asociado           | 5/5| 5/5| No |
| 6        | Cambio de método de pago y pago total   | 5/5| 0/5 | Sí, empeoro |
| 12       | Pago total en efectivo                  | 5/5| 5/5 | No |
| 13       | Registro de método de pago + orden      | 0/5| 5/5 | Sí, mejoro|
| 16       | Actualización de datos del cliente (SMS)| 5/5| 5/5 | No |
| 18       | Registro de reclamo                     | 5/5| 5/5 | No |
| 20       | Cancelación con verificación SMS        | 5/5| 5/5 | No |
| 21       | Rechazo por código SMS incorrecto       | 5/5| 5/5 | No |

## Conclusión

De estos experimentos se puede concluir que el RAG no obtuvo impactos negativos respecto al baseline. Logro las mismas metricas que esta solo con la diferencia que pudo solucionar el reward de la tarea 13 a cambio de fallo de la tarea 6. Respecto a esta mejora de la task 13, se venia trabajando solo con ingresar una vez la politica, pero con el RAG hizo que se le recuerden al agente puntos criticos lo que hizo que para estas nuevas simulaciones no se le pasen por alto. En general, la task 13 ya cumplia su funcion, mas en la comprarcion con la tarea esperada hay argumentos que no coinciden y se le penaliza con el reward 0, a pesar de poder cumplir el registro de la orden.

En cuanto a la tecnica de chuncking tampoco hubo cambios entre el fixed_200 y el headers. Ambos obtuvieron los mismos aciertos y la misma falla (tarea 6). Por su parte, el think si perjudico el rendimiento del agente puesto que ocupaba muchos mas pasos de lo habitual, esto sumado a que las tareas tenian los pasos justos hizo que el 60% las simulaciones de las tareas se corten bruscamente siendo penalizadas con el reward = 0, a pesar que no fallo algo en si del agente sino que se llego al numero de pasos maximos. 

Tambien se detecto un error en la task 6 donde se estan desperdiciando pasos. El agente intenta realizar la actualizacion del metodo de pago antes de enviar y recibir el codigo SMS del cliente. En este momento es donde le salta el error y el agente tiene una alucinacion pidiendole al cliente el codigo SMS que aun no envia. Depsues que el cliente le comunica que no ha recibido ningun SMS es cuando el agente llama a la tool para enviar el codigo de verificacion.

Como conclusion final: El RAG ayuda a que no se pasen por alto algunos puntos criticos, no obstante hace que cada tarea demande de mas pasos lo que logra que algunas task terminen por max steps. Esto hace que no todas lleguen a completarse, incluso algunas quedandose por lo minimo (caso de la task 13 en la simulacion D).
