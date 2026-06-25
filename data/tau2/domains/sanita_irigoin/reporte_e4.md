# Reporte E4 - Sanita Irigoin

## Configuracion del experimento

- Politica fuente: `policy.md` (851 palabras, 11 secciones `##`).
- Modelo: `gemini/gemma-4-31b-it`.
- Subconjunto de evaluacion: tareas 2, 3, 5, 13, 15, 16, 21, 22, 23 y 24.
- Limite de pasos: B, C y D se corrieron con `--max-steps 30`. La condicion A se copio desde E3 como baseline, sin ejecutar simulaciones nuevas.
- Estrategia de tamano fijo elegida para C: `fixed_200`.
- Motivo: la politica tiene 851 palabras; `fixed_200` produce 5 chunks y conserva mas granularidad que `fixed_400`, que daria solo 3 chunks.

## Tabla de chunks por estrategia

| Estrategia | Num. chunks | Palabras promedio por chunk |
|------------|-------------|-----------------------------|
| headers    | 12          | 70.9                        |
| fixed_200  | 5           | 170.2                       |

## Matriz de resultados

En esta tabla, `pass^5` significa tareas que pasaron 5/5 trials sobre las 10 tareas del subconjunto E4. Tambien reporto el total bruto de rewards para mostrar la diferencia entre estabilidad perfecta y desempeno promedio.

| Condicion                 | Sin think | Con think |
|---------------------------|-----------|-----------|
| A - Baseline E3 (sin RAG) | 9/10 tareas 5/5; 45/50 rewards | - |
| B - headers, k=3          | 6/10 tareas 5/5; 44/50 rewards | - |
| C - fixed_200, k=3        | 8/10 tareas 5/5; 48/50 rewards | - |
| D - fixed_200, k=3        | - | 7/10 tareas 5/5; 46/50 rewards |

## Analisis

### Chunking: comparar B y C con A

La mejor estrategia RAG fue `fixed_200`. Condicion B (`headers`) obtuvo 6/10 tareas con 5/5, mientras que condicion C (`fixed_200`) obtuvo 8/10 tareas con 5/5. En rewards brutos, B tuvo 44/50 y C tuvo 48/50. Esto indica que, para esta politica, los chunks por headers fueron demasiado dependientes del encabezado recuperado: varias consultas traian secciones correctas pero incompletas para ejecutar todo el flujo.

Un ejemplo aparece en B, tarea 13. El agente llama varias veces a `retrieve_policy`, pero los chunks recuperados mezclan secciones de catalogo, cambio de opinion y reglas generales, sin devolver una lista clara de productos ni stock. En el JSON se observa:

```text
assistant TOOL retrieve_policy: {"query":"todos los productos disponibles y sus IDs"}
tool: ## Proceso de Atencion ... ## Ejemplo Few-Shot: Cambio de Opinion con IDs ... ## REGLA CRITICA ...
assistant TOOL retrieve_policy: {"query":"lista de IDs de productos"}
tool: ## Regla de Cambio de Opinion ... ## Checklist Interno: Pedido Grande o a Credito con IDs ...
termination_reason: max_steps
```

En cambio, C mejora las tareas mas dificiles. La tarea 21, que en A solo tuvo 1/5, subio a 4/5 con `fixed_200`. Un trial exitoso de C muestra que el agente actualizo el producto final correctamente:

```text
user: En realidad, en vez de Urea 46%, quiero NPK 20-20-20, las mismas 3 unidades al contado en efectivo.
assistant TOOL check_stock: {"producto_id":"P002"}
tool: {"producto_id":"P002","stock_actual":"30","disponible":"True"}
assistant: Tengo stock disponible de NPK 20-20-20. ¿Confirmas el pedido...?
assistant TOOL create_order: {"producto_id":"P002","user_id":"U001","estado_pago":"al contado","metodo_pago":"efectivo","cantidad":3}
```

