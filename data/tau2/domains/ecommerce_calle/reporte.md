# Reporte de Métricas y Experimentos — Entrega 2

## 1. Tabla de resultados pass^5 por tarea (ordenada de mayor % de falla a menor)

> **Nota metodológica:** Se utilizaron 5 corridas por tarea (pass^5) en lugar de 10,
> dado el límite de la API gratuita de Google AI Studio. La métrica pass^k se calcula
> como C(n_éxitos, k) / C(n_total, k). Los valores reportados corresponden al mejor
> prompt encontrado por tarea al finalizar la experimentación.

| Tarea | Descripción breve                              | Éxitos/5 | pass^5 | % falla |
|-------|------------------------------------------------|----------|--------|---------|
| 3     | Cancelación de pedido (confirmación en DB)     | 0/5      | 0.000  | 100%    |
| 8     | Devolución dentro de plazo (consistencia DB)   | 3/5      | 0.000  | 100%    |
| 12    | Verificación de propiedad de orden (rechazo)   | 5/5      | 1.000  | 0%      |
| 16    | (Tarea 16 — ver baseline)                      | 0/5      | 0.000  | 100%    |
| 21    | (Tarea 21 — ver baseline)                      | 0/5      | 0.000  | 100%    |
| 22    | (Tarea 22 — ver baseline)                      | 0/5      | 0.000  | 100%    |
| 23    | (Tarea 23 — ver baseline)                      | 0/5      | 0.000  | 100%    |
| 14    | (Tarea 14 — ver baseline)                      | 1/5      | 0.000  | 80%     |
| 19    | (Tarea 19 — ver baseline)                      | 2/5      | 0.000  | 60%     |
| 0     | (Tarea 0)                                      | 5/5      | 1.000  | 0%      |
| 1     | (Tarea 1)                                      | 5/5      | 1.000  | 0%      |
| 2     | (Tarea 2)                                      | 5/5      | 1.000  | 0%      |
| 4     | (Tarea 4)                                      | 5/5      | 1.000  | 0%      |
| 5     | (Tarea 5)                                      | 5/5      | 1.000  | 0%      |
| 6     | (Tarea 6)                                      | 5/5      | 1.000  | 0%      |
| 7     | (Tarea 7)                                      | 5/5      | 1.000  | 0%      |
| 9     | (Tarea 9)                                      | 5/5      | 1.000  | 0%      |
| 10    | (Tarea 10)                                     | 5/5      | 1.000  | 0%      |
| 11    | (Tarea 11)                                     | 5/5      | 1.000  | 0%      |
| 13    | (Tarea 13)                                     | 5/5      | 1.000  | 0%      |
| 15    | (Tarea 15)                                     | 5/5      | 1.000  | 0%      |
| 17    | (Tarea 17)                                     | 5/5      | 1.000  | 0%      |
| 18    | (Tarea 18)                                     | 5/5      | 1.000  | 0%      |
| 20    | (Tarea 20)                                     | 5/5      | 1.000  | 0%      |
| 24    | (Tarea 24)                                     | 5/5      | 1.000  | 0%      |

---

## 2. Análisis de las 3 tareas con peor rendimiento en el baseline

Las 3 tareas identificadas con pass^5 = 0.000 en la corrida inicial fueron la **Tarea 3**,
la **Tarea 8** y la **Tarea 12**. Se aplicaron en total 5 técnicas distintas distribuidas
sobre estas tres tareas.

---

### Tarea 3 — Cancelación de pedido (confirmación en DB)

**Falla típica del agente:**
El agente reportaba al usuario que el pedido había sido cancelado exitosamente
*antes* de que la base de datos confirmara la operación. La NL assertion del evaluador
detectaba esta desincronización: `cancel_order` se ejecutaba correctamente (Action Check
= 1.0) pero el DB Check fallaba (DB: 0.0), lo que resultaba en reward = 0.0 en todos
los intentos.

**Técnicas aplicadas:**

| Experimento | Técnica                         | Éxitos/5 | pass^5 | Cambio     |
|-------------|---------------------------------|----------|--------|------------|
| Baseline    | —                               | 0/5      | 0.000  | —          |
| Exp 1       | Aislamiento con etiquetas XML   | 0/5      | 0.000  | Sin mejora |
| Exp 3       | Planificación antes de actuar   | 0/5      | 0.000  | Sin mejora |

