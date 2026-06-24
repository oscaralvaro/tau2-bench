# Entrega 4 ecommerce_calle

## Archivos principales

- Reporte final: `reporte_e4.md`
- Hallazgos acumulados: `hallazgos_e1_e4.md`
- Politica RAG: `policy_rag.md`
- Simulaciones finales: `simulations/`

## Simulaciones incluidas

- `sim_e4_A_baseline.json`
- `sim_e4_B_headers_k3.json`
- `sim_e4_C_fixed_k3.json`
- `sim_e4_D_best_think.json`

## Resumen ejecutivo

La mejor condicion final de E4 para `ecommerce_calle` fue C:
`fixed_200`, `retrieval_k = 3`, sin think. El resultado fue `35/50`,
empatando el baseline de E3 y superando a la condicion B con `headers`.

La condicion D si activo `think`, pero quedo afectada por errores de cuota
del free tier de Gemini y termino con `17/50`.
