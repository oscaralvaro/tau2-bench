# Dominio: cable_calderon

Alumna: Maria Jose Calderon Samaniego  
Empresa simulada: CableHogar  
Tipo de dominio: Atención al cliente — Instalación de cable e internet a domicilio

---

## Descripción del Dominio

CableHogar es una empresa que instala y da soporte a servicios de cable e internet a domicilio en la región de Piura. El agente de atención al cliente puede ayudar a los clientes con consultas sobre su cuenta, gestión de órdenes de instalación, cambios de plan y apertura de reclamos.

---

## Entidades

| Entidad | Descripción |
|---|---|
| Cliente | Titular del contrato con datos personales, estado de deuda y lista de contactos autorizados para realizar cambios |
| ContactoAutorizado | Persona autorizada por el titular para realizar cambios en la cuenta |
| Plan | Plan de servicio disponible (internet, cable o combo) con velocidad, canales y precio mensual |
| Servicio | Servicio activo de un cliente, vinculado a un plan con estado y fechas |
| OrdenInstalacion | Orden de visita técnica para instalación nueva, mantenimiento o retiro, con fecha, hora y técnico asignado |
| Reclamo | Ticket de soporte abierto por el cliente por problemas de señal, facturación, instalación u otros |

---

## Herramientas del Agente

### Consulta (sin efectos secundarios)
| Herramienta | Descripción |
|---|---|
| `get_client_details(cliente_id)` | Retorna datos del cliente, titular, deuda y contactos autorizados |
| `get_service_details(cliente_id)` | Retorna el plan activo, estado y fechas del servicio |
| `list_available_plans(tipo?)` | Lista todos los planes disponibles, filtrando opcionalmente por tipo |
| `get_order_details(orden_id)` | Retorna detalles de una orden de instalación |
| `get_complaint_status(reclamo_id)` | Retorna el estado actual de un reclamo |

### Modificación (con efectos secundarios)
| Herramienta | Descripción |
|---|---|
| `schedule_installation(cliente_id, tipo, fecha, hora)` | Agenda una nueva orden de instalación o visita técnica |
| `reschedule_installation(orden_id, nueva_fecha, nueva_hora)` | Reprograma una orden existente |
| `cancel_installation(orden_id)` | Cancela una orden de instalación |
| `upgrade_plan(cliente_id, nuevo_plan_id)` | Sube el plan del cliente a uno de mayor nivel |
| `create_complaint(cliente_id, tipo, descripcion)` | Abre un nuevo reclamo para el cliente |

---

## Resumen de la Política

- Verificación de identidad: Solo el titular o un contacto autorizado puede realizar cambios. Para consultas generales no se requiere verificación.
- Deuda pendiente: No se puede agendar ninguna instalación si el cliente tiene deuda pendiente.
- Reprogramación: Solo se permite con más de 48 horas de anticipación.
- Cancelación: No se puede cancelar si ya hay técnico asignado y faltan menos de 24 horas. Tampoco si la orden está en curso o completada.
- Cambio de plan: Solo se permite upgrade (plan de mayor nivel). El downgrade no está permitido.
- Reclamos de señal: Se atienden en un plazo de 72 horas hábiles.

---

## Tareas (15 en total)

| ID | Tipo | Descripción |
|---|---|---|
| 0 | Consulta | Cliente consulta datos de su cuenta |
| 1 | Consulta | Cliente consulta su plan activo y precio |
| 2 | Consulta | Cliente consulta planes disponibles |
| 3 | Consulta | Cliente consulta estado de su reclamo |
| 4 | Consulta | Cliente consulta detalles de su orden |
| 5 | Modificación | Titular agenda nueva instalación exitosamente |
| 6 | Modificación | Contacto autorizado reprograma una orden |
| 7 | Modificación | Titular hace upgrade de plan exitosamente |
| 8 | Modificación | Titular abre reclamo por problemas de señal |
| 9 | Modificación | Titular cancela orden sin técnico asignado |
| 10 | Rechazo | Cliente con deuda intenta agendar instalación |
| 11 | Rechazo | Intento de reprogramar con menos de 48 horas |
| 12 | Rechazo | Intento de downgrade de plan |
| 13 | Edge case | Persona no autorizada intenta cancelar orden |
| 14 | Edge case | Cancelación con técnico asignado y menos de 24h |