# Hallazgos acumulados E1-E4

## E1

Se construyo el dominio `restaurante_joaquin_cachay` con:

- modelo de datos para restaurante, reservas, pedidos, pagos y SMS
- toolkit operacional del agente
- herramientas del usuario simulado
- conjunto de tareas del dominio

## E2

Avances principales:

- `22` tareas definidas en `tasks.json`
- `split_tasks.json` con `train`, `test`, `base` y luego `base_top10hard`
- politicas iteradas en `prompts/`
- verificacion por SMS implementada

Resultado mas importante:

- el dominio quedo funcional, aunque `restaurant_order_delivery_1` presento un bloqueo tecnico recurrente en algunas corridas completas

Lectura posterior mas fina:

- al inicio parte del problema venia de exponer demasiadas herramientas al usuario simulado
- mas adelante el cuello de botella dominante paso a ser externo: cuota / rate limit / timeouts del proveedor

## E3

Se trabajo sobre `base_top10hard`.

Linea base oficial:

- [sim_e3_baseline.json](C:\Users\Joaquin\tau2-bench\data\simulations\sim_e3_baseline.json)
- `average reward = 0.2000`

Mejoras locales comprobadas:

- `restaurant_large_party_pending_reservation_1`: mejora en `sim_e3_exp3_tool_misuse.json`
- `restaurant_order_cancel_1`: mejora en `sim_e3_exp5_policy_miss.json`
- `restaurant_reject_missing_delivery_info_1`: mejora en `sim_e3_exp6_final_push.json`

Conclusion de E3:

- hubo mejoras locales reales
- no aparecio una unica variante global mejor que el baseline
- por eso el archivo final de E3 se dejo alineado con baseline
- como endurecimiento tecnico posterior, el toolkit quedo con descripciones cortas y el usuario simulado limitado a SMS

## E4

Se dejo implementada la infraestructura para RAG:

- `RAGToolKit` en el dominio
- `policy_rag.md` como prompt reducido
- `ChromaPolicyIndex` configurable por `env-args`
- soporte para `use_think`
- pruebas locales pasando (`48 passed`)
- replay endurecido para que `retrieve_policy` recupere el cache correcto durante evaluacion aun cuando el framework reconstruye el entorno sin reenviar `env-args`

Archivos operativos de E4:

- [run_e4_A_baseline.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_A_baseline.ps1)
- [run_e4_B_headers_k3.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_B_headers_k3.ps1)
- [run_e4_C_fixed_k3.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_C_fixed_k3.ps1)
- [run_e4_D_best_think.ps1](C:\Users\Joaquin\tau2-bench\scripts\restaurante_joaquin_cachay\run_e4_D_best_think.ps1)

Estado practico de E4:

- A ya esta derivado desde E3
- B ya quedo completo y su resultado fue peor que el baseline (`0.0200` vs `0.2000`)
- C quedo parcial con `10/50` simulaciones guardadas y `average reward = 0.0000`
- D quedo parcial con `35/50` simulaciones guardadas y `average reward = 0.0000`
- el cierre experimental de C y D quedo bloqueado por cuota diaria / cuelgues del proveedor, no por codigo faltante del dominio

## Lectura global del proyecto

Lo mas fuerte del dominio:

- buena cobertura de flujos realistas
- herramientas y schemas bastante precisos
- tests del dominio estables
- politicas cada vez mas especificas para casos sensibles
- scripts de corrida mucho mas robustos para Windows y PowerShell

Lo mas fragil:

- algunas tareas largas con delivery pueden disparar problemas de cuota, rate limiting o contexto
- los prompts globales no siempre conservan mejoras locales
- PowerShell y Windows requieren cuidado especial con `utf-8` y JSON en linea
- cuando todas las corridas quedan `skipped`, `tau2` puede romperse al calcular metricas sobre resultados vacios

## Hallazgos operativos clave

1. `utf-8` en Windows no era opcional.
   - el sistema venia con `cp1252`
   - por eso hubo que fijar `encoding="utf-8"` en lectura del dominio y correr `py -X utf8`

2. El problema de varios scripts no era `tau2`, sino PowerShell serializando mal el JSON inline.
   - se resolvio migrando a `ConvertTo-Json -Compress` + `Start-Process`

3. No todo error de simulacion implica que el dominio este mal.
   - `reward = 0` significa que el agente no resolvio la tarea
   - `RESOURCE_EXHAUSTED`, `Timeout`, `ContextWindowExceededError` o `DataFrame.reward` apuntan a infraestructura/proveedor/framework

4. Reducir contexto tambien fue una mejora tecnica real.
   - las descripciones cortas de tools y la restriccion de user tools bajan ruido y ayudan a estabilizar corridas largas

## Estado final de cierre

Lo que si quedo cerrado:

1. la implementacion de E4
2. los tests relevantes del dominio
3. la corrida A
4. la corrida B
5. el analisis honesto A vs B

Lo que no quedo cerrado por factores externos:

1. completar `run_e4_C_fixed_k3.ps1`
2. completar `run_e4_D_best_think.ps1`
3. obtener una comparacion experimental final C vs D con cuota suficiente

Lectura final:

- el repositorio si queda listo para entrega desde el lado de implementacion y evidencia parcial
- la limitacion restante esta en la estabilidad/cuota de Gemini free tier
- por eso la conclusion correcta no es "faltaba codigo", sino "faltaba presupuesto operativo para cerrar todas las corridas"
