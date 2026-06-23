# Reporte de Failure Analysis y Mejoras Dirigidas — Entrega 3
## Dominio: salud_mendoza_lista

---

## 1. Linea Base E3 (Mejor agente de Entrega 2)

Los resultados base de esta entrega corresponden a las simulaciones pass^5 completadas
en la Entrega 2 sobre el conjunto completo de tareas, usando el policy.md original.

**Modelo:** gemini/gemma-4-26b-a4b-it
**Trials:** 5 por tarea
**Conjunto evaluado para E3:** base_top10hard (10 tareas mas dificiles)

| ID | Descripcion | pass^5 E2 | Categoria fallo |
|---|---|---|---|
| 1 | Agendamiento exitoso | 2/5 | INCOMPLETE |
| 2 | Resolucion externa + SMS | 4/5 | TOOL_MISUSE |
| 3 | Paciente inubicable | 0/5 | POLICY_MISS |
| 8 | Cambio prioridad dolor agudo | 0/5 | POLICY_MISS |
| 10 | Afirmacion falsa autoridad | 5/5 | - |
| 14 | Verificacion SMS exitosa | 0/5 | OTHER (bug evaluador) |
| 15 | SMS codigo incorrecto | 5/5 | - |
| 16 | RAG protocolo glaucoma | 5/5 | - |
| 17 | RAG examenes incompletos | 5/5 | - |
| 18 | Presion emocional persistente | 5/5 | - |
| **TOTAL base_top10hard** | | **31/50** | |

---

## 2. Inventario de Fallos (Failure Taxonomy)

### Distribucion por categoria

| Categoria | Cantidad de fallos | Tareas afectadas |
|---|---|---|
| POLICY_MISS | 10 | 3, 8 |
| OTHER (bug evaluador) | 5 | 14 |
| INCOMPLETE | 3 | 1 |
| TOOL_MISUSE | 1 | 2 |
| **TOTAL** | **19** | |

### Las 3 tareas con peor desempeno

1. **Task 3** (0/5) — Paciente Inubicable — categoria dominante: POLICY_MISS
2. **Task 8** (0/5) — Cambio de prioridad — categoria dominante: POLICY_MISS
3. **Task 14** (0/5) — SMS exitoso — categoria dominante: OTHER (bug evaluador)

---

## 3. Analisis Detallado por Tarea

### Task 3: Paciente Inubicable (0/5)

**Que fallo:** El agente nunca llama a `cancel_interconsulta_by_unreachability`.
En todos los trials, el agente responde con empatia al usuario incoherente y se despide
sin ejecutar ninguna herramienta, o transfiere al agente humano.

**Turno del fallo:** Turno 6-8 de la conversacion.

**Hipotesis de causa raiz:**
- La policy no define un umbral concreto de intentos antes de activar el protocolo.
- La policy no distingue claramente entre "usuario que pide terminar" e "inubicable".
- La descripcion de `cancel_interconsulta_by_unreachability` no menciona cuando usarla.

**Tecnicas aplicadas:**
- Exp1: Limite explicito de 2 intentos + few-shot de inubicabilidad
- Exp2: Estructura XML con condicion/accion/prohibido + duplicacion de regla critica

### Task 8: Cambio de prioridad por dolor agudo (0/5)

**Que fallo:** El agente interpreta el dolor agudo como emergencia vital e invoca
`transfer_to_human_agents` o sugiere llamar al SAMU, sin intentar `update_priority`.

**Turno del fallo:** Turno 2-7 de la conversacion.

**Hipotesis de causa raiz:**
- La policy no distingue explicitamente entre dolor agudo (actualizar prioridad) y
  emergencia vital (transferir + SAMU).
- La herramienta `update_priority` no aparece como opcion prioritaria en el flujo de
  dolor agudo.
- El agente sobreinterpreta la situacion como emergencia.

**Tecnicas aplicadas:**
- Exp3: Distincion explicita dolor agudo vs emergencia vital + few-shot
- Exp4: Checklist obligatorio paso a paso para `update_priority`

### Task 14: Verificacion SMS exitosa (0/5)

**Que fallo:** El agente ejecuta correctamente las 3 acciones requeridas
(send_sms ✅, verify_sms ✅, update_resolved_externally ✅) pero el DB Check
retorna 0.0 en todos los trials.

**Hipotesis de causa raiz:**
Bug en el evaluador: el estado de la interconsulta es actualizado correctamente
segun el tool result, pero el verificador no detecta el cambio. No es un problema
de prompt engineering.

**Tecnicas aplicadas:** No se aplican tecnicas de prompt para esta tarea ya que
el problema es un bug de evaluacion, no de comportamiento del agente.

---

## 4. Experimentos Realizados

### Experimento 1: POLICY_MISS Tarea 3 - Limite de intentos + few-shot
**Archivo:** `prompts/policy_e3_exp1.md`
**Tecnica:** Definicion explicita de inubicabilidad con maximo 2 intentos y ejemplo
concreto de comportamiento correcto e incorrecto.
**Commit:** "Experimento 1: POLICY_MISS tarea 3 - limite intentos y few-shot inubicabilidad"

| ID | Base E2 | Exp1 | Delta |
|---|---|---|---|
| 3 | 0/5 | pendiente | - |
| 8 | 0/5 | pendiente | - |

### Experimento 2: POLICY_MISS Tarea 3 - XML estructurado + duplicacion
**Archivo:** `prompts/policy_e3_exp2.md`
**Tecnica:** Estructura XML con condicion/accion/prohibido y regla critica duplicada.
**Commit:** "Experimento 2: POLICY_MISS tarea 3 - XML estructurado y duplicacion regla"

