# Policy E3 experimento 1: baseline top 10 dificil

Simulacion asociada:

- `data/simulations/sim_e3_baseline.json`
- Copia cruda original: `data/simulations/rivera_top10_dificiles_pass5_v2.json`

Objetivo:

Medir el comportamiento del agente de Entrega 2 sobre las 10 tareas mas dificiles antes de aplicar mejoras E3.

Tecnicas observadas:

- Baseline sin nuevos ajustes de prompt E3.
- Diagnostico por `pass^5`.
- Identificacion de fallas por task, tool y argumento.

Resultado:

- 40/50 simulaciones con reward completo.
- Fallaron las tareas 4 y 13.
- La tarea 4 fallo por seleccion de producto/cantidad de lubricante.
- La tarea 13 fallo por campos incompletos de `register_order`.
