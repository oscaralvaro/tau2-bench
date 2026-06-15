# Reporte Entrega 3 - estaciondeservicio_Rivera

Nombre: Diego Eduardo Rivera Rodriguez

## 1. Contexto

El dominio `estaciondeservicio_Rivera` representa un bot B2B de atencion al cliente para recepcionar y procesar pedidos de delivery de combustibles y lubricantes. El bot consulta catalogo y stock, registra clientes, direcciones, metodos de pago, ordenes, pagos, facturas, reclamos y operaciones sensibles con verificacion SMS.

Para Entrega 3 se seleccionaron las 10 tareas mas dificiles del dominio y se ejecuto una corrida `pass^5` diagnostica. La seleccion esta guardada en:

- `data/tau2/domains/estaciondeservicio_Rivera/top10_tareas_dificiles.json`

La corrida baseline se guardo con el nombre esperado por la entrega:

- `data/simulations/sim_e3_baseline.json`

Tambien se conserva la copia original generada por la corrida:

- `data/simulations/rivera_top10_dificiles_pass5_v2.json`

## 2. Resultado baseline E3

La corrida baseline E3 contiene 50 simulaciones: 10 tareas por 5 trials. Se completaron todas las simulaciones. El resultado fue 40/50 exitosas.

| Tarea | Caso | Baseline pass^5 | Fallas | Lectura |
|---:|---|---:|---:|---|
| 4 | Pedido de lubricante asociado | 0/5 | 5 | Fallo por producto/cantidad no canonicos |
| 13 | Metodo de pago nuevo + orden | 0/5 | 5 | Fallo por campos incompletos/formato |
| 1 | Registro de cliente nuevo | 5/5 | 0 | Estable |
| 2 | Nueva direccion + orden | 5/5 | 0 | Estable |
| 6 | Cambio de metodo + pago | 5/5 | 0 | Estable, pero complejo |
| 12 | Pago total efectivo | 5/5 | 0 | Estable |
| 16 | Actualizacion de cliente con SMS | 5/5 | 0 | Estable |
| 18 | Registro de reclamo | 5/5 | 0 | Estable |
| 20 | Cancelacion con SMS | 5/5 | 0 | Estable |
| 21 | SMS incorrecto | 5/5 | 0 | Estable |

## 2.1 Resultado final E3 despues de mejoras

Archivo:

- `data/simulations/sim_e3_final.json`

La corrida final E3 tambien contiene 50 simulaciones. Se completaron todas. El resultado fue 45/50 exitosas.

| Tarea | Caso | Final pass^5 | Fallas | Lectura |
|---:|---|---:|---:|---|
| 13 | Metodo de pago nuevo + orden | 0/5 | 5 | Falla residual por factura virtual no visible en la conversacion |
| 1 | Registro de cliente nuevo | 5/5 | 0 | Estable |
| 2 | Nueva direccion + orden | 5/5 | 0 | Estable |
| 4 | Pedido de lubricante asociado | 5/5 | 0 | Corregida respecto al baseline |
| 6 | Cambio de metodo + pago | 5/5 | 0 | Estable |
| 12 | Pago total efectivo | 5/5 | 0 | Estable |
| 16 | Actualizacion de cliente con SMS | 5/5 | 0 | Estable |
| 18 | Registro de reclamo | 5/5 | 0 | Estable |
| 20 | Cancelacion con SMS | 5/5 | 0 | Estable |
| 21 | SMS incorrecto | 5/5 | 0 | Estable |

Comparacion baseline vs final:

| Tarea | Baseline pass^5 | Final pass^5 | Cambio |
|---:|---:|---:|---|
| 4 | 0/5 | 5/5 | Mejora completa |
| 13 | 0/5 | 0/5 | Pendiente por factura virtual |
| 1 | 5/5 | 5/5 | Se mantiene |
| 2 | 5/5 | 5/5 | Se mantiene |
| 6 | 5/5 | 5/5 | Se mantiene |
| 12 | 5/5 | 5/5 | Se mantiene |
| 16 | 5/5 | 5/5 | Se mantiene |
| 18 | 5/5 | 5/5 | Se mantiene |
| 20 | 5/5 | 5/5 | Se mantiene |
| 21 | 5/5 | 5/5 | Se mantiene |

