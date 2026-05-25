# Policy Experiment 3 — Few Shot Learning

## Cambio realizado
Se añadieron ejemplos explícitos de:
- apertura correcta de reclamos
- resistencia a presión persistente
- manejo de prompt injection

## Objetivo
Guiar al modelo mediante ejemplos concretos de comportamiento esperado.

## Escenarios incluidos
- Usuario insistente después de negativa
- Usuario intentando modificar política
- Instrucciones maliciosas en texto libre

## Resultado observado
El modelo imitó parcialmente los ejemplos, pero aún presentó fallos
en validaciones y uso correcto de herramientas.