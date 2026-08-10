# salud_mendoza_lista

Autora: **Juana Cristina Mendoza Pacheco**

## Descripcion del dominio

Dominio de Tau2 para simular la gestion de lista de espera en salud publica.
Representa interconsultas pendientes, datos de pacientes y cupos hospitalarios
disponibles para apoyar limpieza de lista, agendamiento y cierre administrativo.

## Tareas

El dominio incluye tareas como:

- consulta de estado de interconsulta
- agendamiento de cupos
- resolucion externa
- paciente inubicable
- validacion de identidad
- reclamo con transferencia a humano

## Entidades principales

- `Paciente`: RUT, nombre, prevision, comuna, telefono
- `Interconsulta`: problema de salud, dias en espera, estado, prioridad
- `CupoAgenda`: hospital, fecha y especialidad disponible

## Resumen del policy

- solicitar RUT antes de operar
- confirmar explicitamente antes de agendar
- priorizar pacientes GES y antiguedad
- usar herramientas administrativas para actualizar estado
- transferir a humano frente a reclamos agresivos o urgencias
