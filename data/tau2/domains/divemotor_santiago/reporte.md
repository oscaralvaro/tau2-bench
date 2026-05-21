# Reporte Entrega 2 - Divemotor Santiago

## Configuracion

- Dominio: `divemotor_santiago`
- Modelo agente: `gemini/gemma-4-31b-it`
- Modelo usuario: `gemini/gemma-4-26b-a4b-it`
- Idioma: espanol
- Split final: `base`
- Metrica principal: `pass^10`

## Cobertura de tareas

El conjunto final contiene 20 tareas: 10 tareas originales revisadas y 10 tareas nuevas. Las tareas cubren al menos estas dimensiones de evaluacion:

- 1. Afirmaciones falsas de autoridad
- 2. Estado propio reportado incorrectamente
- 4. Prueba de limites de politica
- 5. Presion emocional
- 6. Presion persistente despues de negativa
- 8. Solicitudes condicionales de multiples pasos
- 9. Restricciones simultaneas en conflicto
- 10. Elegibilidad de acciones segun estado
- 12. Operaciones parciales sobre colecciones
- 14. Coordinacion entre multiples entidades
- 16. Fundamentacion en resultados de herramientas
- 18. Descubrimiento de restricciones implicitas
- 20. Solicitudes fuera del alcance
- 21. Verificacion de identidad y fallos de busqueda
- 22. Acciones secundarias en cascada o dependientes
- Prompt injection e instrucciones prohibidas

## Comando de simulacion final

```powershell
$agentArgs = @{
  temperature = 0.0
  rate_limit_requests_per_minute = 14
  rate_limit_requests_per_day = 14000
  rate_limit_tokens_per_minute = 150000
  rate_limit_bucket = "google-free-tier-31b"
  rate_limit_token_reserve = 750
} | ConvertTo-Json -Compress

$userArgs = @{
  temperature = 0.0
  rate_limit_requests_per_minute = 14
  rate_limit_requests_per_day = 14000
  rate_limit_tokens_per_minute = 150000
  rate_limit_bucket = "google-free-tier-26b"
  rate_limit_token_reserve = 750
} | ConvertTo-Json -Compress

$agentArgsEscaped = $agentArgs.Replace('"', '\"')
$userArgsEscaped = $userArgs.Replace('"', '\"')

python -m tau2.cli run `
  --domain divemotor_santiago `
  --agent-llm gemini/gemma-4-31b-it `
  --user-llm gemini/gemma-4-26b-a4b-it `
  --num-trials 10 `
  --task-split-name base `
  --max-concurrency 1 `
  --save-to divemotor_santiago_final_pass10 `
  --agent-llm-args $agentArgsEscaped `
  --user-llm-args $userArgsEscaped
```

Despues de ejecutar, copiar el resultado a:

```text
data/tau2/domains/divemotor_santiago/simulations/sim_final_all.json
```

## Resultados pass^10 por tarea

Completar despues de ejecutar `pass^10`.

| Tarea | Descripcion breve | pass^10 | % de falla |
|---|---|---:|---:|
| Pendiente | Pendiente de simulacion final | - | - |

## Tres peores tareas

Completar despues de la corrida final. Para cada tarea:

- Falla tipica observada:
- Tecnicas intentadas:
- Metrica antes:
- Metrica despues:
- Evidencia en archivo de simulacion:

## Experimentos de prompt engineering

Prompts disponibles:

- `prompts/policy_exp1.md`: estructura y claridad
- `prompts/policy_exp2.md`: few-shot SMS
- `prompts/policy_exp3.md`: defensa contra prompt injection y duplicacion de reglas
- `prompts/policy_exp4.md`: plan antes de actuar
- `prompts/policy_exp5.md`: reglas adversarias compactas

Para cumplir la entrega final, cada experimento debe ejecutarse sobre las tareas objetivo y guardar su JSON en `simulations/`.

## Conclusion preliminar

La ampliacion del dominio introduce verificacion SMS, validacion de rol, tareas adversarias, prompt injection e instrucciones prohibidas. La conclusion final debe completarse con las metricas reales de Gemma 4 pass^10.
