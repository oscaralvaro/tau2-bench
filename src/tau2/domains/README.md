# Tau2 Domains

Este directorio contiene los dominios del proyecto Tau2, incluyendo los dominios
desarrollados para APS - RAG Clinico por **Juana Cristina Mendoza Pacheco**.

## Estructura general de un dominio

Cada dominio vive en su propia carpeta y normalmente incluye:

- `data_model.py`: modelos Pydantic de las entidades y de la base de datos.
- `tools.py`: herramientas que el agente puede invocar.
- `environment.py`: carga politica, herramientas, base de datos y tareas.
- `utils.py`: rutas y utilidades del dominio.
- `README.md`: resumen funcional del dominio.

Los datos asociados viven en `data/tau2/domains/<domain_name>/` y suelen incluir:

- `db.json`: base de datos simulada del dominio.
- `tasks.json`: tareas del benchmark.
- `split_tasks.json` o `split_task.json`: particiones de tareas.
- `policy.md`: politica o lineamientos que debe seguir el agente.

## Dominios de Salud Mendoza

### `salud_mendoza_lista`

Dominio orientado a la **gestion de lista de espera** y limpieza administrativa de
interconsultas quirurgicas o de especialidad.

Objetivos principales:

- consultar datos del paciente por RUT
- revisar el estado de una interconsulta
- buscar cupos hospitalarios disponibles
- agendar reservas
- cerrar casos resueltos externamente
- marcar casos como inubicables
- escalar reclamos a un humano

Entidades principales:

- `Paciente`
- `Interconsulta`
- `CupoAgenda`

Resumen de policy:

- validar identidad del paciente
- obtener confirmacion explicita antes de agendar
- priorizar pacientes GES y antiguedad
- escalar reclamos agresivos o emergencias

### `salud_mendoza_rag`

Dominio orientado a un **asistente de interconsulta clinica** para APS, con foco en
validacion de pertinencia y completitud de derivaciones antes de enviarlas al nivel
hospitalario.

Objetivos principales:

- consultar requisitos de derivacion por diagnostico
- validar solicitudes de interconsulta
- adjuntar examenes faltantes
- orientar pertinencia APS/UAPO/hospital
- reconocer urgencias oftalmologicas

Entidades principales:

- `ProtocoloRAG`
- `Examen`
- `SolicitudInterconsulta`

Resumen de policy:

- no validar solicitudes incompletas
- aplicar protocolos por diagnostico sospechado
- informar plazos GES cuando corresponde
- diferenciar urgencia de tramite electivo
- escalar cuando la solicitud es insegura o fuera de protocolo

## Tareas

Ambos dominios incluyen tareas benchmark en `tasks.json`.

- `salud_mendoza_lista` contiene escenarios de agenda, lista de espera, resolucion
  externa, inubicabilidad y escalamiento.
- `salud_mendoza_rag` contiene escenarios de validacion de protocolos, glaucoma,
  cataratas, urgencia oftalmologica, retinopatia diabetica, UAPO, trauma ocular y
  tumor ocular.

## Ejecucion rapida

En PowerShell, desde la raiz del repo:

```powershell
$env:PYTHONPATH="src"
pytest tests/test_domains/salud_mendoza_lista/test_tools_salud_mendoza_lista.py -q
pytest tests/test_domains/salud_mendoza_rag/test_tools_salud_mendoza_rag.py -q
python -m tau2.cli play
```

Para correr un benchmark automatico:

```powershell
$env:PYTHONPATH="src"
python -m tau2.cli run --domain salud_mendoza_rag
```
