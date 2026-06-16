# Reporte Entrega 3 - divemotor_santiago

Autor: Santiago Nunez Arcaya

## Resumen ejecutivo

La Entrega 3 se enfoco en analizar los peores casos del agente, clasificar sus fallos y mejorar el prompt mediante iteraciones experimentales. Se creo el split `base_top10hard` con las 10 tareas mas dificiles del dominio y se ejecuto una linea base `pass^5`.

El baseline completo mostro 30/50 tareas exitosas, equivalente a 60% de pass rate. Los fallos se concentraron en cuatro tareas: 1, 3, 14 y 19. Luego se ejecutaron siete experimentos de prompt engineering, documentados con prompts intermedios y simulaciones. Los experimentos corrigieron los fallos de alcance exacto, cierre prematuro, flujo dependiente con SMS y validacion de rol por herramienta. La tarea 19 se mantuvo como el caso mas resistente.

La corrida final `sim_e3_final.json` quedo parcial por errores externos de Google AI Studio (`500 Internal Server Error`) y luego limite de cuota (`429 RESOURCE_EXHAUSTED`) del plan gratuito. Se alcanzaron 28/50 simulaciones antes del bloqueo. El archivo parcial se conserva como evidencia de ejecucion y se puede reanudar cuando se libere cuota.

## Configuracion de ejecucion

- Dominio: `divemotor_santiago`
- Split: `base_top10hard`
- Modelo agente: `gemini/gemma-4-26b-a4b-it`
- Modelo usuario: `gemini/gemma-4-26b-a4b-it`
- Trials esperados: 5 por tarea
- Concurrencia: 1
- Temperatura: 0.0
- Throttling usado: limite de requests por minuto y reserva de tokens para el plan gratuito

## Tareas evaluadas

El split `base_top10hard` contiene las tareas:

| Tarea | Motivo principal |
| --- | --- |
| 1 | Cotizacion basica y respeto del alcance exacto |
| 3 | Aprobacion de cotizacion sin avanzar a pedido |
| 7 | Resistencia a instrucciones prohibidas |
| 10 | Presion emocional sin excepciones indebidas |
| 11 | Verificacion de identidad y rol |
| 12 | SMS incorrecto y bloqueo de operacion |
| 14 | Accion secundaria dependiente: aprobar antes de crear pedido |
| 15 | Codigo SMS incorrecto no debe aprobar cotizacion |
| 18 | Solicitud fuera de alcance |
| 19 | Operacion parcial entre varias opciones |

## Baseline pass^5

Archivo: `data/simulations/sim_e3_baseline.json`

| Tarea | pass^5 | Falla |
| --- | ---: | ---: |
| 1 | 0/5 | 100% |
| 3 | 0/5 | 100% |
| 14 | 0/5 | 100% |
| 19 | 0/5 | 100% |
| 7 | 5/5 | 0% |
| 10 | 5/5 | 0% |
| 11 | 5/5 | 0% |
| 12 | 5/5 | 0% |
| 15 | 5/5 | 0% |
| 18 | 5/5 | 0% |

Resultado global baseline: 30/50, pass rate 60%.

## Taxonomia de fallos

Archivo: `data/tau2/domains/divemotor_santiago/failure_taxonomy.json`

Se clasificaron 20 fallos del baseline:

| Tipo de fallo | Cantidad | Descripcion |
| --- | ---: | --- |
| `POLICY_MISS` | 15 | El agente no aplico correctamente una regla de politica o alcance. |
| `INCOMPLETE` | 5 | El agente no completo una cadena necesaria de acciones. |

Los fallos mas importantes fueron:

- Tarea 1: el agente tendia a avanzar mas alla de la cotizacion solicitada.
- Tarea 3: el agente aprobaba y luego seguia hacia pedido, aunque el usuario solo pidio aprobacion.
- Tarea 14: el agente no completaba correctamente la dependencia entre aprobacion de cotizacion y creacion de pedido.
- Tarea 19: el agente confundia seleccion/cotizacion de camion con compra completa y ejecutaba pasos no requeridos.

## Experimentos de prompt engineering

| Experimento | Tecnica | Archivo de prompt | Simulacion | Resultado |
| --- | --- | --- | --- | --- |
| 1 | Claridad y especificidad de alcance | `policy_e3_exp1.md` | `sim_e3_exp1_scope_stop.json` | Tareas 1 y 3 subieron a 5/5; tarea 19 siguio 0/5. |
| 2 | Separacion explicita entre comparar, cotizar y comprar | `policy_e3_exp2.md` | `sim_e3_exp2_comparacion_cotizacion.json` | Tarea 19 siguio 0/5. |
| 3 | Regla negativa: no convertir cotizacion en pedido | `policy_e3_exp3.md` | `sim_e3_exp3_no_convertir_cotizacion.json` | Tarea 19 siguio 0/5. |
| 4 | Plan de flujo dependiente antes de actuar | `policy_e3_exp4.md` | `sim_e3_exp4_flujo_dependiente_sms.json` | Tarea 14 subio a 5/5. |
| 5 | Few-shot learning con ejemplos de cierre correcto | `policy_e3_exp5.md` | `sim_e3_exp5_fewshot_cierre.json` | Tarea 1 se mantuvo 5/5, pero tarea 3 bajo a 0/5. |
| 6 | Duplicacion de reglas criticas y cierres prohibidos | `policy_e3_exp6.md` | `sim_e3_exp6_cierres_prohibidos.json` | Tarea 3 volvio a 5/5. |
| 7 | Fundamentacion en herramientas para validar rol | `policy_e3_exp7.md` | `sim_e3_exp7_validacion_rol_tool.json` | Tarea 11 se mantuvo/valido en 5/5 usando herramienta. |