**Análisis de lo intentado:**

- **Exp 1 (XML tags):** Se introdujeron etiquetas XML para delimitar comandos del sistema
  y texto dirigido al usuario, con el objetivo de que el backend parseara el comando de
  cancelación sin ambigüedad. La técnica no tuvo efecto porque el problema no era de
  parsing sino de *orden de ejecución*: el agente seguía respondiendo antes de esperar
  la confirmación de la herramienta.

- **Exp 3 (Plan generation):** Se instruyó al agente para que generara un plan explícito
  paso a paso antes de ejecutar cualquier acción. La hipótesis era que al forzar el orden
  "1. llamar a `cancel_order` → 2. esperar confirmación → 3. informar al usuario", se
  eliminaría la desincronización. A pesar de ello, el modelo siguió anteponiendo la
  respuesta al usuario antes de recibir la confirmación de la DB. Gemma 3 parece tener
  dificultades estructurales para respetar dependencias temporales entre tool calls y
  generación de texto, incluso cuando se le indica explícitamente.

**Conclusión:** Ninguna técnica de prompting logró resolver esta tarea. La falla está
ligada a una limitación del modelo para esperar confirmación asíncrona de herramientas
antes de formular su respuesta, lo cual puede requerir cambios a nivel de arquitectura
del agente (e.g., forzar un ciclo de espera por tool result en el runner) más que
ajustes al prompt.

---

### Tarea 8 — Devolución dentro de plazo (inconsistencia DB/escenario)

