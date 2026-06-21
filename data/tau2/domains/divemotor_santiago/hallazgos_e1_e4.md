# Hallazgos acumulados E1-E4 - Divemotor Santiago

Autor: Santiago Nunez Arcaya

> Documento en construccion. Los apartados E4 se completaran con valores y fragmentos de las simulaciones B, C y D. Las interpretaciones finales deben ser revisadas por el autor para reflejar sus propias conclusiones.

## 1. Descripcion del dominio y las tareas

El dominio representa la atencion comercial de Divemotor Santiago para clientes personales y empresariales. El agente consulta vehiculos, valida presupuesto y stock, crea cotizaciones y ejecuta operaciones sensibles como aprobar cotizaciones, crear pedidos y cancelar pedidos. Estas acciones modifican una base estructurada y, por ello, deben estar fundamentadas en herramientas y sujetas a verificacion de identidad.

El conjunto evoluciono de 10 tareas iniciales a 20 tareas. Los escenarios incorporan consultas, cotizaciones, pedidos, presion emocional, afirmaciones falsas, prompt injection, operaciones parciales, solicitudes fuera de alcance y verificacion SMS correcta e incorrecta. E4 reutiliza las diez tareas dificiles de E3: 1, 3, 7, 10, 11, 12, 14, 15, 18 y 19.

El total exacto de simulaciones E1-E4 se completara al terminar D, contando los JSON realmente entregados y evitando contar intentos interrumpidos o duplicados.

## 2. Evolucion del agente a lo largo de las entregas

E1 uso `pass^1`, mientras E2, E3 y E4 usan varias repeticiones. Por esa diferencia metodologica, E1 sirve como punto de partida descriptivo y no como comparacion numerica directa.

| Entrega | Cambio principal | Metrica | Resultado sobre el subconjunto E4 | Delta vs E3 |
| --- | --- | --- | ---: | ---: |
| E1 | Dominio, datos, herramientas y tareas iniciales | pass^1 | No comparable directamente | - |
| E2 | Tareas adversarias, SMS y prompt engineering | pass^5 | Pendiente de recalculo sobre las mismas 10 tareas | - |
| E3 | Taxonomia de fallos y siete iteraciones del prompt | pass^5 | 30/50 (60%) | 0 pp |
| E4 | RAG agentico y herramienta `think` | pass^5 | Pendiente | Pendiente |

La comparacion valida entre E2, E3 y E4 se calculara usando las mismas diez tareas. Esto evita atribuir una diferencia al agente cuando en realidad proviene de haber evaluado tareas distintas.

## 3. Categorias de fallo mas frecuentes

### POLICY_MISS

En E3 esta categoria describe decisiones que contradicen la politica o el alcance solicitado. En el baseline se registraron 15 casos. Un patron fue continuar desde una cotizacion correcta hacia SMS, aprobacion y pedido, aunque el usuario solo habia solicitado cotizar.

Evidencia E3 pendiente de insertar desde el JSON: mensaje del usuario, llamada a `crear_cotizacion` y accion posterior no solicitada. La misma tarea se revisara en B, C y D para determinar si `retrieve_policy` recupero la regla de alcance exacto.

### INCOMPLETE

En E3 se registraron 5 casos en los que el agente no termino una cadena dependiente. En la tarea 14 verificaba el SMS, pero no siempre aprobaba la cotizacion y creaba el pedido. E4 permitira observar si recuperar juntas las reglas de SMS y pedidos facilita completar la secuencia o si el chunking separa informacion necesaria.

### Otras categorias por validar en E4

Se revisaran los JSON para identificar llamadas de herramienta incorrectas, ciclos, cierre prematuro, falta de recuperacion de politica y uso inutil de `think`. Solo se incluiran categorias con evidencia observable.

## 4. Comportamiento especifico de Gemma 4 en el dominio

Los experimentos previos muestran dos comportamientos que deben verificarse nuevamente. Primero, el modelo puede sobre-ejecutar un flujo comercial: interpreta cotizar como el inicio de una compra completa. Segundo, puede completar correctamente pasos individuales pero perder dependencias de varios pasos, especialmente cuando debe verificar SMS, aprobar y luego crear un pedido.

Los dos ejemplos concretos de E4 se insertaran desde las conversaciones reales. Para cada uno se mostrara el mensaje del usuario, la recuperacion de politica o el pensamiento registrado y la accion posterior del agente.

## 5. Recomendaciones para un sistema de produccion

Esta seccion se cerrara despues de comparar A, B, C y D. Se separaran consultas de lectura, operaciones comerciales reversibles y operaciones sensibles que modifican stock o estado. Los umbrales propuestos se justificaran con el pass^5 observado y no solo con una apreciacion general del modelo.

