# Simulations

Artefactos de simulacion del dominio `restaurante_joaquin_cachay`.

## Historicos

- `sim_pass1_full_preexp.json`
- `sim_final_all_pass1_gemma4_2026-05-24.json`

## Entrega 2

- `sim_pass1_partial_gemma4_26b_2026-06-26.json`
- `sim_pass5_partial_gemma4_26b_2026-06-27.json`
- `sim_debug_order_delivery_pass1_retry5_2026-06-27.json`

Notas:

- `pass1` y `pass5` siguen parciales porque solo falta `restaurant_order_delivery_1`.
- `sim_debug_order_delivery_pass1_retry5_2026-06-27.json` es evidencia del bloqueo tecnico aislado de esa tarea.
- los logs utiles de depuracion viven en `data/logs/restaurante_joaquin_cachay/`

## Entrega 3

Archivos de simulacion relevantes en `data/simulations`:

- `sim_e3_baseline.json`
- `sim_e3_final.json`
- `sim_e3_exp1_sms_identity.json`
- `sim_e3_exp2_sms_payload.json`
- `sim_e3_exp3_tool_misuse.json`
- `sim_e3_exp5_policy_miss.json`
- `sim_e3_exp6_final_push.json`
- `sim_e3_final_top10hard.json`

Lectura recomendada:

- `sim_e3_baseline.json`: baseline oficial sobre `base_top10hard`
- `sim_e3_final.json`: archivo final a citar en la entrega; coincide con baseline porque ninguna variante global supero ese resultado
- `sim_e3_exp3_tool_misuse.json`: mejor evidencia de mejora local en `restaurant_large_party_pending_reservation_1`
- `sim_e3_exp5_policy_miss.json`: mejor evidencia de mejora local en `restaurant_order_cancel_1`
- `sim_e3_exp6_final_push.json`: mejor evidencia de mejora local en `restaurant_reject_missing_delivery_info_1`
- `sim_e3_final_top10hard.json`: corrida final completa sobre las 10 tareas dificiles

Archivos auxiliares:

- `sim_e3_baseline_derived.json`: baseline intermedio historico
- `sim_e3_baseline_test.json`: prueba corta de invocacion
- `sim_e3_smoke.json`: smoke test de infraestructura

## Entrega 4

Archivos esperados:

- `sim_e4_A_baseline.json`
- `sim_e4_B_headers_k3.json`
- `sim_e4_C_fixed_k3.json`
- `sim_e4_D_best_think.json`

Estado actual:

- `sim_e4_A_baseline.json`: ya derivado desde `sim_e3_baseline.json`
- `sim_e4_B_headers_k3.json`: existe, pero quedo parcial por agotamiento de cuota
- `sim_e4_C_fixed_k3.json`: pendiente de corrida
- `sim_e4_D_best_think.json`: pendiente de corrida

Scripts asociados:

- `scripts/restaurante_joaquin_cachay/run_e4_A_baseline.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_B_headers_k3.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_C_fixed_k3.ps1`
- `scripts/restaurante_joaquin_cachay/run_e4_D_best_think.ps1`

Notas operativas:

- los scripts de E3/E4 ya generan logs separados de `stdout` y `stderr`
- si una corrida falla por cuota, revisar primero `data/logs/restaurante_joaquin_cachay/` antes de asumir que el dominio esta mal
