# Hallazgos acumulados E1-E4 - ecommerce_calle

## 1. Descripcion del dominio y las tareas

`ecommerce_calle` modela soporte post-venta para una tienda online: consultas de
pedido, seguimiento, cancelaciones, cambios de direccion, devoluciones,
reemplazos, reembolsos y escalamiento a un humano. El dominio mezcla tareas
permitidas, casos fuera de politica, bypass de identidad, presion emocional y
prompt injection.

Desde E3, el subconjunto critico de evaluacion quedo fijado en las 10 tareas de
menor `pass^5`: `3, 8, 10, 11, 14, 16, 19, 21, 22, 23`. E4 reutiliza exactamente
ese subconjunto para que la comparacion entre entregas sea valida.

## 2. Evolucion del agente a lo largo de las entregas

| Entrega | Cambio principal | Metrica | Resultado | Lectura |
|---------|------------------|---------|-----------|---------|
| E1 | Baseline inicial | pass^1 | Sin consolidar en este resumen | Punto de partida |
| E2 | Politica mas clara y restricciones explicitas | pass^5 | 13/50 en `base_top10hard` previo a E3 | Mejora por prompting |
| E3 | Prompt consolidado con checklist SMS, anti-injection y cierre de escalamiento | pass^5 | 35/50 | Mejor salto observado |
| E4-B | RAG con `headers`, `k=3` | pass^5 | 32/50 | Regresion frente a E3 |
| E4-C | RAG con `fixed_200`, `k=3` | pass^5 | 35/50 | Empata E3, no mejora |
| E4-D | Mejor chunking + think | pass^5 | 17/50 | Resultado afectado por cuota/fallos |

La lectura global es clara: la mayor ganancia real del proyecto ocurre en E3,
cuando el agente recibe un prompt mas procedimental. E4 cambia la forma de
recuperar politica, pero no supera ese techo.

## 3. Categorias de fallo mas frecuentes

### EVAL_MISMATCH

Descripcion breve: la conversacion parece correcta, pero el estado final de la
base o el evaluador no reflejan exito.

Persistencia en E4: sigue siendo una explicacion plausible para tareas como `22`,
que permanece en `0/5` en A, B, C y D pese a que el flujo conversacional puede
verse razonable.

### POLICY_MISS

Descripcion breve: el agente no aplica bien una regla de negocio aunque la
informacion relevante esta disponible.

Persistencia en E4: la tarea `8` mejora parcialmente con `headers` (`2/5`), pero
no de forma estable. Eso sugiere que recuperar trozos de politica puede ayudar,
pero no basta para volver robusta la decision.

### SIMULATOR_DRIFT

Descripcion breve: el simulador introduce variacion que desvincula la trayectoria
del caso objetivo.

Persistencia en E4: baja en comparacion con E2/E3, pero no desaparece. La mejora
de E3 en tareas SMS sigue siendo mas importante que el cambio a RAG.

### INFRA_PROVIDER_FAILURE

Descripcion breve: el experimento falla por limites o errores del proveedor, no
por la logica del agente.

Nueva evidencia en E4: la condicion D termina con `23` `agent_error`, `1`
`max_steps` y logs `RESOURCE_EXHAUSTED` del free tier de Gemini. Este tipo de
fallo no existia como factor central en el analisis de E3 y se vuelve decisivo al
evaluar think.

## 4. Comportamiento especifico de Gemma 4 en el dominio

Gemma 4 se comporta bien cuando el flujo es procedimental y el prompt deja claro
el orden de herramientas. Eso ya se habia visto en E3 y se mantiene en A/C para
las siete tareas estables (`10, 11, 14, 16, 19, 21, 23`).

El cambio a RAG no entrega una mejora consistente en las tareas mas dificiles:

- tarea `3`: `0/5` en todas las condiciones
- tarea `8`: solo B llega a `2/5`
- tarea `22`: `0/5` en todas las condiciones

Esto sugiere que el cuello de botella no era solo "tener mas politica a mano",
sino una mezcla de evaluacion estricta, fragilidad del entorno y decisiones de
agente que siguen sin estabilizarse en los casos mas sensibles.

Tambien se confirma que la herramienta `think` si fue usada en D: el JSON final
contiene `55` llamadas a `think`. El problema es que la mejora potencial queda
opacada por fallos de cuota del proveedor.

## 5. Recomendaciones para un sistema de produccion

La mejor configuracion reproducible al cierre de E4 es:

- chunking `fixed_200`
- `retrieval_k = 3`
- sin `think`

No porque supere a E3, sino porque evita la regresion de `headers` y mantiene el
mejor resultado limpio observado (`35/50`).

Para produccion, la recomendacion sigue siendo conservadora:

- automatizar solo tareas informativas o procedimentales ya estabilizadas
- mantener aprobacion humana en cancelaciones, devoluciones y reembolsos
- no depender de `think` en free tier si la estabilidad del proveedor no esta
  garantizada

Si hubiera una E5, las prioridades razonables no serian mas prompting sino:

- depurar `EVAL_MISMATCH` en tareas como `22`
- instrumentar mejor fallos de estado final
- repetir D en un entorno con cuota suficiente para separar fallos de razonamiento
  de fallos de infraestructura
