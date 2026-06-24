# Policy Experiment 4 — Refuerzo de Uso Obligatorio de Herramientas

## Cambio realizado
Se reforzó explícitamente que toda acción debe ejecutarse mediante tools.

## Objetivo
Evitar respuestas donde el agente confirme acciones sin ejecutar herramientas.

## Reglas agregadas
- Nunca confirmar acciones sin tool call
- Ejecutar herramientas antes de responder
- Registrar todas las acciones en sistema

## Resultado observado
Hubo ligera mejora en consistencia conversacional, pero las tareas
más difíciles continuaron fallando.