Aunque C fue el mejor RAG, no supero al baseline A en pass^5 global: A tuvo 9/10 tareas perfectas y C tuvo 8/10. La mejora principal de C fue sobre los casos que ya eran fragiles en E3, especialmente cambio de opinion y SMS.

### Think tool: comparar D con C

La condicion D uso la mejor estrategia de chunking (`fixed_200`) con `use_think=true`. El JSON confirma uso real de think: hubo 79 llamadas a `think`, 63 llamadas a `retrieve_policy`, y 34 de las 50 simulaciones incluyeron al menos una llamada `think`.

Ejemplo util de think en tarea 2:

```text
assistant TOOL retrieve_policy: {"query":"pedido de Urea 46% al contado"}
assistant TOOL think: {"thought":"The user wants to order 3 units of \"Urea 46%\"... check stock using check_stock(producto_id=\"P001\")... ask for explicit confirmation... SMS verification is not required."}
```

Sin embargo, think no mejoro el resultado final: D obtuvo 7/10 tareas perfectas y 46/50 rewards, menor que C (8/10 y 48/50). El problema no fue falta de razonamiento, sino que el modelo siguio cometiendo errores de argumentos de herramienta o se quedo sin pasos. En D, tarea 3 fallo por `max_steps` despues de equivocarse con los parametros de `create_order`:

```text
assistant TOOL create_order: {"user_id":"U003","metodo_pago":"credito","producto_id":"P002","cantidad":5,"estado_pago":"pendiente"}
tool: {"error":"Metodo de pago invalido. Use 'efectivo' o 'transferencia'."}
assistant TOOL think: {"thought":"... use metodo_pago='transferencia' ..."}
assistant TOOL create_order: {"user_id":"U003","metodo_pago":"transferencia","producto_id":"P002","cantidad":5,"estado_pago":"pendiente"}
tool: {"error":"Estado de pago invalido. Use 'al contado', 'credito' o 'cuotas'."}
termination_reason: max_steps
```

Think ayudo a diagnosticar el error, pero llego tarde y consumio pasos. Para este dominio, la herramienta think no fue suficiente para compensar errores en argumentos estructurados.

## Tarea por tarea (mejor condicion RAG: C fixed_200)

| Tarea ID | Descripcion breve | pass^5 baseline A | pass^5 C | Cambio |
|----------|-------------------|-------------------|----------|--------|
| 2  | Pedido al contado con stock disponible | 5/5 | 5/5 | Igual |
| 3  | Pedido a credito de cliente frecuente | 5/5 | 5/5 | Igual |
| 5  | Producto sin stock y alternativa | 5/5 | 4/5 | Bajo |
| 13 | Cantidad mayor al stock disponible | 5/5 | 5/5 | Igual |
| 15 | Falsa promesa de credito para cliente nuevo | 5/5 | 5/5 | Igual |
| 16 | Usuario nuevo afirma ser frecuente | 5/5 | 5/5 | Igual |
| 21 | Cambio de opinion sobre producto | 1/5 | 4/5 | Mejoro |
| 22 | Flujo exitoso de SMS | 4/5 | 5/5 | Mejoro |
| 23 | Codigo SMS incorrecto | 5/5 | 5/5 | Igual |
| 24 | Consulta de pedidos y cancelacion masiva | 5/5 | 5/5 | Igual |

## Conclusion

RAG con `fixed_200` fue la mejor condicion nueva: obtuvo 8/10 tareas perfectas y 48/50 rewards. La estrategia `headers` fue peor, probablemente porque algunos encabezados aislan reglas que el modelo necesita combinar con catalogo, stock, confirmacion y SMS. El think tool fue usado realmente, pero no mejoro a C: produjo 7/10 tareas perfectas y varios fallos por `max_steps` o argumentos incorrectos de herramientas. En este dominio, RAG sirve para reforzar casos dificiles como cambio de opinion y SMS, pero el baseline E3 aun fue mas estable en pass^5 global.
