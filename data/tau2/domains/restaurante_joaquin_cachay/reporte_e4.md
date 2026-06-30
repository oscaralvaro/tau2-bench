# Reporte - Entrega 4

## Objetivo

Esta entrega agrega recuperacion de politica con RAG y soporte para `think` en el dominio `restaurante_joaquin_cachay`.

## Cambios implementados

Archivos principales modificados:

- `src/tau2/domains/restaurante_joaquin_cachay/tools.py`
- `src/tau2/domains/restaurante_joaquin_cachay/environment.py`
- `src/tau2/domains/restaurante_joaquin_cachay/utils.py`
- `data/tau2/domains/restaurante_joaquin_cachay/policy_rag.md`
- `tests/test_domains/test_restaurante_joaquin_cachay/test_tools_restaurante_joaquin_cachay.py`
- `tests/test_domains/test_restaurante_joaquin_cachay/test_env_args_restaurante_joaquin_cachay.py`

Resumen tecnico:

- el toolkit del dominio ahora hereda de `RAGToolKit`
- `get_environment()` acepta `chunking_strategy`, `retrieval_k`, `use_think` y `use_rag`
- el indice de politica se construye con `ChromaPolicyIndex`
- cuando `use_rag=true`, el agente usa `policy_rag.md`
- cuando `use_think=true`, se agrega `THINK_INSTRUCTION`
- la lectura de prompts del dominio ahora usa `encoding="utf-8"` explicito
- `get_tools()` publica descripciones cortas de herramientas para reducir el contexto operativo

Hardening adicional util para E4:

- el simulador de usuario quedo limitado a las herramientas SMS que realmente necesita
- los scripts de PowerShell quedaron reescritos para serializar JSON con `ConvertTo-Json` y ejecutar `tau2` via `Start-Process`
- las corridas nuevas reducen reintentos en 429 para fallar rapido cuando la cuota diaria ya esta agotada
- el script de D ahora pasa `use_rag=true` explicitamente, porque en este dominio el default es `false`

## Validacion local

Comando ejecutado:

```powershell
py -X utf8 -m pytest tests\test_domains\test_restaurante_joaquin_cachay\test_tools_restaurante_joaquin_cachay.py tests\test_domains\test_restaurante_joaquin_cachay\test_env_args_restaurante_joaquin_cachay.py -q
```

Resultado:

- `41 passed`

## Split usado en E4

Se reutiliza `base_top10hard`, definido en [split_tasks.json](C:\Users\Joaquin\tau2-bench\data\tau2\domains\restaurante_joaquin_cachay\split_tasks.json), porque corresponde a las 10 tareas mas dificiles detectadas en E3.

## Condiciones experimentales

### A. Baseline sin RAG

Archivo:

- [sim_e4_A_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e4_A_baseline.json)

Origen:

- copia directa de [sim_e3_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline.json)

Resultado base heredado:

- tareas: `10`
- corridas: `50`
- `average reward`: `0.2000`

### B. Headers + k=3 + sin think

Script:

- [run_e4_B_headers_k3.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_B_headers_k3.ps1)

Archivo actual:

- [sim_e4_B_headers_k3.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e4_B_headers_k3.json)

Estado real:

- el archivo existe
- declara `10` tareas y `5` trials
- solo quedaron persistidas `2` simulaciones antes de agotarse la cuota externa
- por eso todavia no sirve como resultado final comparable de la condicion B

### C. Fixed_200 + k=3 + sin think

Script:

- [run_e4_C_fixed_k3.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_C_fixed_k3.ps1)

Archivo esperado:

- `sim_e4_C_fixed_k3.json`

Estado:

- script listo
- corrida completa aun no guardada

Decision actual:

- para la condicion C se dejo preparada la variante `fixed_200`
- la idea es probar primero chunks mas pequenos sobre una politica de tamano medio

### D. Mejor chunking + think

Script:

- [run_e4_D_best_think.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_D_best_think.ps1)

Archivo esperado:

- `sim_e4_D_best_think.json`

Notas:

- el script deja `headers` por defecto en `$bestChunkingStrategy`
- si `fixed_200` supera a `headers` en B/C, solo hay que cambiar ese valor antes de correr D
- el script ya fuerza `use_rag=true` de manera explicita

## Estado real de las simulaciones

| Condicion | Estado | Observacion |
|---|---|---|
| A | lista | derivada desde `sim_e3_baseline.json` |
| B | parcial | archivo existente, pero solo con `2` simulaciones persistidas |
| C | pendiente | script listo, sin corrida completa guardada |
| D | pendiente | depende de comparar B vs C con cuota disponible |

## Tabla de resultados

| Condicion | Chunking | retrieval_k | think | average reward | pass^5 | Archivo |
|---|---|---:|---|---:|---:|---|
| A | sin RAG | n/a | no | 0.2000 | baseline heredado de E3 | `sim_e4_A_baseline.json` |
| B | headers | 3 | no | parcial | no comparable aun | `sim_e4_B_headers_k3.json` |
| C | fixed_200 | 3 | no | pendiente | pendiente | `sim_e4_C_fixed_k3.json` |
| D | mejor entre B/C | 3 | si | pendiente | pendiente | `sim_e4_D_best_think.json` |

## Bloqueos operativos identificados

Los bloqueos principales de E4 ya no son de implementacion del dominio, sino operativos:

- Windows venia leyendo/escribiendo en `cp1252`, lo que obligo a fijar `utf-8` en lectura y a correr `py -X utf8`
- PowerShell rompia los JSON inline de `--agent-llm-args`; por eso los scripts ahora serializan con `ConvertTo-Json` y usan `Start-Process`
- Gemini puede devolver `RESOURCE_EXHAUSTED` o agotar la cuota diaria antes de completar las `50` simulaciones de una condicion
- cuando una corrida queda totalmente `skipped`, `tau2` puede fallar despues al calcular metricas sobre un DataFrame vacio; ese bug es del framework, no del dominio

## Siguiente paso practico

Con la implementacion ya estabilizada, el siguiente cierre real para E4 es:

1. rerun completo de B con cuota disponible
2. corrida completa de C
3. comparar B vs C
4. correr D con la ganadora
5. reemplazar en esta tabla los estados `parcial` / `pendiente` por metricas reales