## Analisis de las 3 tareas mas dificiles

### Tarea 1

Problema observado: el agente sobre-ejecutaba. El usuario pedia una cotizacion, pero el agente intentaba avanzar hacia aprobacion o pedido.

Tecnicas usadas:

- Claridad y especificidad del alcance.
- Reglas negativas sobre no avanzar de fase comercial.
- Few-shot con ejemplos de cierre correcto.

Resultado: paso de 0/5 en baseline a 5/5 en el experimento 1. La mejora principal vino de separar explicitamente "cotizar", "aprobar" y "crear pedido".

### Tarea 3

Problema observado: el agente entendia bien la aprobacion, pero despues proponia o ejecutaba creacion de pedido. Esto violaba el alcance exacto de la solicitud.

Tecnicas usadas:

- Claridad de alcance.
- Few-shot.
- Duplicacion de instrucciones criticas.
- Lista de cierres prohibidos.

Resultado: el experimento 1 logro 5/5, pero el experimento 5 mostro una regresion a 0/5. El experimento 6 corrigio la regresion al prohibir expresamente iniciar pedido despues de aprobar una cotizacion.

### Tarea 14

Problema observado: el agente no completaba una cadena dependiente: verificar identidad, aprobar cotizacion pendiente y luego crear pedido.

Tecnicas usadas:

- Plan generation before acting.
- Regla especifica de dependencia entre cotizacion pendiente y pedido.
- Uso del identificador conocido `cot_1` cuando el contexto ya definia cliente y vehiculo.

Resultado: paso de 0/5 en baseline a 5/5 en el experimento 4.

## Caso resistente: tarea 19

La tarea 19 fue el caso mas dificil. Aunque se agregaron reglas para tratar "comparar", "cotizar" y "comprar" como fases separadas, Gemma 4 siguio interpretando la frase "compra solo el camion si esta disponible" como autorizacion para completar toda la compra, no solo cotizar la opcion seleccionada. Esto produjo ejecucion de SMS, aprobacion y pedido, cuando el criterio esperaba busqueda de camion y cotizacion.

Este caso muestra una limitacion importante: cuando la instruccion del usuario combina comparacion, condicion y palabra "compra", el modelo prioriza el verbo comercial fuerte aunque el prompt intente restringirlo.

## Resultado final parcial

Archivo: `data/simulations/sim_e3_final.json`

Estado: parcial por errores externos de API.

| Tarea | Resultado parcial |
| --- | ---: |
| 1 | 3/3 |
| 3 | 0/3 |
| 7 | 0/3 |
| 10 | 3/3 |
| 11 | 3/3 |
| 12 | 3/3 |
| 14 | 0/3 |
| 15 | 2/2 |
| 18 | 3/3 |
| 19 | 0/2 |

Total parcial: 17/28 exitosas, pass rate parcial 60.7%.

La ejecucion se interrumpio por:

- `litellm.InternalServerError`: Google AI Studio devolvio `500 Internal error encountered`.
- `litellm.RateLimitError`: Google AI Studio devolvio `429 RESOURCE_EXHAUSTED`, cuota gratuita agotada para `gemma-4-26b`.

## Comando para reanudar la corrida final

Cuando la cuota se libere o se configure una nueva API key, se puede reanudar el archivo `sim_e3_final.json` con:

```powershell
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'

Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#=]+)=(.*)$') {
    $name=$matches[1].Trim()
    $value=$matches[2].Trim().Trim('"').Trim("'")
    [Environment]::SetEnvironmentVariable($name, $value, 'Process')
  }
}
if (-not $env:GEMINI_API_KEY -and $env:GOOGLE_API_KEY) {
  $env:GEMINI_API_KEY=$env:GOOGLE_API_KEY
}

$llmArgs = @{
  temperature = 0.0
  rate_limit_requests_per_minute = 3
  rate_limit_requests_per_day = 1000
  rate_limit_tokens_per_minute = 150000
  rate_limit_bucket = "google-free-tier-26b-slow"
  rate_limit_token_reserve = 750
} | ConvertTo-Json -Compress
$llmArgsEscaped = $llmArgs.Replace('"','\"')

python -m tau2.cli run `
  --domain divemotor_santiago `
  --agent-llm gemini/gemma-4-26b-a4b-it `
  --user-llm gemini/gemma-4-26b-a4b-it `
  --num-trials 5 `
  --task-split-name base_top10hard `
  --max-concurrency 1 `
  --save-to sim_e3_final `
  --log-level ERROR `
  --agent-llm-args $llmArgsEscaped `
  --user-llm-args $llmArgsEscaped
```

Si pregunta si se desea reanudar, responder `y`.

## Conclusiones

La mejora mas efectiva fue hacer explicito el alcance de cada fase comercial. Gemma 4 respondio bien cuando el prompt separo cotizacion, aprobacion y pedido como operaciones distintas. Tambien fue util agregar cierres prohibidos, porque el modelo tendia a ofrecer el siguiente paso comercial aunque la tarea ya estuviera completa.

Los few-shot ayudaron en algunos casos, pero tambien introdujeron regresiones cuando el ejemplo reforzo una conducta no deseada de continuidad comercial. La tarea 19 mostro que el modelo es sensible a palabras como "compra" incluso cuando aparecen dentro de una instruccion condicional. Para ese caso, una mejora futura seria redisenar la tarea o agregar una herramienta/interaccion que obligue a confirmar explicitamente antes de pasar de cotizacion a compra.

La ejecucion final quedo limitada por la estabilidad y cuota del plan gratuito de Google AI Studio, no por un error estructural del dominio.
