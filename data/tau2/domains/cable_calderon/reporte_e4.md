# Entrega 4 – Análisis de RAG en el dominio Cable Calderón

## Objetivo

El objetivo de esta entrega fue evaluar si la incorporación de RAG mejoraba el desempeño del agente para el dominio cable_calderon. Para ello se comparó el baseline con distintas configuraciones de recuperación de información, analizando su impacto sobre las tareas diseñadas para el dominio.

## Configuraciones evaluadas

Se evaluaron las siguientes configuraciones:

| Configuración | Descripción |
|--------------|-------------|
| A | Baseline (sin RAG) |
| B | RAG utilizando chunking por **headers** con `retrieval_k = 3` |
| C | RAG utilizando chunking **fixed_400** |
| D | RAG utilizando **headers** con `think()` habilitado |

Cada configuración fue ejecutada sobre el mismo conjunto de tareas (las más difíciles) para poder comparar los resultados de forma consistente.

## Resultados

| Configuración | Average Reward | Observaciones |
|--------------|---------------:|--------------|
| A | **0.260** | Fue el Baseline |
| B | **0.320** | El mejor resultado obtenido |
| C | **0.000** | La ejecución presentó errores durante la recuperación de información y no pudo completarse correctamente. |
| D | **0.129** | La ejecución fue parcial debido al límite diario de solicitudes de la API. |

La mejor configuración fue **B**, donde el reward promedio aumentó de **0.260** a **0.320**, lo que representa aproximadamente una mejora del **23 %** respecto al baseline.

## Análisis

En la configuración baseline el agente dependía únicamente de la política incluida dentro del prompt. Aunque lograba resolver correctamente algunos casos, en varias tareas no seguía completamente el procedimiento esperado o no recuperaba toda la información necesaria antes de ejecutar una acción.

La configuración **B** obtuvo el mejor rendimiento. Considero que esto se debe a que la estrategia de dividir la política por encabezados permitió recuperar secciones completas relacionadas con la consulta del usuario. De esta forma el agente recibía información más organizada y específica para cada situación, evitando revisar toda la política en cada conversación. Esto hizo que las respuestas fueran más consistentes y que el agente siguiera mejor las reglas establecidas para cambios de plan, reclamos y validaciones.

En la configuración **C** se utilizó una división fija del documento. Sin embargo, durante la ejecución aparecieron errores relacionados con `retrieve_policy`, lo que provocó que una gran parte de las simulaciones fuera omitida. Debido a ello, los resultados obtenidos no pueden compararse directamente con las demás configuraciones. En este caso considero que el problema estuvo asociado a la forma en que se recuperaban los fragmentos de la política y no al funcionamiento general del dominio.

Por otro lado, la configuración **D** incorporó el uso de `think()` para que el agente razonara antes de tomar decisiones. Aunque inicialmente esperaba una mejora, los resultados fueron inferiores al baseline. Cabe mencionar que durante la ejecución también se alcanzó el límite diario de solicitudes de Google AI Studio, por lo que varias simulaciones fueron omitidas. En consecuencia, los resultados de esta configuración deben interpretarse con cautela, ya que no fue posible completar todas las conversaciones previstas y probablemente por eso sus resultados fueron menores.

Durante el desarrollo también se presentaron limitaciones relacionadas con la cuota gratuita de Google AI Studio, tanto para la generación de respuestas como para los embeddings utilizados por RAG. Esto obligó a repetir algunas ejecuciones y afectó principalmente las configuraciones C y D.

## Conclusiones

La estrategia que obtuvo el mejor desempeño fue **RAG con chunking por encabezados**, ya que permitió recuperar información más relevante de la política y mejoró el comportamiento del agente respecto al baseline.

La estrategia basada en fragmentos de tamaño fijo no produjo los resultados esperados debido a problemas durante la recuperación de información, por lo que no fue posible completar correctamente las simulaciones correspondientes.

Finalmente, el uso de `think()` no mostró una mejora en este experimento. Sin embargo, considero que este resultado estuvo influenciado por las limitaciones de la API y por las simulaciones omitidas, por lo que sería recomendable repetir esta evaluación en un entorno con una mayor disponibilidad de solicitudes para obtener una comparación más representativa.

En general, la incorporación de RAG demostró ser una mejora para el dominio cuando la política fue organizada mediante encabezados, ya que permitió al agente acceder a información más relevante en el momento adecuado y ofrecer respuestas más consistentes durante la atención de los usuarios.