## 3. Taxonomia de fallas

Las fallas de la corrida final estan detalladas en:

- `data/tau2/domains/estaciondeservicio_Rivera/failure_taxonomy.json`

Distribucion por categoria:

| Categoria | Cantidad | Tareas |
|---|---:|---|
| INCOMPLETE | 5 | 13 |
| TOOL_MISUSE | 0 | - |
| POLICY_MISS | 0 | - |
| HALLUCINATION | 0 | - |
| INJECTION_VULN | 0 | - |
| IDENTITY_BYPASS | 0 | - |
| OTHER | 0 | - |

Conclusion de la taxonomia final: la categoria dominante fue `INCOMPLETE`. El agente creo la orden correctamente en casi todos los campos, pero registro `solicitar_factura_virtual=false` y `email_factura=null` porque el usuario no menciono la factura durante la conversacion. Se corrigio el escenario para que el usuario declare proactivamente la factura virtual a `facturacion@riveranorte.pe`.

## 4. Analisis de las 3 tareas mas fragiles

### Tarea 4: pedido de lubricante asociado

Falla observada: en los 5 trials, el agente registro `item_0018` y cantidad `2`, aunque la evaluacion esperaba `item_0001` y cantidad `1`. La asociacion con `order_fuel_9100` si fue correcta.

Causa raiz: la task decia "un producto lubricante", pero el expected action era exacto. El modelo hizo una inferencia razonable desde el catalogo, pero no coincidio con la evaluacion.

Correcciones aplicadas:

- Se hizo explicito en `tasks.json` que el usuario quiere `1` unidad de `ACEITE SINTETICO 2T PT HIGH QUALITY`, `item_0001`.
- Se reforzo `policy.md` para pedir producto y cantidad exactos antes de registrar lubricantes asociados.
- Esta correccion se mide en `policy_e3_exp2.md`, asociado a `sim_e3_final.json`.

### Tarea 13: metodo de pago nuevo + orden

Falla observada en baseline: el agente registro correctamente el metodo de pago, pero la orden omitio `solicitar_factura_virtual`, `email_factura`, `observaciones` y en varios trials uso fecha con sufijo `Z`.

Causa raiz: el modelo dependio de defaults de la tool y no completo todos los argumentos canonicos que compara el evaluador.

Correcciones aplicadas:

- Se reforzo `policy.md` para usar el `id` devuelto por `register_payment_method`.
- Se agrego regla de fecha local ISO sin `Z`.
- Se obligo a completar factura y observaciones de forma explicita.
- Estos ajustes forman parte de `policy_e3_exp2.md`, asociado a `sim_e3_final.json`.

Falla residual en `sim_e3_final.json`: despues de corregir fecha y observaciones, la task 13 siguio fallando porque el usuario simulado no dijo en el dialogo que queria factura virtual. El expected action si exige `solicitar_factura_virtual=true` y `email_factura=facturacion@riveranorte.pe`.

Correccion adicional aplicada despues de la corrida final:

- Se ajusto `tasks.json` para que el usuario mencione proactivamente la factura virtual y el correo cuando entregue los datos del pedido.
- Se reforzo `tasks.json`, `policy.md`, `tools.py` y `policy_e3_exp3.md` para que el tipo de pago use el valor canonico `bank_transfer` y no variantes en lenguaje natural como "transferencia bancaria".
- Se documento este ajuste residual en `policy_e3_exp3.md`; falta correr la simulacion asociada para convertirlo en evidencia final.

### Tarea 6: cambio de metodo de pago y pago total

Estado baseline: paso 5/5, pero se mantiene como tercera tarea fragil por complejidad estructural. Usa verificacion SMS, cambio de metodo, pago y consulta final de estado.

Riesgo principal: aunque no fallo en esta corrida, tiene varias dependencias. Un error en orden de tools, SMS o grounding final puede romper DB o action checks.

Mejoras mantenidas:

- Reglas SMS ya integradas en `policy.md`.
- Checklist general de escritura documentado dentro del analisis, sin crear un experimento adicional sin simulacion propia.

