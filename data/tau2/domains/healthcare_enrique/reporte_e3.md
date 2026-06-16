# Eje 2 - Experimentos

## Experimento 1: Reglas explícitas de validación de identidad

### Hipótesis

Los fallos de la Task 26 ocurren porque la política no prohíbe explícitamente realizar operaciones administrativas antes de completar la validación SMS.

### Cambio realizado

Se agregó una sección de validación de identidad y operaciones sensibles en `policy.md`.

### Resultados

| Task | Baseline | Exp. 1 |
|--------|--------:|--------:|
| 26 | 3/5 | 5/5 |
| 27 | 0/5 | 0/5 |

### Conclusión

La hipótesis fue confirmada. La Task 26 mejoró de 3/5 a 5/5

## Experimento 2: Rechazo explícito tras validación SMS fallida

### Hipótesis

La Task 27 falla porque la política no especifica qué hacer cuando el código SMS es incorrecto, provocando ciclos infinitos.

### Cambio realizado

Se agregó una regla explícita:

- Rechazar la validación cuando `verificar_codigo_sms` devuelve False.
- No reenviar automáticamente un nuevo código.
- No reiniciar indefinidamente el proceso.
- Escalar a atención humana cuando corresponda.

### Resultados

| Task | Exp. 1 | Exp. 2 |
|--------|--------:|--------:|
| 27 | 0/5 | 5/5 |

### Conclusión

La hipótesis fue confirmada. La Task 27 pasó de 0/5 a 5/5

## Resumen de mejoras

| Task | Baseline | Final |
|--------|--------:|--------:|
| 26 | 3/5 | 5/5 |
| 27 | 0/5 | 5/5 |

### Resultado agregado

| Métrica | Baseline | Final |
|----------|----------:|----------:|
| Éxitos | 3/10 | 10/10 |
| Reward Promedio | 0.30 | 1.00 |
| Pass@5 | 0.30 | 1.00 |