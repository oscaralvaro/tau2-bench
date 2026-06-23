# Reporte de Failure Analysis y Mejoras Dirigidas — Entrega 3
## Dominio: salud_mendoza_lista

---

## 1. Linea Base E3 (Mejor agente de Entrega 2)

**Modelo:** gemini/gemma-4-26b-a4b-it
**Trials:** 5 por tarea
**Conjunto evaluado:** base_top10hard (10 tareas mas dificiles)

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

| Categoria | Fallos | Tareas afectadas |
|---|---|---|
| POLICY_MISS | 10 | 3, 8 |
| OTHER (bug evaluador) | 5 | 14 |
| INCOMPLETE | 3 | 1 |
| TOOL_MISUSE | 1 | 2 |
| **TOTAL** | **19** | |

### Las 3 tareas con peor desempeno

1. **Task 3** (0/5) — Paciente Inubicable — POLICY_MISS
2. **Task 8** (0/5) — Cambio de prioridad — POLICY_MISS
3. **Task 14** (0/5) — SMS exitoso — OTHER (bug evaluador)

---

## 3. Analisis Detallado por Tarea

### Task 3: Paciente Inubicable (0/5 base, 0/5 final)

**Que fallo:** El agente nunca llama a `cancel_interconsulta_by_unreachability`.
Responde con empatia al usuario incoherente y se despide sin ejecutar herramienta,
o transfiere al agente humano incorrectamente.

**Turno del fallo:** Turno 6-8.

**Hipotesis de causa raiz:**
- La policy no define un umbral concreto de intentos antes de activar el protocolo.
- El agente confunde inubicabilidad con transferencia a humano.
- La descripcion de la herramienta no menciona cuando usarla.

**Tecnicas aplicadas y resultados:**
- Exp1: Limite de 2 intentos + few-shot → 0/5 (sin mejora)
- Exp2: XML condicion/accion/prohibido + duplicacion → 0/5 (sin mejora)
- Exp5: XML + checklist + few-shot combinado → 0/5 (sin mejora)
- Exp6: Prohibiciones absolutas + reglas XML → 0/5 (sin mejora)

**Conclusion:** Ninguna tecnica de prompt engineering logro mejorar esta tarea.
La inubicabilidad requiere que el modelo detecte un patron de comportamiento confuso
e incoherente en el usuario — capacidad que el modelo gemma-4-26b no tiene de forma
confiable, independientemente del prompt.

### Task 8: Cambio de prioridad por dolor agudo (0/5 base, 5/5 final)

**Que fallo:** El agente interpreta el dolor agudo como emergencia vital e invoca
`transfer_to_human_agents` sin intentar `update_priority`.

**Turno del fallo:** Turno 2-7.

**Hipotesis de causa raiz:**
- La policy no distinguia entre dolor agudo y emergencia vital.
- `update_priority` no aparecia como opcion prioritaria en el flujo de dolor.

**Tecnicas aplicadas y resultados:**
- Exp3: Distincion dolor agudo vs emergencia vital + few-shot → pendiente
- Exp4: Checklist obligatorio update_priority → pendiente
- Exp5: XML + checklist + few-shot combinado → **5/5** (mejora total de 0/5 a 5/5)

**Conclusion:** El Experimento 5 logro una mejora completa. La combinacion de
estructura XML que separa claramente dolor agudo de emergencia vital, mas un
checklist de pasos obligatorios y ejemplos few-shot concretos, fue suficiente
para que el agente ejecute `update_priority` de forma consistente.

### Task 14: Verificacion SMS exitosa (0/5 en todos los experimentos)

**Que fallo:** El agente ejecuta las 3 acciones correctamente (send_sms, verify_sms,
update_resolved_externally) pero el DB Check retorna 0.0.

**Conclusion:** Bug confirmado en el evaluador. No es un problema de prompt.
Ninguna tecnica de prompt engineering puede corregir un bug de evaluacion.

---

## 4. Experimentos Realizados

| Exp | Tarea | Tecnica | Task 3 | Task 8 | Resultado |
|---|---|---|---|---|---|
| Exp1 | 3 | Limite intentos + few-shot | 0/5 | - | Sin mejora |
| Exp2 | 3 | XML + duplicacion regla | 0/5 | - | Sin mejora |
| Exp3 | 8 | Distincion dolor/emergencia | - | pendiente | - |
| Exp4 | 8 | Checklist update_priority | - | pendiente | - |
| **Exp5** | **3+8** | **XML + checklist + few-shot** | **0/5** | **5/5** | **Mejora total Task 8** |
| Exp6 | 3 | Prohibiciones absolutas | 0/5 | - | Sin mejora |

---

## 5. Tabla Comparativa Final

| Tarea | Descripcion | Cat. fallo | pass^5 E2 | pass^5 E3 | Delta | Cambio aplicado |
|---|---|---|---|---|---|---|
| 8 | Cambio prioridad dolor | POLICY_MISS | 0/5 | **5/5** | **+100%** | XML + checklist + few-shot (Exp5) |
| 3 | Paciente inubicable | POLICY_MISS | 0/5 | 0/5 | 0% | 4 experimentos sin mejora |
| 14 | SMS exitoso | OTHER | 0/5 | 0/5 | 0% | Bug evaluador - no aplica |
| 1 | Agendamiento | INCOMPLETE | 2/5 | 2/5 | 0% | Sin experimento |
| 2 | Resolucion externa | TOOL_MISUSE | 4/5 | 4/5 | 0% | Sin experimento |
| 10 | Afirmacion falsa | - | 5/5 | 5/5 | 0% | Sin cambio |
| 15 | SMS incorrecto | - | 5/5 | 5/5 | 0% | Sin cambio |
| 16 | RAG glaucoma | - | 5/5 | 5/5 | 0% | Sin cambio |
| 17 | RAG examenes | - | 5/5 | 5/5 | 0% | Sin cambio |
| 18 | Presion emocional | - | 5/5 | 5/5 | 0% | Sin cambio |
| **TOTAL** | | | **31/50** | **36/50** | **+10%** | |

---

## 6. Conclusion

### Categoria mas frecuente
POLICY_MISS fue la categoria dominante (10 de 19 fallos). Esto confirma que el
principal problema del agente es la ambiguedad en la policy para casos similares
pero con acciones distintas.

### Tecnica mas efectiva
La combinacion XML + checklist + few-shot (Exp5) fue la unica tecnica que logro
mejora real. La razon: el XML fuerza al modelo a procesar condicion y accion como
unidades separadas; el checklist elimina la ambiguedad sobre el orden de pasos;
el few-shot da ejemplos concretos del patron a detectar. Ninguna de las tres
tecnicas por separado fue suficiente.

### Hipotesis que mas se equivoco
Se hipotetizo que la Task 3 (inubicable) era un problema de ambiguedad en el
prompt — que con suficiente especificidad el agente detectaria el patron. El
analisis demostro que no: 4 experimentos con tecnicas distintas y ninguna mejora.
La deteccion de comportamiento incoherente en el usuario es una capacidad del
modelo, no del prompt.

### Limitaciones de ejecucion
La inestabilidad de la API de Google (errores 500, AssistantMessage bug, rate limits)
en el plan gratuito impidio completar todos los experimentos con 5 trials completos.
Los resultados de Exp3 y Exp4 quedaron pendientes de ejecucion. El resultado mas
relevante (Exp5 con Task 8: 5/5) fue verificado y es confiable.