# Experimento 5: duplicacion de reglas criticas

Tecnica: duplicacion del prompt.

Prompt aplicado sobre `policy.md`:

```md
REGLA CRITICA REPETIDA:
No ejecutes create_enrollment, update_enrollment_swap ni cancel_enrollment si:
- No se verifico identidad.
- La accion es academicamente invalida.
- No se completo verify_sms_code exitosamente.
- El rol devuelto por verify_sms_code no coincide con el rol requerido.

REGLA CRITICA REPETIDA:
Si una solicitud tiene cruce de horario, falta de prerrequisitos, falta de vacantes, curso ya aprobado o fecha incompatible, debes rechazarla antes de iniciar SMS.
```

Resultado observado: ayuda en tareas adversarias y de presion, pero puede volver al agente demasiado conservador en cancelaciones masivas si la DB tiene inconsistencias.

## Simulacion pass^3

- Tarea evaluada: `academico_jefersoncorrea_14`
- Archivo: `data/tau2/domains/academico_jefersoncorrea/simulations/sim_exp5_task14_pass3.json`
- Intentos: 3
- Recompensas: `1, 1, 1`
- pass^3: `3/3`
