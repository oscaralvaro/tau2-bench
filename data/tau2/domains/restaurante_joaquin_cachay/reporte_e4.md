# Reporte - Entrega 4

## Objetivo

Esta entrega incorpora recuperacion de politica con RAG y soporte para `think` en el dominio `restaurante_joaquin_cachay`, sin cambiar manualmente el codigo entre condiciones experimentales.

## Cambios implementados

Archivos modificados en esta iteracion:

- `src/tau2/domains/restaurante_joaquin_cachay/tools.py`
- `src/tau2/domains/restaurante_joaquin_cachay/environment.py`
- `scripts/restaurante_joaquin_cachay/run_e4_B_headers_k3.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_C_fixed_k3.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_D_best_think.ps1`
- `tests/test_domains/test_restaurante_joaquin_cachay/test_tools_restaurante_joaquin_cachay.py`
- `tests/test_domains/test_restaurante_joaquin_cachay/test_env_args_restaurante_joaquin_cachay.py`

Resumen tecnico:

- el toolkit del dominio hereda de `RAGToolKit`
- `get_environment()` acepta `chunking_strategy`, `retrieval_k`, `use_think` y `use_rag`
- el indice se construye con `ChromaPolicyIndex`
- cuando `use_rag=true`, el entorno sirve `policy_rag.md`
- cuando `use_think=true`, se agrega `THINK_INSTRUCTION`
- `retrieve_policy` usa cache persistente por estrategia de chunking
- el replay/evaluator vuelve a alinear el contexto de `retrieve_policy` antes de rehidratar la trayectoria, evitando mismatches cuando el framework recompone el entorno sin reenviar `env_args`

Hardening operativo adicional:

- los scripts de PowerShell ahora serializan JSON con `ConvertTo-Json -Compress`
- los scripts B/C/D ejecutan `py` via `System.Diagnostics.Process` para no romper los argumentos JSON
- C y D quedaron con `num_retries = 3` para tolerar errores transitorios de Gemini sin esconder cuotas agotadas
- D fuerza `use_rag=true` explicitamente

## Validacion local

Comando ejecutado:

```powershell
py -X utf8 -m pytest tests\test_domains\test_restaurante_joaquin_cachay\test_tools_restaurante_joaquin_cachay.py tests\test_domains\test_restaurante_joaquin_cachay\test_env_args_restaurante_joaquin_cachay.py -q
```

Resultado:

- `48 passed, 4 warnings`

## Split usado en E4

Se reutiliza `base_top10hard`, definido en [split_tasks.json](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\split_tasks.json), porque corresponde a las 10 tareas mas dificiles detectadas en E3.

## Condiciones experimentales

### A. Baseline sin RAG

Archivo:

- [sim_e4_A_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e4_A_baseline.json)

Origen:

- copia directa de [sim_e3_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline.json)

Resultado confirmado:

- tareas: `10`
- corridas: `50/50`
- corridas exitosas: `10/50`
- `average reward`: `0.2000`

### B. Headers + k=3 + sin think

Script:

- [run_e4_B_headers_k3.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_B_headers_k3.ps1)

Archivo:

- [sim_e4_B_headers_k3.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e4_B_headers_k3.json)

Resultado confirmado:

- tareas: `10`
- corridas: `50/50`
- corridas exitosas: `1/50`
- `average reward`: `0.0200`

Lectura:

- `headers + k=3` no mejoro el baseline
- fue claramente peor que A
- la unica senal positiva residual quedo en `restaurant_order_takeout_1`

### C. Fixed_200 + k=3 + sin think

Script:

- [run_e4_C_fixed_k3.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_C_fixed_k3.ps1)

Archivo parcial:

- [sim_e4_C_fixed_k3.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e4_C_fixed_k3.json)

Estado observado:

- tareas declaradas: `10`
- corridas guardadas: `10/50`
- corridas exitosas: `0/10`
- `average reward` parcial: `0.0000`

Lectura:

- no hay evidencia de mejora hasta donde alcanzo a ejecutarse
- la condicion quedo tecnicamente implementada, pero experimentalmente inconclusa por cuota/estabilidad del proveedor

### D. Mejor chunking + think

Script:

- [run_e4_D_best_think.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_D_best_think.ps1)

