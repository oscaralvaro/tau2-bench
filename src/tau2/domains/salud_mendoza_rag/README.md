# salud_mendoza_rag

Autora: **Juana Cristina Mendoza Pacheco**

## Descripcion del dominio

Dominio de Tau2 para un asistente RAG clinico de APS que ayuda a revisar
interconsultas antes de derivarlas al hospital. El foco esta en pertinencia,
completitud de examenes y orientacion de ruta asistencial.

## Tareas

El dominio incluye tareas como:

- consulta de requisitos de derivacion
- deteccion de examenes faltantes
- validacion de solicitudes
- diferenciacion entre electivo y urgencia
- retinopatia diabetica
- UAPO y teleoftalmologia
- trauma ocular complejo
- sospecha de tumor ocular

## Entidades principales

- `Examen`
- `ProtocoloRAG`
- `SolicitudInterconsulta`

## Resumen del policy

- validar examenes obligatorios antes de aprobar una solicitud
- aplicar criterios por diagnostico soportado
- informar plazos GES cuando corresponda
- derivar a urgencias si el cuadro sugiere riesgo visual agudo
- escalar a humano cuando el medico insiste en una conducta insegura
