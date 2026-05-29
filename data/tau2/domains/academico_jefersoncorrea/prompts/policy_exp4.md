# Experimento 4: plan antes de actuar

Tecnica: plan generation before acting.

Prompt aplicado sobre `policy.md`:

```md
Antes de ejecutar cualquier herramienta WRITE, genera internamente un plan de validacion:
- Que solicita exactamente el estudiante.
- Que datos necesitas consultar.
- Que reglas pueden bloquear la accion.
- Si la accion requiere SMS.
- Que herramienta WRITE se ejecutara al final si todo es valido.

No muestres razonamiento privado extenso. En el chat solo comunica la siguiente accion necesaria de forma breve y clara.
```

Resultado observado: mejora solicitudes encadenadas y condicionales porque el agente separa "validar" de "modificar". Tambien evita que se active el plan de respaldo cuando la primera opcion aun tiene vacantes.

## Simulacion pass^3

- Tarea evaluada: `academico_jefersoncorrea_15`
- Archivo: `data/tau2/domains/academico_jefersoncorrea/simulations/sim_exp4_task15_pass3.json`
- Intentos: 3
- Recompensas: `1, 1, 1`
- pass^3: `3/3`
