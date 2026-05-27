# salud_mendoza

Autora: **Juana Cristina Mendoza Pacheco**

## Descripcion del dominio

Dominio unificado de Tau2 para salud publica que combina:

- gestion administrativa de lista de espera
- revision RAG de interconsultas oftalmologicas antes de derivar

El agente puede limpiar lista, agendar cupos, revisar completitud de examenes,
identificar signos de alarma y orientar la ruta asistencial.

## Tareas

El dominio incluye tareas como:

- consulta de estado de interconsulta
- agendamiento de cupos
- resolucion externa
- paciente inubicable
- validacion de identidad
- reclamo con transferencia a humano
- consulta de requisitos de derivacion
- deteccion de examenes faltantes
- validacion de solicitudes
- diferenciacion entre electivo y urgencia

## Entidades principales

- `Paciente`
- `Interconsulta`
- `CupoAgenda`
- `ProtocoloRAG`
- `SolicitudInterconsulta`

## Resumen del policy

- solicitar RUT antes de operar sobre lista de espera
- confirmar explicitamente antes de agendar o cerrar
- validar examenes obligatorios antes de aprobar una solicitud
- derivar a urgencias si el cuadro sugiere riesgo visual agudo
- escalar a humano ante reclamos agresivos o conducta insegura