**Falla típica del agente:**
Existía una contradicción entre lo que el escenario de la tarea indicaba ("ORD-002 está
dentro del plazo de devolución") y lo que los datos reales de la DB permitían inferir
(la fecha del pedido excedía los 30 días). El agente a veces rechazaba correctamente
basándose en las fechas reales, y otras veces aprobaba basándose en el escenario,
generando comportamiento inconsistente. En el baseline: 0/5.

**Técnicas aplicadas:**

| Experimento | Técnica                                  | Éxitos/5 | pass^5 | Cambio           |
|-------------|------------------------------------------|----------|--------|------------------|
| Baseline    | —                                        | 0/5      | 0.000  | —                |
| Exp 5       | Operational Precedence + corrección DB   | 3/5      | 0.000  | +3 éxitos (k=1)  |

**Análisis de lo intentado:**

- **Exp 5 (Operational Precedence Prompting + corrección de datos):** Se implementó una
  jerarquía de confianza explícita en el prompt: *resultados de herramientas > información
  explícita del escenario > inferencias del modelo*. Además, se corrigieron las fechas en
  la DB para que fueran coherentes con la política de 30 días, eliminando la causa raíz
  de la contradicción. El resultado fue una mejora notable: pass^1 subió de 0.000 a
  0.600 (3 de cada 5 intentos individuales resultaron exitosos). Sin embargo, pass^5
  permanece en 0.000 porque hubo 2 fallos entre los 5 trials, lo que hace imposible
  que todos sean éxito. La inconsistencia residual sugiere que Gemma 3 aún no aplica
  la jerarquía de forma completamente determinista.

**Conclusión:** La corrección de datos junto con la jerarquía de precedencia fue la
intervención más efectiva del conjunto de experimentos en términos de reducción de
fallas absolutas (0 → 3 éxitos), aunque la varianza sigue siendo alta.

---

### Tarea 12 — Verificación de propiedad de orden (rechazo con justificación)

**Falla típica del agente:**
El agente rechazaba la operación (sabía que no debía ejecutarla) pero fallaba en el
*cómo*: no especificaba explícitamente que el pedido ORD-004 pertenecía a otro usuario
(U003), que era exactamente lo que la NL assertion evaluaba. En el baseline: 0/5.

**Técnicas aplicadas:**

| Experimento | Técnica              | Éxitos/5 | pass^5 | Cambio              |
|-------------|----------------------|----------|--------|---------------------|
| Baseline    | —                    | 0/5      | 0.000  | —                   |
| Exp 2       | Chain of Thought     | 1/5      | 0.000  | +1 éxito (k=1=0.2) |
| Exp 4       | Few-Shot Learning    | 5/5      | 1.000  | **+5 éxitos ✓**    |

**Análisis de lo intentado:**

- **Exp 2 (Chain of Thought):** Forzar el razonamiento explícito ("¿A quién pertenece
  esta orden?" → "¿Coincide con el usuario actual?") mejoró la tasa de rechazo correcto,
  pero el modelo aún no siempre incluía el nombre del propietario real en su respuesta.
  El CoT fue un paso necesario pero insuficiente: resolvió el *qué hacer* pero no el
  *cómo comunicarlo*. pass^1 subió de 0.0 a 0.2 (1/5).

- **Exp 4 (Few-Shot Learning):** Proveer ejemplos de diálogos concretos donde el agente
  explicitaba "el pedido ORD-X pertenece al usuario U00Y, no a tu cuenta" fue la solución
  definitiva. El modelo imitó el patrón de respuesta exacto que el evaluador esperaba.
  Resultado: 5/5, pass^5 = 1.000. **Esta fue la única técnica que logró resultado perfecto
  en cualquier tarea de las 3 problemáticas.**

**Conclusión:** La combinación CoT (para el razonamiento) + Few-Shot (para el formato de
respuesta) fue la estrategia ganadora. El Few-Shot solo ya fue suficiente porque incorporaba
implícitamente el razonamiento correcto dentro de los ejemplos.

---

## 3. Conclusión general

### Limitaciones observadas en Gemma 3

1. **Dependencias temporales con herramientas:** Gemma 3 tiene dificultades para inhibir
   la generación de texto hasta haber recibido confirmación de una tool call. Incluso con
   instrucciones explícitas de "espera la confirmación antes de responder", el modelo
   tiende a anticipar la respuesta. Esto afectó directamente a la Tarea 3 de forma
   irresoluble con prompting.

2. **Inconsistencia ante fuentes de información contradictorias:** Cuando el escenario
   descrito en la tarea contradice los datos reales de las herramientas, el modelo
   muestra comportamiento variable e impredecible. La Tarea 8 evidenció que sin una
   jerarquía de confianza explícita y datos consistentes, el modelo "elige" su fuente
   de forma no determinista.

3. **Formato de respuesta sin ejemplos:** El modelo entiende cuándo rechazar pero no
   siempre sabe cómo redactar el rechazo con el nivel de detalle requerido por los
   evaluadores. Las instrucciones declarativas ("debes incluir X en tu respuesta") son
   menos efectivas que los ejemplos concretos.

### Técnicas que funcionaron mejor

- **Few-Shot Learning** fue la técnica más efectiva del experimento, logrando el único
  pass^5 = 1.000 entre las tareas problemáticas (Tarea 12, Exp 4). Su ventaja es que
  muestra el comportamiento esperado en lugar de describirlo, lo que encaja mejor con
  la forma en que los modelos de lenguaje aprenden.

- **Operational Precedence Prompting combinado con corrección de datos** fue la segunda
  técnica más efectiva, mejorando pass^1 de 0.0 a 0.6 en la Tarea 8. Establecer una
  jerarquía explícita de fuentes de verdad ayuda cuando el modelo enfrenta señales
  contradictorias.

- **Chain of Thought** fue útil como técnica de apoyo para que el agente valide
  condiciones antes de actuar, pero no fue suficiente por sí sola para resolver los
  casos donde el problema era de *formato* de respuesta.

### Técnicas que no funcionaron

- **XML tags** no tuvo ningún impacto sobre la Tarea 3. El problema de fondo era de
  sincronización con herramientas, no de parsing del output del agente.

- **Plan generation before acting** tampoco resolvió la Tarea 3. Gemma 3 generaba el
  plan correcto en texto, pero no lo respetaba en la ejecución real.

### Aprendizaje principal

La lección más importante de estos experimentos es que **el prompting tiene límites
duros cuando el problema es estructural**. En la Tarea 3, ninguna técnica funcionó
porque el modelo no puede bloquear su generación hasta recibir una respuesta asíncrona
de una herramienta — esto es una limitación del runner o de la arquitectura, no del
prompt. En contraste, cuando el problema es de *comportamiento lingüístico* (cómo
formular un rechazo, qué información incluir), el Few-Shot Learning es altamente
efectivo porque le da al modelo un patrón concreto que imitar.
