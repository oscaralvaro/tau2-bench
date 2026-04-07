1. Descripción del Dominio 
Healthcare_Enrique es un agente de IA diseñado para optimizar la gestión clínica en el Sistema de Atención Primaria de Salud (SPS) de Chile, bajo el modelo de Estrategia de Cuidado Integral Centrado en las Personas (ECICEP).
El agente actúa como un puente inteligente entre la ficha clínica del paciente y las decisiones administrativas, asegurando que los pacientes crónicos con Diabetes Mellitus Tipo 2 (DM2), Hipertensión Arterial (HTA) y Vicios de Refracción reciban una atención oportuna, integrada y técnicamente válida según las Guías de Práctica Clínica del Ministerio de Salud.
2. Entidades 
Paciente (Ficha Maestro)
1.	RUT: Identificador único (con dígito verificador).
2.	Edad y Sexo: Crítico para metas de $HbA1c$ y garantías GES (Oftalmología > 65 años).
3.	Clasificación de Riesgo (G-ECICEP): G1 (Bajo), G2 (Moderado), G3 (Alto).
4.	Riesgo Cardiovascular (RCV): Bajo, Moderado, Alto, Muy Alto (basado en tablas Framingham/MINSAL).
5.	Estado PSCV: Activo/Inactivo en el Programa de Salud Cardiovascular.
Profesional de Salud
•	ID SIS: Registro en la Superintendencia de Salud.
•	Rol: (Médico, Enfermero/a, Nutricionista, TENS, Tecnólogo Médico Oftalmología).
•	Certificación PA: Booleano que indica si el profesional está certificado en la técnica de toma de Presión Arterial (requerido por guía HTA).
•	Sector: (Ej: Sector Azul, Sector Rojo) para la asignación territorial en el CESFAM.
Registro Clínico de Parámetros (Exámenes y Biometría)
La fuente de verdad para el RAG. Cada registro debe tener una estampa de tiempo.
•	Tipo de Parámetro:
o	Laboratorio: $HbA1c$, Creatinina, RAC, Perfil Lipídico.
o	Biometría: PA Sistólica, PA Diastólica, Peso, Talla, IMC.
o	Oftalmológico: Agudeza Visual (Ojo Izquierdo/Derecho), Presión Intraocular.
•	Fecha de Toma: Crucial para calcular la Vigencia (ej. < 6 meses para DM2).
•	Valor y Unidad: (Ej: 7.5%, 140/90 mmHg, 0.3 Snellen).
Interconsulta (SIC - Solicitud de Interconsulta)
•	ID Solicitud: Correlativo único.
•	Especialidad Destino: (Nefrología, Oftalmología/UAPO, Cardiología).
•	Criterio de Derivación: El "por qué" clínico (ej: Falla terapéutica, Sospecha de catarata).
•	Estado: (Borrador, Validada por IA, Pendiente de Exámenes, Enviada).
Bloque de Agenda Multiprofesional
•	ID Bloque: Identificador de la cita grupal.
•	Tipo de Prestación: (Control Integral, Ingreso, Rescate).
•	Lista de Participantes: Mínimo 2 profesionales de roles distintos.
•	Duración: Tiempo total (Sugerido: 45-60 min para ECICEP G3).
•	Estado de Cupo: (Disponible, Reservado, Confirmado, Inasistencia).
3. Tools
A. Módulo de Consulta y Vigilancia
1.	get_patient_summary(rut):
o	Función: Extrae la ficha maestra del paciente, su riesgo cardiovascular (RCV) y su clasificación ECICEP (G1-G3).
2.	get_clinical_records(rut, parameter_type, months_back):
o	Función: Busca registros específicos (ej. $HbA1c$, Presión Arterial) en un rango de tiempo.
B. Módulo de Validación de Derivaciones (RAG Logic)
3.	validate_referral_criteria(rut, target_specialty):
o	Función: Cruza los datos del paciente contra la "Matriz de Guías Clínicas" (RAG).
o	Lógica Interna:
	Si es Nefrología: Revisa 2 $HbA1c$ < 6 meses + Creatinina.
	Si es Oftalmología: Revisa $AV \leq 0.3$ y edad $> 65$.
o	Retorno: Un objeto con status: [VALID/INVALID] y una lista de missing_requirements si corresponde.
4.	update_sic_status(sic_id, new_status):
o	Función: Cambia el estado de una interconsulta (de "Borrador" a "Validada por IA" o "Pendiente de Exámenes").
C. Módulo de Orquestación de Agenda
5.	find_multiprofessional_availability(sector, required_roles, date_range):
o	Función: Busca en la entidad Bloque de Agenda espacios donde coincidan los roles solicitados (ej: Médico + Enfermero) dentro del mismo sector del paciente.
o	Restricción: Solo considera profesionales con Certificación PA: True si la cita incluye control de hipertensión.
6.	book_integral_control(rut, block_id):
o	Función: Reserva el bloque para el paciente y actualiza el Estado de Cupo a "Reservado".
o	Uso: Se ejecuta una vez que el administrativo o el paciente confirman la propuesta de Enrique.
D. Módulo de Alertas
7.	trigger_clinical_alert(rut, alert_type, value):
o	Función: Notifica al equipo de cabecera si el agente detecta valores críticos (ej: Glicemia $> 300$ mg/dL) durante la revisión de registros.