## 5. Experimentos de prompt

Cada simulacion guardada corresponde a un experimento o evidencia de experimento. Por eso se dejaron solo tres archivos `policy_e3_exp`, no seis.

| Experimento | Simulacion asociada | Archivo | Tecnica principal | Objetivo |
|---|---|---|---|
| 1 | `sim_e3_baseline.json` | `prompts/policy_e3_exp1.md` | Diagnostico baseline | Medir el agente antes de mejoras E3 |
| 2 | `sim_e3_final.json` | `prompts/policy_e3_exp2.md` | Claridad + grounding + normalizacion | Corregir task 4 y reducir fallas de task 13 |
| 3 | Pendiente post-final | `prompts/policy_e3_exp3.md` | Especificidad de factura virtual | Corregir la falla residual de task 13 |

La tecnica mas efectiva para los fallos observados fue combinar especificidad de task con grounding de argumentos antes de la tool. El error dominante no era que el modelo ignorara la policy, sino que completaba acciones validas de negocio con argumentos no identicos a los esperados por la evaluacion.

## 6. Cambios aplicados

Archivos modificados para corregir las causas raiz:

- `data/tau2/domains/estaciondeservicio_Rivera/policy.md`
- `data/tau2/domains/estaciondeservicio_Rivera/tasks.json`
- `src/tau2/domains/estaciondeservicio_Rivera/tools.py`

Archivos agregados para Entrega 3:

- `data/tau2/domains/estaciondeservicio_Rivera/failure_taxonomy.json`
- `data/tau2/domains/estaciondeservicio_Rivera/reporte_e3.md`
- `data/tau2/domains/estaciondeservicio_Rivera/prompts/policy_e3_exp1.md`
- `data/tau2/domains/estaciondeservicio_Rivera/prompts/policy_e3_exp2.md`
- `data/tau2/domains/estaciondeservicio_Rivera/prompts/policy_e3_exp3.md`

## 7. Pendiente de evidencia final

Despues de estos cambios, corresponde re-ejecutar la tarea 13, o idealmente todo el top 10, para generar una nueva simulacion final E3 con la correccion de factura virtual.

Comando recomendado para corroborar solo la tarea corregida:

```bash
python -m tau2.cli run \
  --domain estaciondeservicio_Rivera \
  --task-ids 13 \
  --agent-llm gemini/gemma-4-26b-a4b-it \
  --user-llm gemini/gemma-4-26b-a4b-it \
  --num-trials 5 \
  --max-concurrency 2 \
  --save-to sim_e3_final_task13_v2 \
  --agent-llm-args '{"temperature": 0.0, "rate_limit_requests_per_minute": 14, "rate_limit_requests_per_day": 14000, "rate_limit_tokens_per_minute": 150000, "rate_limit_bucket": "google-free-tier-agent", "rate_limit_token_reserve": 750}' \
  --user-llm-args '{"temperature": 0.0, "rate_limit_requests_per_minute": 14, "rate_limit_requests_per_day": 14000, "rate_limit_tokens_per_minute": 150000, "rate_limit_bucket": "google-free-tier-user", "rate_limit_token_reserve": 750}'
```

Comando recomendado para la evidencia final completa del top 10:

```bash
python -m tau2.cli run \
  --domain estaciondeservicio_Rivera \
  --task-ids 6 20 16 21 18 2 13 12 4 1 \
  --agent-llm gemini/gemma-4-26b-a4b-it \
  --user-llm gemini/gemma-4-26b-a4b-it \
  --num-trials 5 \
  --max-concurrency 2 \
  --save-to sim_e3_final \
  --agent-llm-args '{"temperature": 0.0, "rate_limit_requests_per_minute": 14, "rate_limit_requests_per_day": 14000, "rate_limit_tokens_per_minute": 150000, "rate_limit_bucket": "google-free-tier-agent", "rate_limit_token_reserve": 750}' \
  --user-llm-args '{"temperature": 0.0, "rate_limit_requests_per_minute": 14, "rate_limit_requests_per_day": 14000, "rate_limit_tokens_per_minute": 150000, "rate_limit_bucket": "google-free-tier-user", "rate_limit_token_reserve": 750}'
```
