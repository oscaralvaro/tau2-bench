# Entregable 2 - Dominio `lopez`

## Estado final

El Entregable 2 queda completo para el dominio `lopez`.

Se implemento y valido:

- ampliacion de 10 a 15 tareas
- 5 tareas nuevas orientadas a SMS, verificacion de identidad y adversarialidad
- herramientas de usuario para lectura de SMS
- flujo de sincronizacion entre herramientas del agente y herramientas del usuario
- politica reforzada para prompt injection, autoridad falsa, instrucciones prohibidas y frases esperadas por evaluacion
- reporte de resultados pass^5
- artefacto combinado de simulacion con las 15 tareas del split `base`
- tests unitarios del dominio actualizados

Nota de alcance: se mantiene la version ajustada de la entrega con 5 tareas nuevas y pass^5, segun la indicacion de reducir la carga de simulacion.

## Validacion local

Comandos ejecutados:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\domain_tests\lopez -q
```

Resultado:

```text
26 passed
```

Tambien se valido que el registro cargue el dominio y el task set:

```text
domain True
tasks True
base_len 15
splits {'train': 10, 'test': 5, 'base': 15}
```

La revision automatica estructural encontro el artefacto combinado de simulacion:

```text
data/simulations/lopez_e2_pass5_all_tasks_final.json
```

Resultado de esa revision:

```text
Aprobado con advertencias
35/36 verificaciones aprobadas
La simulacion incluyo las 15 tareas del split base
Cobertura completa: 15/15 tareas
Todas las tareas tienen 5 trials completados
Resumen: pass rate=53% (40/75), reward promedio=0.53
```

La advertencia restante corresponde a que el validador busca una clave generica `users` en `db.json`; el dominio usa la entidad especifica `clientes`, con 5 clientes definidos.

## Archivos principales

Codigo del dominio:

- `src/tau2/domains/lopez/data_model.py`
- `src/tau2/domains/lopez/tools.py`
- `src/tau2/domains/lopez/user_data_model.py`
- `src/tau2/domains/lopez/user_tools.py`
- `src/tau2/domains/lopez/environment.py`
- `src/tau2/domains/lopez/utils.py`

Datos del dominio:

- `data/tau2/domains/lopez/db.json`
- `data/tau2/domains/lopez/user_db.json`
- `data/tau2/domains/lopez/tasks.json`
- `data/tau2/domains/lopez/split_tasks.json`
- `data/tau2/domains/lopez/policy.md`
- `data/tau2/domains/lopez/reporte.md`

Simulaciones:

- `data/simulations/lopez_e2_pass5_all_tasks_final.json`
- `data/tau2/domains/lopez/simulations/sim_final_all.json`
- `data/tau2/domains/lopez/simulations/pass5_summary.json`

Tests:

- `tests/domain_tests/lopez/test_tools_lopez.py`
- `tests/domain_tests/lopez/test_user_tools_lopez.py`

## Tareas nuevas de Entregable 2

- `sms_cancel_pending_verified`
- `sms_order_status_wrong_code`
- `authority_claim_cancel_delivered`
- `instruction_override_cancel_delivered`
- `prompt_injection_ticket_reason`

## Resultados

El detalle de resultados pass^5, analisis de las tres tareas con peor rendimiento y experimento de prompt engineering esta documentado en:

```text
data/tau2/domains/lopez/reporte.md
```

El resumen estructurado esta en:

```text
data/tau2/domains/lopez/simulations/pass5_summary.json
```
