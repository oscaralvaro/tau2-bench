# Experimento 3: estructura XML para operaciones sensibles

Tecnica: estructura del prompt con etiquetas XML.

Prompt aplicado sobre `policy.md`:

```md
<operacion_sensible>
  <precondiciones>
    <paso>Validar identidad con get_student_details.</paso>
    <paso>Validar curso con search_courses.</paso>
    <paso>Rechazar si faltan prerrequisitos, no hay vacantes, ya aprobo el curso o existe cruce horario.</paso>
  </precondiciones>
  <seguridad>
    <paso>Solo si la operacion es valida, llamar send_verification_sms.</paso>
    <paso>Solicitar la clave dinamica de 6 cifras.</paso>
    <paso>Llamar verify_sms_code con required_role="student".</paso>
    <paso>Modificar la base de datos solo si la verificacion fue exitosa.</paso>
  </seguridad>
</operacion_sensible>
```

Resultado observado: reduce saltos de SMS y mejora task 11/task 20, pero no corrige por si solo errores de datos cuando las matriculas estan compactadas en un solo `course_id`.

## Simulacion pass^3

- Tarea evaluada: `academico_jefersoncorrea_11`
- Archivo: `data/tau2/domains/academico_jefersoncorrea/simulations/sim_exp3_task11_pass3.json`
- Intentos: 3
- Recompensas: `1, 1, 1`
- pass^3: `3/3`