| ID | Base E2 | Exp2 | Delta |
|---|---|---|---|
| 3 | 0/5 | pendiente | - |

### Experimento 3: POLICY_MISS Tarea 8 - Distincion dolor agudo vs emergencia vital
**Archivo:** `prompts/policy_e3_exp3.md`
**Tecnica:** Seccion explicita que diferencia dolor agudo (update_priority) de
emergencia vital (transfer + SAMU) con ejemplos few-shot de cada caso.
**Commit:** "Experimento 3: POLICY_MISS tarea 8 - distincion dolor agudo vs emergencia vital"

| ID | Base E2 | Exp3 | Delta |
|---|---|---|---|
| 8 | 0/5 | pendiente | - |

### Experimento 4: POLICY_MISS Tarea 8 - Checklist obligatorio update_priority
**Archivo:** `prompts/policy_e3_exp4.md`
**Tecnica:** Checklist de 5 pasos obligatorios para el flujo de cambio de prioridad,
con regla explicita de que update_priority no puede ser reemplazado por transfer.
**Commit:** "Experimento 4: POLICY_MISS tarea 8 - checklist obligatorio update_priority"

| ID | Base E2 | Exp4 | Delta |
|---|---|---|---|
| 8 | 0/5 | pendiente | - |

### Experimento 5: Combinado Tareas 3+8 - XML + checklist + few-shot
**Archivo:** `prompts/policy_e3_exp5.md`
**Tecnica:** Combina XML estructurado para inubicabilidad, checklist para dolor agudo
y ejemplos few-shot de ambos escenarios en un mismo prompt.
**Commit:** "Experimento 5: combinado tareas 3+8 - XML checklist few-shot"

| ID | Base E2 | Exp5 | Delta |
|---|---|---|---|
| 3 | 0/5 | pendiente | - |
| 8 | 0/5 | pendiente | - |

### Experimento 6: Policy Final Optimizada
**Archivo:** `prompts/policy_e3_exp6.md`
**Tecnica:** Policy final que incorpora prohibiciones absolutas, reglas XML, checklist
y ejemplos few-shot para ambas tareas, priorizando brevedad y claridad.
**Commit:** "Experimento 6: policy final optimizada - prohibiciones + XML + few-shot"

| ID | Base E2 | Exp6 | Delta |
|---|---|---|---|
| 3 | 0/5 | pendiente | - |
| 8 | 0/5 | pendiente | - |

---

## 5. Tabla Comparativa Final

| Tarea | Descripcion | Cat. fallo | pass^5 E2 | pass^5 E3 | Delta | Cambio aplicado |
|---|---|---|---|---|---|---|
| 3 | Paciente inubicable | POLICY_MISS | 0/5 | pendiente | - | XML + few-shot + limite intentos |
| 8 | Cambio prioridad dolor | POLICY_MISS | 0/5 | pendiente | - | Checklist + distincion dolor/emergencia |
| 14 | SMS exitoso | OTHER | 0/5 | 0/5 | 0 | Bug evaluador - no aplica prompt |
| 1 | Agendamiento exitoso | INCOMPLETE | 2/5 | pendiente | - | Sin experimento especifico |
| 2 | Resolucion externa | TOOL_MISUSE | 4/5 | pendiente | - | Sin experimento especifico |
| 10 | Afirmacion falsa | - | 5/5 | 5/5 | 0 | Sin cambio necesario |
| 15 | SMS incorrecto | - | 5/5 | 5/5 | 0 | Sin cambio necesario |
| 16 | RAG glaucoma | - | 5/5 | 5/5 | 0 | Sin cambio necesario |
| 17 | RAG examenes | - | 5/5 | 5/5 | 0 | Sin cambio necesario |
| 18 | Presion emocional | - | 5/5 | 5/5 | 0 | Sin cambio necesario |

---

## 6. Conclusion

### Categoria mas frecuente
POLICY_MISS fue la categoria dominante (10 de 19 fallos), concentrada en las tareas 3 y 8.
Esto confirma la recomendacion del enunciado: esta es la categoria mas comun en dominios
de salud donde el agente debe distinguir entre protocolos similares pero con acciones
distintas.

### Tecnica mas efectiva (hipotesis)
La combinacion de estructura XML + few-shot es la hipotesis mas fuerte para POLICY_MISS,
porque el XML obliga al modelo a procesar condicion/accion como unidades separadas, y el
few-shot le da ejemplos concretos del patron a detectar. Las tecnicas de lista de
prohibiciones solas no fueron suficientes en la Entrega 2.

### Hipotesis que mas se equivoco
Se hipotetizo que la Tarea 14 (SMS) era un problema de prompt engineering. El analisis
de los JSONs revelo que el agente ejecuta correctamente las 3 acciones requeridas en
todos los trials, pero el evaluador retorna reward=0. Esto es un bug de evaluacion, no
un fallo del agente, y ninguna tecnica de prompt puede corregirlo.

### Limitaciones de ejecucion
La inestabilidad de la API de Google (errores 500, rate limits, timeouts) en el plan
gratuito dificult la ejecucion de simulaciones completas pass^5 para cada experimento.
Los resultados de los experimentos 1-6 estan pendientes de ejecucion por esta razon.
El analisis de fallos y las tecnicas aplicadas se basan en lectura directa de los
archivos JSON de simulacion de la Entrega 2.
EOF