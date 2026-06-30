# Policy Experiment 2 — Chain of Thought

## Cambio realizado
Se agregó razonamiento paso a paso antes de ejecutar cualquier acción.

## Objetivo
Reducir errores de lógica y mejorar validaciones antes de actuar.

## Nueva instrucción agregada

1. Identificar la solicitud del usuario
2. Verificar identidad
3. Consultar herramientas
4. Evaluar políticas
5. Ejecutar acción solo si es válida
6. Confirmar resultado

## Resultado observado
El agente mostró respuestas más estructuradas, pero no logró mejorar
las tareas con reward 0 de forma consistente.