Archivo parcial:

- [sim_e4_D_best_think.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e4_D_best_think.json)

Estado observado:

- tareas declaradas: `10`
- corridas guardadas: `35/50`
- corridas exitosas: `0/35`
- `average reward` parcial: `0.0000`

Lectura:

- D tampoco muestra mejora en las corridas que si llegaron a guardarse
- varios relanzamientos quedaron bloqueados por cuota diaria de Gemini (`429 RESOURCE_EXHAUSTED`) o procesos colgados sin generar nuevas simulaciones

## Tabla de resultados

| Condicion | Chunking | retrieval_k | think | Corridas guardadas | Average reward | Estado |
|---|---|---:|---|---:|---:|---|
| A | sin RAG | n/a | no | 50/50 | 0.2000 | cerrada |
| B | headers | 3 | no | 50/50 | 0.0200 | cerrada |
| C | fixed_200 | 3 | no | 10/50 | 0.0000 | parcial |
| D | headers + think | 3 | si | 35/50 | 0.0000 | parcial |

## Analisis

### Que si se puede afirmar con evidencia

1. La implementacion de E4 quedo hecha y validada por tests.
2. La condicion B demuestra que agregar RAG no mejora automaticamente este dominio.
3. El mejor resultado confirmado sigue siendo el baseline sin RAG.
4. Las condiciones C y D quedaron experimentalmente inconclusas por limitaciones operativas del proveedor, no por ausencia de implementacion.

### Comparacion confirmada A vs B

| Tarea | A | B | Lectura |
|---|---:|---:|---|
| `restaurant_adversarial_vip_unavailable_item_1` | `5/5` | `0/5` | regresion clara bajo RAG con `headers` |
| `restaurant_order_takeout_1` | `5/5` | `1/5` | sigue siendo la unica tarea con senal positiva en B, pero muy por debajo de A |
| resto del split | `0/5` | `0/5` | B no recupera ninguna tarea adicional |

### Interpretacion tecnica

La degradacion de B es consistente con esta hipotesis:

- `retrieve_policy` agrega pasos y latencia donde el baseline ya resolvia con la politica completa inline
- `headers` probablemente recupera chunks demasiado amplios para tareas donde importan frases exactas como `no disponible`, `cancelado`, `cerrado` o `incorrecto`
- al pasar de politica completa a `policy_rag.md` + retrieval, el equilibrio del prompt cambia y el agente pierde estabilidad en tareas que ya estaban resueltas

## Bloqueos operativos identificados

Los bloqueos dominantes de E4 fueron operativos:

- Windows venia por defecto en `cp1252`, por lo que hubo que fijar `utf-8` y usar `py -X utf8`
- PowerShell rompia los JSON inline de `--agent-llm-args`; por eso los scripts se reescribieron
- Gemini free tier devolvio `429 RESOURCE_EXHAUSTED` al agotar cuota diaria
- algunos relanzamientos quedaron colgados sin escribir nuevas simulaciones ni logs finales
- cuando una corrida queda totalmente `skipped`, `tau2` puede fallar despues en metricas sobre DataFrame vacio; ese bug es del framework, no del dominio

## Conclusion honesta para la entrega

La conclusion correcta para reportar hoy es esta:

> La implementacion de RAG y `think` para `restaurante_joaquin_cachay` quedo completada y validada localmente con tests. Sin embargo, la evaluacion experimental completa de E4 no pudo cerrarse por restricciones operativas del proveedor Gemini en free tier. La unica comparacion cerrada y confiable es A vs B, donde `headers + k=3` degrada el rendimiento respecto al baseline sin RAG (`0.0200` vs `0.2000`). Las condiciones C y D quedaron parciales y, hasta donde alcanzaron a ejecutarse, no mostraron mejora.

## Estado de cierre

Si se evalua estrictamente por implementacion:

- E4 de codigo: completada
- tests relevantes: pasando
- scripts B/C/D: corregidos y reproducibles en Windows

Si se evalua estrictamente por simulaciones completas:

- A: completa
- B: completa
- C: parcial
- D: parcial

En otras palabras:

- lo pendiente ya no es de codigo base del dominio
- lo pendiente es capacidad de corrida estable con cuota suficiente del proveedor
