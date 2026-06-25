# Hallazgos E1-E4 - Hotel Calle

## Evolucion del dominio

En la Entrega 1 el dominio era principalmente una prueba funcional de reservas de hotel. En las entregas siguientes se amplio hacia escenarios mas realistas: usuarios con informacion incompleta, afirmaciones falsas, prompt injection, cambios de opinion y verificacion de identidad por SMS.

## Lo que mejoro

- Las tareas cubren mas dimensiones de evaluacion y ya no solo casos felices.
- El agente final de E3 logro una linea base fuerte: 45/50 en pass^5.
- Se agrego evidencia numerica por simulacion y una taxonomia de fallos.
- El dominio tiene pruebas automatizadas para las herramientas principales.
- La integracion RAG permite comparar prompt completo contra recuperacion de politica.

## Lo que fue mas dificil

- Las tareas con informacion faltante requieren que el agente pregunte de forma muy exacta.
- El flujo SMS es sensible al orden: enviar codigo, recibirlo, verificarlo y recien despues actuar.
- En RAG, separar la politica en chunks hizo que el agente perdiera reglas relacionadas.
- Algunos fallos no eran errores de ejecucion, sino incapacidad del agente de cumplir la tarea bajo la metrica esperada.

## Aprendizaje principal

El mayor aprendizaje fue distinguir entre tres tipos de problema: un bug de herramienta, una instruccion incompleta en la politica y una falla real del modelo. En este dominio, el agente suele entender la solicitud, pero falla cuando debe seguir una secuencia precisa de herramientas o comunicar un dato literal esperado por la evaluacion.

## Decision final

Para entrega, se conserva la politica final de E3 como mejor agente principal. La condicion D queda documentada como la mejor variante RAG probada, pero no reemplaza a la linea base porque su rendimiento global fue menor.
