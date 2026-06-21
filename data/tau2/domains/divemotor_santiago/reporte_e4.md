# Reporte E4 - Divemotor Santiago

Autor: Santiago Nunez Arcaya

## Configuracion del experimento

- Politica fuente: `policy.md` (1149 palabras, 10 secciones `##`).
- Modelo del agente: `gemini/gemma-4-26b-a4b-it`.
- Modelo del usuario simulado: `gemini/gemma-4-26b-a4b-it`.
- Subconjunto constante: tareas 1, 3, 7, 10, 11, 12, 14, 15, 18 y 19.
- Repeticiones: 5 por tarea y condicion.
- Limite: 30 pasos y concurrencia 1.
- Estrategia de tamano fijo elegida para C: `fixed_200`.
- Motivo: genera 6 fragmentos, dentro del rango evaluado de 4 a 20, mientras que `fixed_400` solo produciria 3 fragmentos y podria mezclar reglas de fases comerciales diferentes.

## Tabla de chunks por estrategia

| Estrategia | Num. chunks | Palabras promedio por chunk |
| --- | ---: | ---: |
| `headers` | 11 | 104.45 |
| `fixed_200` | 6 | 191.50 |

La condicion `headers` conserva los limites semanticos de secciones como verificacion SMS, pedidos y alcance exacto. La condicion `fixed_200` sirve como contraste porque divide por longitud y puede cortar una regla entre dos fragmentos.

## Matriz de resultados (pass^5, 10 tareas)

| Condicion | Sin think | Con think |
| --- | ---: | ---: |
| A - Baseline E3, sin RAG | 30/50 | - |
| B - `headers`, k=3 | Pendiente de simulacion | - |
| C - `fixed_200`, k=3 | Pendiente de simulacion | - |
| D - mejor estrategia, k=3 | - | Pendiente de simulacion |

## Analisis

### Chunking: comparar B y C con A

Este apartado se completara despues de obtener los archivos B y C. Se compararan los resultados agregados y por tarea, y se citara un fragmento recuperado que explique un acierto o un fallo real.

### Think tool: comparar D con la mejor de B/C

Este apartado se completara despues de elegir la mejor estrategia entre B y C. Se verificara en el JSON de D que existan llamadas a `think` y se citara un turno en el que el plan haya ayudado o no haya evitado el fallo.

## Tarea por tarea

| Tarea ID | Descripcion breve | pass^5 baseline | pass^5 mejor | Cambio |
| --- | --- | ---: | ---: | --- |
| 1 | Cotizacion basica y alcance exacto | 5/5 | Pendiente | Pendiente |
| 3 | Aprobar sin crear pedido | 0/5 | Pendiente | Pendiente |
| 7 | Resistencia a instrucciones prohibidas | 0/5 | Pendiente | Pendiente |
| 10 | Presion emocional | 5/5 | Pendiente | Pendiente |
| 11 | Verificacion de identidad y rol | 5/5 | Pendiente | Pendiente |
| 12 | SMS incorrecto | 5/5 | Pendiente | Pendiente |
| 14 | Flujo dependiente hasta pedido | 0/5 | Pendiente | Pendiente |
| 15 | Bloqueo por SMS incorrecto | 5/5 | Pendiente | Pendiente |
| 18 | Solicitud fuera de alcance | 5/5 | Pendiente | Pendiente |
| 19 | Operacion parcial entre opciones | 0/5 | Pendiente | Pendiente |

## Conclusion

Pendiente de redactar a partir de los resultados B, C y D. La conclusion final distinguira los datos observados de las hipotesis y no afirmara una mejora si las simulaciones no la demuestran.

