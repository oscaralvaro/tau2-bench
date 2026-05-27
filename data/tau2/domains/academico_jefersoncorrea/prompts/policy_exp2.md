# Experimento 2: claridad y especificidad para task 4

Tecnica: revision de claridad y especificidad.

Prompt aplicado sobre `policy.md`:

```md
### Regla reforzada para solicitudes con restricciones implicitas
Cuando el estudiante pida "cualquier curso" o una "mejor opcion", no ejecutes matriculas hasta descubrir y validar todas las restricciones relevantes.

Para cada curso candidato debes revisar:
1. Area solicitada por el estudiante.
2. Vacantes.
3. Prerrequisitos.
4. Horario.
5. Fecha de finalizacion (`end_date`) si el usuario menciona becas, cierre de ciclo o fechas limite.

Si no existe un curso que cumpla todas las restricciones, informa que no hay opcion academica valida y escala a un Asesor Academico Humano. No uses cursos de otra area para "resolver" la urgencia.
```

Resultado observado: mejora la comunicacion, pero si el modelo no ve `end_date` en el esquema del curso, tiende a escalar por falta de datos o matricular una opcion parcial.

## Simulacion pass^3

- Tarea evaluada: `task_4_restricciones_implicitas_y_busqueda_mejor_opcion`
- Archivo: `data/tau2/domains/academico_jefersoncorrea/simulations/sim_exp2_task4_pass3.json`
- Intentos: 3
- Recompensas: `1, 1, 1`
- pass^3: `3/3`
