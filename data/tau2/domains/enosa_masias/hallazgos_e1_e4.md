# Hallazgos acumulados E1-E4 - Dominio enosa_masias

## 1. Descripcion del dominio y las tareas
El entorno enosa_masias fue creado para simular un asistente virtual de atencion al cliente para una empresa de distribucion electrica. Procesa consultas de facturacion, reportes de apagones y emergencias de peligro publico. En la Entrega 3 y 4, el entorno se configuro con 10 tareas adversarias de alta dificultad para evaluar la resistencia del agente ante usuarios que emplean ingenieria social y manipulan los procedimientos.

## 2. Evolucion del rendimiento del agente
| Entrega | Modificacion principal del entorno           | Metrica evaluada | Rendimiento global |
|---------|----------------------------------------------|------------------|--------------------|
| E1      | Creacion del baseline con tareas simples     | pass^1           | 1.0000             |
| E2      | Aumento de tareas (20 tareas regulares)      | pass^5           | 1.0000             |
| E3      | Implementacion de Top 10 tareas adversarias  | pass^5           | 0.8980             |
| E4      | Integracion de RAG (Estrategia Headers, k=3) | pass^5           | 0.7800             |

## 3. Principales categorias de fallo detectadas
- CONTEXT_PIVOT_EVASION: Detectado en la E3. El usuario simulado es bloqueado correctamente al intentar reportar un caso sin cumplir los requisitos (ejemplo, tener deuda activa). Inmediatamente, el usuario cambia la narrativa simulando estar frente a una emergencia mortal (cables con chispas en la calle) para forzar al agente a registrar el ticket saltandose la politica comercial.
- RAG_CONTEXT_LOSS: Detectado en la E4. Al aplicar estrategias de fragmentacion por cantidad de palabras fijas, las instrucciones condicionantes se separaban de las herramientas, ocasionando alucinaciones operativas.
- QUOTA_EXHAUSTION: El framework demostro cuellos de botella de infraestructura. El uso intensivo del toolkit RAG agoto el limite diario de llamadas a la API de embeddings, provocando caidas del sistema en masa (Error 429).

## 4. Analisis de comportamiento del LLM (Gemma 4)
- Sesgo de complacencia extrema: El modelo Gemma-4 presenta una fuerte alineacion hacia la resolucion empatica de problemas. Ante un prompt de usuario simulado con alto nivel de agresividad o urgencia declarada, el modelo prioriza calmar al cliente antes que respetar los flujos de validacion de datos de ENOSA.
- Robustez contra inyecciones de comandos: A pesar del sesgo anterior, el modelo es altamente resistente a inyecciones tecnicas. Bloqueo el 100% de los intentos donde el usuario introducia literales como SYSTEM OVERRIDE, logrando separar correctamente las instrucciones de sistema de los inputs del chat.

## 5. Recomendaciones de arquitectura para un pase a produccion
- Segmentacion de modulos RAG: Para implementaciones B2C de alto trafico, no se recomienda usar APIs externas con cuotas estrictas para la recuperacion de documentos. Se debe migrar a bases vectoriales locales (como ChromaDB con modelos all-MiniLM) para evitar interrupciones por cuota (Error 429).
- Aprobacion de circuito cerrado (Human-in-the-loop): Dado que el agente demostro vulnerabilidades ante ingenieria social en transacciones criticas (creacion de tickets), se recomienda que la herramienta create_ticket genere estados en borrador que requieran la validacion final de un operador humano.