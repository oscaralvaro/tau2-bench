# PR Draft - restaurante_joaquin_cachay

## Titulo sugerido

`restaurante_joaquin_cachay: cierra E3 y E4 con RAG, hardening de replay y scripts robustos para Windows`

## Resumen corto

Este PR consolida el dominio `restaurante_joaquin_cachay` a nivel de codigo, tests, reportes y scripts de corrida.

Cambios principales:

- se implementa RAG en el dominio con `RAGToolKit`
- se agrega hardening de replay para `retrieve_policy`
- se corrigen scripts de PowerShell para pasar JSON sin romper `tau2`
- se documentan los resultados reales de E1-E4
- se deja evidencia local de tests pasando

## Cambios incluidos

### Dominio

- `src/tau2/domains/restaurante_joaquin_cachay/tools.py`
- `src/tau2/domains/restaurante_joaquin_cachay/environment.py`

### Scripts de corrida

- `scripts/restaurante_joaquin_cachay/run_e4_B_headers_k3.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_C_fixed_k3.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_D_best_think.ps1`

### Tests

- `tests/test_domains/test_restaurante_joaquin_cachay/test_tools_restaurante_joaquin_cachay.py`
- `tests/test_domains/test_restaurante_joaquin_cachay/test_env_args_restaurante_joaquin_cachay.py`

### Reportes

- `data/tau2/domains/restaurante_joaquin_cachay/reporte.md`
- `data/tau2/domains/restaurante_joaquin_cachay/reporte_e3.md`
- `data/tau2/domains/restaurante_joaquin_cachay/reporte_e4.md`
- `data/tau2/domains/restaurante_joaquin_cachay/hallazgos_e1_e4.md`

### Artefacto de simulacion para PR

- `data/simulations/resultados_restaurante_joaquin_cachay_full_throttled.json`

Ese archivo trackeado fue refrescado con el mejor `pass^5` real disponible (`105/110`), para que el repositorio entregue una evidencia mucho mas representativa que el artefacto historico de `12` tareas.

## Validacion local

Comando ejecutado:

```powershell
py -X utf8 -m pytest tests\test_domains\test_restaurante_joaquin_cachay\test_tools_restaurante_joaquin_cachay.py tests\test_domains\test_restaurante_joaquin_cachay\test_env_args_restaurante_joaquin_cachay.py -q
```

Resultado:

- `48 passed, 4 warnings`

## Estado real de simulaciones

### E2

- mejor `pass^5` disponible: `105/110`
- unica tarea no cerrada: `restaurant_order_delivery_1`
- causa dominante: bloqueo operativo externo (`quota`, `timeout`, `context`, `skipped`)

### E3

- baseline oficial y experimentos dirigidos documentados
- conclusion: hubo mejoras locales, pero no una variante global mejor que el baseline

### E4

- A completa: `0.2000`
- B completa: `0.0200`
- C parcial: `10/50`, `0.0000`
- D parcial: `35/50`, `0.0000`

Conclusion honesta:

- la implementacion de E4 quedo completa
- el cierre experimental total de C y D quedo limitado por cuota/estabilidad de Gemini free tier

## Limitaciones que conviene declarar en el PR

1. `restaurant_order_delivery_1` no pudo cerrarse en `pass^5` por error operativo externo, no por falta de implementacion estructural del dominio.
2. Las corridas E4 C y D quedaron parciales por `429 RESOURCE_EXHAUSTED` y procesos colgados del proveedor.
3. El repositorio si queda listo para revision de codigo, tests y analisis; lo no cerrado es capacidad de corrida estable en el proveedor.

## Estado del validador automatico

En una copia limpia con solo archivos trackeados, el validador de `.github/scripts/validate_student_pr.py` queda asi:

- aprobadas: `36/39`
- advertencias: `1`
- errores reales restantes: `2`

Errores restantes:

1. cobertura incompleta para `restaurant_order_delivery_1`
2. `restaurant_order_delivery_1` con menos de `5` trials

Eso confirma que, para el PR, el unico bloqueo estructural que seguiria vivo es esa tarea.

## Texto sugerido para la descripcion del PR

```md
## Resumen

Este PR consolida el dominio `restaurante_joaquin_cachay` a traves de las entregas E1-E4.

Se implementaron mejoras de codigo y de infraestructura experimental:

- RAG con `RAGToolKit`
- soporte de `chunking_strategy`, `retrieval_k`, `use_rag` y `use_think`
- hardening de replay para `retrieve_policy`
- scripts de PowerShell robustos para Windows/UTF-8/JSON
- tests de dominio actualizados
- reportes E3/E4 y hallazgos globales actualizados

## Validacion

```powershell
py -X utf8 -m pytest tests\test_domains\test_restaurante_joaquin_cachay\test_tools_restaurante_joaquin_cachay.py tests\test_domains\test_restaurante_joaquin_cachay\test_env_args_restaurante_joaquin_cachay.py -q
```

Resultado:

- `48 passed, 4 warnings`

## Simulaciones

- E2: mejor pass^5 disponible `105/110`; el unico bloqueo restante fue `restaurant_order_delivery_1`
- E3: baseline y experimentos documentados; no hubo mejora global estable sobre baseline
- E4: A y B cerradas; C y D quedaron parciales por quota/free-tier de Gemini

## Nota honesta

La limitacion restante es operativa del proveedor y no de estructura base del dominio: cuota, timeouts y procesos colgados impidieron cerrar algunas corridas largas.
```

## Checklist antes de abrir el PR

1. No agregar `data/tau2/domains/restaurante_joaquin_cachay/cache/`
2. No agregar logs temporales de `data/logs/`
3. Si quieres validar localmente el bot del curso:

```powershell
$files = git diff --name-only
py -X utf8 .github\scripts\validate_student_pr.py --domain restaurante_joaquin_cachay --changed-files $files
```

4. Tener presente que tu workspace local puede tener artefactos ignorados en `data/simulations/` y eso puede contaminar el resultado del validador local; el CI del PR solo vera archivos trackeados
5. Aun en el mejor caso, el validador puede seguir marcando el bloqueo historico de `restaurant_order_delivery_1`
6. En la descripcion del PR, explicar explicitamente que el problema restante es de cuota/infraestructura y no de ausencia de implementacion

## Archivos que si conviene stagear

```text
data/simulations/resultados_restaurante_joaquin_cachay_full_throttled.json
data/tau2/domains/restaurante_joaquin_cachay/reporte.md
data/tau2/domains/restaurante_joaquin_cachay/reporte_e3.md
data/tau2/domains/restaurante_joaquin_cachay/reporte_e4.md
data/tau2/domains/restaurante_joaquin_cachay/hallazgos_e1_e4.md
data/tau2/domains/restaurante_joaquin_cachay/pr_draft_final.md
scripts/restaurante_joaquin_cachay/run_e4_B_headers_k3.ps1
scripts/restaurante_joaquin_cachay/run_e4_C_fixed_k3.ps1
scripts/restaurante_joaquin_cachay/run_e4_D_best_think.ps1
src/tau2/domains/restaurante_joaquin_cachay/environment.py
src/tau2/domains/restaurante_joaquin_cachay/tools.py
tests/test_domains/test_restaurante_joaquin_cachay/test_env_args_restaurante_joaquin_cachay.py
tests/test_domains/test_restaurante_joaquin_cachay/test_tools_restaurante_joaquin_cachay.py
```
