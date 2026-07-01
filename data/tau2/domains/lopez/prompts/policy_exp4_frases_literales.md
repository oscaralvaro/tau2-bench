# Experimento 4 - Frases literales de comunicacion

## Tecnica

Revision de claridad + repeticion de condiciones criticas.

## Tareas objetivo

- `warranty_valid_precheck`
- `order_cancel_delivered_rejected`
- `support_ticket_ready_pickup`
- `sales_out_of_stock_component`

## Cambio probado

Se agregaron frases obligatorias para casos donde el evaluador revisa comunicacion exacta:

```text
Si no hay stock, incluye la frase exacta `no hay stock`.
Si la garantia esta vigente, incluye la frase exacta `garantia vigente`.
Si un pedido entregado no puede cancelarse, incluye la frase exacta `no se puede cancelar`.
Si el ticket esta listo, incluye la frase exacta `listo para recojo`.
```

## Resultado observado

La tecnica funciono bien en tareas de comunicacion directa: `sales_out_of_stock_component` y `support_ticket_ready_pickup` alcanzaron 5/5. En `warranty_valid_precheck`, el modelo aun omitio o reformulo parte de la frase esperada, por lo que quedo en 0/5.