5.	Policy Summary:
1. Reglas de Validación de Interconsultas (RAG Logic)
El agente solo marcará una interconsulta como Validada por IA si se cumplen los siguientes requisitos sin excepción:
A. Para Diabetes Mellitus Tipo 2 (DM2) -> Nefrología/Diabetología
•	Regla de Evidencia: Debe existir registro de al menos dos (2) exámenes de $HbA1c$ en los últimos 6 meses.
•	Regla de Fracaso Terapéutico: El paciente debe tener registrado el uso de Metformina + un segundo agente + Insulina NPH en dosis máximas sin alcanzar la meta.
•	Filtro de Inestabilidad: Si el registro de Glicemia es $> 300$ mg/dL o $HbA1c > 9\%$, el agente debe detener la validación estándar y sugerir "Evaluación por Urgencia/Manejo Avanzado" en lugar de derivación electiva.
B. Para Hipertensión Arterial (HTA) -> Cardiología
•	Regla de Riesgo: Solo se validan derivaciones para pacientes clasificados con RCV Alto o Muy Alto.
•	Regla de Diagnóstico: Para derivación inicial, el paciente debe tener un perfil de presión (3 mediciones en 3 días) o un MAPA de 24 horas registrado en los últimos 3 meses.
C. Para Vicios de Refracción -> UAPO/Oftalmología
•	Regla de Edad (GES): El paciente debe tener 65 años o más.
•	Regla de Agudeza Visual: El valor registrado debe ser $\leq 0.3$ (20/60) en el mejor ojo y debe estar documentado que no mejora con sus lentes actuales.
•	Regla de Exclusión: Queda prohibido validar interconsultas si el motivo es "Ojo Rojo Doloroso" o "Pérdida súbita de visión"; estas deben ser derivadas a la red de urgencia inmediatamente.
________________________________________
2. Reglas de Orquestación de Agenda (Model ECICEP)
A. Composición del Bloque Multiprofesional
•	Triada Obligatoria: Para pacientes G3 (Riesgo Alto), el bloque debe incluir obligatoriamente a un Médico y un Enfermero/a. La presencia del Nutricionista es prioritaria pero opcional según disponibilidad.
•	Certificación Técnica: No se puede asignar a un profesional a un bloque de control HTA si su atributo Certificación PA es False.
B. Tiempos y Frecuencia
•	Duración Mínima: Los controles integrales para pacientes G2 y G3 no pueden durar menos de 45 minutos de tiempo compartido.
•	Periodicidad Estricta:
o	G3: Agendar cada 3 meses.
o	G2: Agendar cada 6 meses.
o	G1: Agendar anualmente.
C. Territorialidad (Sectorización)
•	Regla de Sector: Enrique no puede agendar a un paciente en un bloque con profesionales que no pertenezcan a su mismo Sector (Ej: Paciente Sector Azul solo con Equipo Sector Azul).
________________________________________
3. Reglas de Integridad de Datos y Privacidad
•	Vigencia de Exámenes: Todo examen de laboratorio ($HbA1c$, Creatinina, Perfil Lipídico) tiene una validez máxima de 6 meses para efectos de toma de decisiones. Pasado ese tiempo, el dato se considera "Vencido" y el agente debe solicitar uno nuevo.
•	Identificación: El agente debe validar el RUT mediante el algoritmo de dígito verificador antes de mostrar cualquier resumen clínico.
•	Neutralidad: Enrique no puede modificar dosis de medicamentos; solo puede reportar si la dosis actual está bajo la meta terapéutica definida en la tabla de metas (HbA1c $< 7\%$ o $< 8\%$ según fragilidad).
6.	Tasks
task_0 - El usuario intenta derivar a un paciente de 67 años a Oftalmología con Agudeza Visual (AV) de 0.6 y sin registro de presión intraocular. | Tests: El agente rechaza la validación por no cumplir el criterio GES ($AV \leq 0.3$) y faltar datos críticos.
task_1 - El médico solicita derivar a un paciente DM2 a Nefrología tras falla con 3 fármacos (incluida Insulina) y 2 HbA1c vigentes fuera de meta. | Tests: El agente valida correctamente la interconsulta al verificar el cumplimiento del protocolo de falla terapéutica.
task_2 - Un administrativo solicita agendar un control integral para un paciente G3 (Riesgo Alto) pero solo hay disponibilidad de Médico (sin Enfermero). | Tests: El agente se niega a agendar el bloque, citando la política ECICEP que exige la tríada/dupla obligatoria para G3.
task_3 - El usuario intenta agendar una cita de rutina para un paciente cuyo último registro de glicemia es de 350 mg/dL. | Tests: El agente interrumpe el flujo, bloquea el agendamiento y dispara una alerta clínica por inestabilidad.
task_4 - El usuario solicita una interconsulta a Oftalmología para un paciente de 45 años por vicio de refracción. | Tests: El agente rechaza la solicitud basándose en la política de edad (Garantía GES solo para $> 65$ años).
