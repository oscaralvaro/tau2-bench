# Dominio: sanita_irigoin
**Autor:** Maricielo Nicolle Irigoin Cabrera

---

## Descripción del Dominio

El dominio `sanita_irigoin` simula un agente virtual de atención al cliente
para una distribuidora de insumos agrícolas especializada en el cultivo de
arroz. El agente ayuda a los agricultores a elegir productos (fertilizantes,
herbicidas y plaguicidas), verificar disponibilidad, crear pedidos y hacer
seguimiento, todo bajo las políticas comerciales del negocio.

---

## Entidades

- **Usuario**: Cliente identificado por `user_id`. Puede ser `nuevo` o
  `frecuente`. El tipo de cliente determina las condiciones de pago disponibles.
- **Suelo**: Caracterizado por nombre, pH y nivel de nutrientes
  (`bajo`, `medio`, `alto`).
- **Cultivo**: Identificado por etapa (`almacigo`, `siembra`,
  `crecimiento`, `cosecha`).
- **Producto**: Tiene tipo (`fertilizante`, `herbicida`, `plaguicida`),
  composición, precio y stock.
- **Pedido**: Vincula un usuario con un producto, método de pago
  (`efectivo`, `transferencia`) y estado de entrega
  (`pendiente`, `entregado`).
- **Diagnóstico**: Asocia un suelo y un cultivo con un problema detectado
  (`bajo_nutrientes`, `salinidad`, `plagas`, `maleza`).
- **Inventario**: Registra el stock actual y mínimo de cada producto.

---

## Herramientas (Tools)

### Lectura (sin efectos secundarios)
- `get_user_details(user_id)`: Retorna nombre y tipo de cliente.
- `get_producto_details(producto_id)`: Retorna información completa del producto.
- `check_stock(producto_id)`: Verifica si un producto tiene stock disponible.
- `get_soil_details(suelo_id)`: Retorna características del suelo.
- `get_crop_details(cultivo_id)`: Retorna la etapa actual del cultivo.
- `recommend_fertilizer(diagnostico_id, presupuesto)`: Recomienda un
  fertilizante dentro del presupuesto con stock disponible.
- `suggest_alternative(producto_id)`: Sugiere un producto alternativo del
  mismo tipo si no hay stock.
- `validate_budget(producto_id, presupuesto)`: Verifica si el precio entra
  dentro del presupuesto del cliente.
- `get_order_details(order_id)`: Retorna los detalles de un pedido existente.

### Escritura (modifican estado)
- `create_order(user_id, producto_id, cantidad, metodo_pago, estado_pago)`:
  Crea un pedido si hay stock suficiente y el pago es válido según el tipo
  de cliente. Descuenta el stock automáticamente.

### Escalamiento
- `escalate_to_human(motivo)`: Escala la conversación a un vendedor humano.

---

## Resumen de Política

La política completa está en `data/tau2/domains/sanita_irigoin/policy.md`.
Reglas principales:

### Recomendación
- Solo recomendar productos para el cultivo de arroz.
- Considerar tipo de suelo, etapa del cultivo y nivel de nutrientes.
- Ajustarse al presupuesto del cliente.
- Nunca recomendar productos sin stock.
- Si no hay stock, sugerir alternativa del mismo tipo.

### Pagos
- **Clientes nuevos**: Solo pueden pagar al contado (efectivo o transferencia).
- **Clientes frecuentes**: Pueden pagar al contado, a crédito o en cuotas.
- Si un cliente nuevo solicita crédito, rechazar y explicar la política.

### Pedidos
- Solo crear pedidos si hay stock suficiente.
- El stock se descuenta automáticamente al confirmar.
- El estado de entrega inicial es siempre `pendiente`.

### Casos fuera de dominio
El agente rechaza solicitudes sobre cultivos distintos al arroz, servicios
no ofrecidos (fumigación, asesoría presencial), productos fuera del
catálogo, y acciones fuera del sistema.

### Escalamiento
Escalar cuando el cliente solicita atención humana, la consulta es muy
técnica, o hay un problema con un pedido ya entregado.

---

## Tareas (15 en total)

| ID | Descripción | Tipo |
|---|---|---|
| 0 | Consulta detalles de producto disponible | Consulta simple |
| 1 | Verificar stock de producto | Consulta simple |
| 2 | Crear pedido al contado con stock disponible | Modificación exitosa |
| 3 | Crear pedido a crédito (cliente frecuente) | Modificación exitosa |
| 4 | Cliente nuevo intenta pagar a crédito | Rechazo por política |
| 5 | Comprar producto sin stock → sugerir alternativa | Rechazo + alternativa |
| 6 | Recomendar fertilizante dentro del presupuesto | Recomendación exitosa |
| 7 | Recomendación con presupuesto insuficiente | Rechazo por presupuesto |
| 8 | Consultar estado de pedido existente | Consulta simple |
| 9 | Consultar perfil de cliente | Consulta simple |
| 10 | Consultar etapa de cultivo | Consulta simple |
| 11 | Cliente pide producto para maíz (fuera de dominio) | Rechazo fuera de dominio |
| 12 | Cliente solicita fumigación presencial | Rechazo fuera de dominio |
| 13 | Comprar más unidades de las que hay en stock | Edge case |
| 14 | Cliente insatisfecho solicita vendedor humano | Escalamiento |

---

## Métricas obtenidas

- **Average Reward**: 0.9333
- **COMMUNICATE**: 1.000
- **DB**: 0.500
- **Pass^k (k=1)**: 0.933