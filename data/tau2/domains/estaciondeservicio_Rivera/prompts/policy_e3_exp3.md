# Policy E3 experimento 3: ajuste residual de factura virtual en tarea 13

Simulacion asociada:

- `data/simulations/sim_e3_exp3_task13_pass5.json`

Objetivo:

Corregir la falla residual de la tarea 13 observada en `sim_e3_final_estaciondeservicio_Rivera.json`.

Tecnicas utilizadas:

- Claridad y especificidad en el usuario simulado.
- Grounding por campos obligatorios antes de `register_order`.
- Normalizacion de factura virtual.

Regla experimental:

- Si el escenario espera factura virtual, el usuario debe mencionarla explicitamente durante los datos del pedido.
- Si el escenario espera registrar transferencia bancaria, la llamada a `register_payment_method` debe usar literalmente `source="bank_transfer"`, no "transferencia" ni "transferencia bancaria".
- Si el usuario menciona factura virtual o correo de factura, `register_order` debe usar:
  - `solicitar_factura_virtual=True`
  - `email_factura` con el correo indicado
  - `observaciones=None` si no hay observaciones
- No depender de defaults de la herramienta cuando la evaluacion compara el campo.

Resultado:

- Task 13 paso de 0/5 en `sim_e3_final_estaciondeservicio_Rivera.json` a 5/5 en esta corrida focalizada.
