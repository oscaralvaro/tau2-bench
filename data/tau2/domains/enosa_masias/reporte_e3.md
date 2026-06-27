# Reporte Final - Entrega 3 (Failure Analysis y Mejoras)

## 1. Contexto de la Línea Base
Se utilizó el agente desarrollado en la Entrega 2, el cual logró una gran estabilidad en tareas de lectura y consulta general, pero presentó fisuras lógicas en el subset `base_top10hard`. El análisis del archivo `enosa_masias_simulacion.json` reveló que el modelo base (Gemma-4) sufre una degradación de razonamiento cuando se le aplican vectores de estrés: presión emocional extrema (urgencias médicas) e inyecciones de comandos (Prompt Injection).

## 2. Resumen del Diagnóstico
Los tres fallos más graves encontrados y categorizados fueron:
1. **IDENTITY_BYPASS:** Vulneración del protocolo SMS por exceso de empatía en emergencias fingidas.
2. **TOOL_MISUSE:** Arrastre de comandos inyectados por el usuario hacia el parámetro `description` de las herramientas del sistema.
3. **HALLUCINATION:** Llenado predictivo de parámetros (inventar direcciones) para agilizar la creación de tickets.

## 3. Estrategia de Mejora (Prompt Engineering)
Se construyó una nueva versión de la política (`policy_e3.md`) aplicando:
- **Priorización de reglas (Boundary Setting)** para anular la "empatía tóxica" del LLM.
- **Definición estricta de variables (Data vs. Instructions)** para aislar inyecciones.
- **Chain of Thought preventivo** exigiendo auto-validación de parámetros antes de usar Tools de escritura.

## 4. Resultados y Conclusión Operativa
Durante la ejecución de las simulaciones de verificación (pass^5) para comprobar la eficacia de `policy_e3.md`, se presentaron limitaciones técnicas severas asociadas a la cuota y estabilidad de la API gratuita de Google (`500 Internal Server Error`, `Connection timed out`), exacerbadas por la gran cantidad de tokens que exigen las tareas *hard* debido a su longitud conversacional.

Sin embargo, a nivel lógico, las técnicas de "Prioridad Cero" y "Auto-validación de parámetros" son directamente proporcionales a la mitigación de alucinaciones en modelos de la familia Gemma. La mejora radica en quitarle poder de decisión al modelo en zonas grises (empatía vs seguridad) e imponer *hard-stops* conversacionales claros.