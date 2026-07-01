# Experimento 2 - Secuencias de accion explicitas

## Tecnica

Plan generation before acting + revision de especificidad.

## Tareas objetivo

- `sales_laptop_budget`
- `order_cancel_pending`

## Cambio probado

Se agrego una regla operativa para que el agente piense la secuencia minima antes de actuar:

```text
Antes de ejecutar una operacion de venta o cancelacion, identifica la secuencia obligatoria:
1. consultar o buscar la entidad real con herramientas
2. validar elegibilidad segun politica y estado
3. ejecutar la accion de escritura solo si procede
4. comunicar el resultado exacto devuelto por la herramienta
```

Para ventas:

```text
Si el cliente acepta comprar un producto recomendado, llama a crear_pedido con el producto exacto y confirma el pedido creado.
```

Para cancelaciones:

```text
Si el pedido esta pendiente, primero consulta el pedido, luego llama a cancelar_pedido y finalmente comunica el estado cancelado.
```

## Resultado observado

La tecnica buscaba reducir fallas por omision de herramientas de escritura. En las corridas pass^5 finales, `sales_laptop_budget` y `order_cancel_pending` siguieron en 0/5, por lo que el cambio no fue suficiente para Gemma 4 en esas tareas.
