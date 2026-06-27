# Policy E3 experimento 2: mejora top 10 despues del baseline

Simulacion asociada:

- `data/simulations/sim_e3_final_estaciondeservicio_Rivera.json`

Objetivo:

Corregir las fallas detectadas en el baseline, especialmente tarea 4 y tarea 13.

Tecnicas utilizadas:

- Claridad y especificidad para el producto de lubricante.
- Grounding en resultado de herramienta: usar el `id` devuelto por `register_payment_method`.
- Estructura por campos obligatorios antes de `register_order`.
- Normalizacion de fecha local ISO sin `Z`.

Reglas experimentales:

- Si el usuario pide lubricante asociado, no elijas por inferencia. Usa producto, `id_item` y cantidad exacta.
- En ordenes de lubricante, pasa siempre `id_order_combustible_asociado`.
- Despues de `register_payment_method`, conserva el `id` devuelto y usalo como `payment_method_id`.
- Antes de `register_order`, revisa que tengas fecha local ISO sin `Z`, decision de factura virtual, correo de factura si aplica y observaciones.
- Si el usuario pide factura virtual o menciona correo de factura para la orden, pasa `solicitar_factura_virtual=True` y ese correo en `email_factura`.
- Si no hay observaciones, pasa `observaciones=None`; no omitas el campo.

Resultado:

- 45/50 simulaciones con reward completo.
- La tarea 4 paso de 0/5 a 5/5.
- La tarea 13 siguio en 0/5 por un requisito de factura virtual que no aparecia en el dialogo.
