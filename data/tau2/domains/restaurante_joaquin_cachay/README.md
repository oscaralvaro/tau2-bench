# restaurante_joaquin_cachay

Autor: Joaquin Cachay Cornejo

## Domain Summary

El dominio `restaurante_joaquin_cachay` modela un asistente de atencion al cliente para un restaurante de tipo casual-premium llamado Restaurante Joaquin Cachay. El agente ayuda a clientes que quieren consultar el menu, revisar disponibilidad, hacer reservas, crear pedidos de tipo dine-in, takeout o delivery, registrar pagos y consultar el estado de sus ordenes o reservas.

El objetivo del dominio es simular un caso de soporte realista y evaluable automaticamente dentro de Tau2-Bench, donde el agente debe combinar consulta de informacion, operaciones sobre una base de datos estructurada y cumplimiento estricto de reglas de negocio.

A diferencia de un dominio puramente informativo, este dominio incluye tanto operaciones de lectura como de escritura sobre el estado del restaurante. Por eso resulta util para evaluar si un agente:

- entiende informacion estructurada del negocio
- pide los datos minimos requeridos antes de actuar
- rechaza solicitudes invalidas o incompletas
- no inventa disponibilidad, precios ni estados
- confirma acciones de escritura antes de ejecutarlas

## Business Scope

El restaurante ofrece tres modalidades de servicio:

- `dine_in`: consumo en el local
- `takeout`: recojo en tienda
- `delivery`: despacho a domicilio

Las operaciones cubiertas por el dominio incluyen:

- consultas de informacion general del restaurante
- consultas del menu y disponibilidad de platos
- consultas de mesas y reservas
- creacion de perfiles de cliente
- creacion y cancelacion de reservas
- creacion de pedidos
- consulta del estado de pedidos
- registro de pagos
- cierre de pedidos
- cancelacion de pedidos
- registro de resenas

## Main Entities

### RestaurantInfo
Contiene la informacion principal del negocio:

- nombre del restaurante
- tipo de cocina
- telefono y email
- direccion
- coordenadas geograficas
- horario de atencion
- si acepta dine-in, takeout y delivery
- ticket promedio
- si tiene programa de fidelizacion

### DiningArea
Representa una zona fisica del restaurante, por ejemplo:

- salon principal
- terraza
- sala privada

Cada zona tiene:

- id
- nombre
- tipo de area
- accesibilidad
- reglas operativas basicas

### RestaurantTable
Representa una mesa del restaurante. Cada mesa tiene:

- id
- numero visible
- area a la que pertenece
- capacidad
- estado
- mesas combinables

Los estados de mesa permiten simular disponibilidad realista:

- `available`
- `occupied`
- `reserved`
- `cleaning`
- `out_of_service`

### MenuCategory
Agrupa items del menu:

- entradas
- fondos
- bebidas
- postres

Cada categoria tiene:

- id
- nombre
- descripcion
- orden visual
- estado activo/inactivo

### MenuItem
Representa un plato o bebida. Cada item puede incluir:

- id
- categoria
- nombre y descripcion
- precio base
- disponibilidad
- tiempo estimado de preparacion
- nivel de picante
- banderas dietarias: vegetariano, vegano, gluten free
- informacion de alergenos
- informacion nutricional
- modificadores disponibles
- ingredientes asociados

### ModifierGroup / ModifierOption
Permiten personalizar productos, por ejemplo:

- acompanamiento del plato
- tamano de bebida

Esto hace que el dominio sea mas realista para pedidos de restaurante, ya que el agente debe respetar disponibilidad y estructura de modificadores.

### Ingredient
Representa inventario basico del restaurante:

- id
- nombre
- unidad de medida
- stock actual
- nivel de reposicion
- proveedor
- costo por unidad
- estado de stock
- si requiere refrigeracion

Aunque el agente no manipula directamente inventario en las tareas actuales, esta capa permite justificar disponibilidad de productos y enriquecer el realismo del dominio.

### CustomerProfile
Representa al cliente registrado. Contiene:

- customer id
- nombre completo
- telefono
- email
- puntos de fidelizacion
- preferencias dietarias
- platos favoritos
- direccion por defecto

### Reservation
Representa una reserva y contiene:

- reservation id
- customer id
- cantidad de personas
- fecha
- hora
- estado
- mesas asignadas
- solicitudes especiales
- timestamp de creacion

Estados de reserva cubiertos en el dominio:

- `pending`
- `confirmed`
- `seated`
- `completed`
- `cancelled`
- `no_show`

### RestaurantOrder
Representa una orden del restaurante. Incluye:

- order id
- customer id
- tipo de orden
- estado
- mesa o reserva asociada, si aplica
- items pedidos
- subtotal
- impuestos
- cargo por servicio
- descuentos
- total
- historial de pagos
- informacion de delivery, si aplica
- timestamps de creacion y cierre

Estados de orden modelados:

- `draft`
- `received`
- `in_preparation`
- `ready`
- `served`
- `completed`
- `cancelled`

### Payment
El dominio soporta diferentes tipos de pago:

- cash
- credit_card
- debit_card
- mobile_wallet
- gift_card

Esto permite evaluar escenarios de pago realistas, como registrar un pago movil y luego cerrar una orden.

### Review
Representa feedback del cliente:

- review id
- cliente asociado
- orden asociada
- rating
- comentario
- fecha de creacion

## Tools

El dominio implementa herramientas del lado del asistente y tambien herramientas del lado del usuario.

### Assistant Tools

#### Read tools

- `get_restaurant_info`
  - devuelve la configuracion general y perfil del restaurante
- `get_menu`
  - devuelve el menu; puede filtrar solo items disponibles
- `get_menu_item_details(menu_item_id)`
  - devuelve el detalle de un item especifico
- `get_available_tables(party_size, area_id=None)`
  - busca mesas disponibles para un tamano de grupo
- `get_customer_profile(customer_id)`
  - devuelve el perfil del cliente
- `get_reservation_details(reservation_id)`
  - devuelve el detalle de una reserva
- `get_order_details(order_id)`
  - devuelve el detalle de una orden

#### Write tools

- `create_customer_profile(...)`
  - crea un nuevo cliente o reutiliza uno existente por telefono
- `create_reservation(...)`
  - crea una reserva y asigna mesa si existe disponibilidad
- `seat_reservation(reservation_id)`
  - marca una reserva como seated
- `cancel_reservation(reservation_id)`
  - cancela una reserva
- `create_order(...)`
  - crea una orden dine-in, takeout o delivery
- `update_order_item_status(order_id, order_item_id, status)`
  - actualiza el estado de un item dentro de una orden
- `record_payment(order_id, payment)`
  - registra un pago asociado a una orden
- `close_order(order_id)`
  - cierra una orden ya pagada
- `cancel_order(order_id)`
  - cancela una orden
- `update_table_status(table_id, status)`
  - cambia el estado de una mesa
- `submit_review(...)`
  - registra una resena posterior al servicio

#### Generic tools

- `calculate(expression)`
  - calcula expresiones matematicas simples

### User Tools

El dominio tambien incluye herramientas de usuario para representar el comportamiento del cliente durante simulaciones mas ricas:

- `view_profile`
- `update_profile`
- `set_dining_preferences`
- `browse_menu`
- `view_cart`
- `add_item_to_cart`
- `remove_item_from_cart`
- `clear_cart`
- `request_reservation`
- `confirm_reservation_request`
- `cancel_active_reservation`
- `view_active_reservation`
- `submit_order`
- `view_active_order`
- `request_payment`
- `confirm_payment`
- `set_presence`

Estas herramientas permiten representar tanto el estado del negocio como el estado visible del cliente, aunque las tareas de entrega estan enfocadas principalmente en el lado del asistente.

## Policy Summary

La politica completa se encuentra en:

- `data/tau2/domains/restaurante_joaquin_cachay/policy.md`

Resumen de reglas principales:

### Reglas generales

- El agente no debe inventar disponibilidad, precios, estados, cargos, pagos ni resultados.
- Solo puede usar items y modificadores que existan realmente en la base de datos y esten disponibles.
- Debe usar como fuente de verdad las tools y la base de datos del dominio.

### Confirmacion explicita

Antes de cualquier accion que modifique estado, el agente debe:

- resumir lo que va a hacer
- pedir confirmacion explicita del usuario, por ejemplo: `yes`

Esto aplica a:

- crear reservas
- cancelar reservas
- crear pedidos
- registrar pagos
- cerrar pedidos
- cancelar pedidos
- registrar resenas

### Reservas

Para crear una reserva, el agente debe tener como minimo:

- nombre del cliente
- telefono
- cantidad de personas
- fecha
- hora

Si existe mesa disponible adecuada, la reserva puede quedar `confirmed`.
Si no existe capacidad suficiente, la reserva puede quedar `pending`.

### Pedidos

Para crear un pedido, el agente debe confirmar:

- items solicitados
- cantidades
- modificadores
- instrucciones especiales

Para delivery, ademas debe tener:

- direccion completa
- nombre del contacto
- telefono del contacto

Si falta informacion esencial, el agente no debe crear la orden.

### Disponibilidad

Si un plato no esta disponible, el agente debe:

- decir claramente que no esta disponible
- no crear una orden con ese item
- no inventar sustitutos sin soporte de tools

### Pagos

El agente solo debe registrar pagos sobre una orden existente.
No debe decir que una orden esta pagada si no se ha registrado realmente el pago via tool.
No debe volver a cobrar una orden ya pagada o completada.

### Escalamiento a humano

El agente debe escalar a humano solo cuando la solicitud excede el alcance de las tools, por ejemplo:

- compensaciones
- descuentos manuales
- incidentes graves o de seguridad
- excepciones a la politica
- arreglos especiales no soportados por el sistema

## Database Summary

La base de datos del dominio se encuentra en:

- `data/tau2/domains/restaurante_joaquin_cachay/db.json`

Resumen actual:

- 1 restaurante principal
- multiples zonas del local
- multiples mesas con distintos estados
- categorias de menu
- items del menu con disponibilidad realista
- modificadores de platos y bebidas
- ingredientes con distintos estados de stock
- 6 clientes registrados
- 6 reservas con estados variados
- 8 ordenes con estados variados
- empleados en distintos roles
- reviews historicas

El dataset fue disenado para cubrir tanto casos exitosos como edge cases y rechazos por politica.

## Tasks Summary

El dominio contiene 12 tareas en total, divididas en `train`, `test` y `base`.

Archivo:

- `data/tau2/domains/restaurante_joaquin_cachay/tasks.json`

Splits:

- `train`
- `test`
- `base`

### Tipos de escenarios cubiertos

Las tareas cubren:

- consultas simples de informacion del restaurante
- consultas de menu con restricciones dietarias o disponibilidad
- creacion exitosa de reservas
- cancelacion de reservas existentes
- creacion de pedidos delivery
- creacion de pedidos takeout
- registro de pagos y cierre de ordenes
- cancelacion de ordenes
- rechazo de pedidos con items no disponibles
- rechazo de pedidos con informacion incompleta
- rechazo de intento de cobro duplicado
- caso borde donde una reserva grande queda `pending`

### Representative Tasks

- `restaurant_info_1`
  - consulta basica del restaurante y disponibilidad de delivery
- `restaurant_menu_query_1`
  - consulta de platos principales gluten free y disponibles
- `restaurant_reservation_create_1`
  - crea perfil de cliente y luego crea reserva confirmada
- `restaurant_reservation_cancel_1`
  - cancela una reserva existente tras consultar su estado
- `restaurant_order_delivery_1`
  - crea una orden delivery con items, modificadores y direccion
- `restaurant_order_takeout_1`
  - crea una orden takeout para un nuevo cliente
- `restaurant_payment_close_1`
  - consulta una orden, registra un pago y la cierra
- `restaurant_order_cancel_1`
  - cancela una orden pendiente
- `restaurant_reject_unavailable_item_1`
  - el agente debe rechazar un plato no disponible
- `restaurant_reject_missing_delivery_info_1`
  - el agente debe pedir direccion y no crear la orden
- `restaurant_reject_paid_order_payment_1`
  - el agente debe rechazar cobrar de nuevo una orden ya pagada
- `restaurant_large_party_pending_reservation_1`
  - el agente debe crear una reserva que quede pending por capacidad insuficiente

## Evaluation Design

Las tareas combinan distintos tipos de verificacion disponibles en Tau2-Bench:

- `actions`
  - validan que el agente llame a las tools esperadas
- `communicate_info`
  - validan que comunique informacion clave al usuario
- `nl_assertions`
  - validan cualitativamente el comportamiento esperado del agente

Esto permite evaluar tanto precision operacional como adherencia a la politica.

## Files Included

### Source module
- `src/tau2/domains/restaurante_joaquin_cachay/data_model.py`
- `src/tau2/domains/restaurante_joaquin_cachay/tools.py`
- `src/tau2/domains/restaurante_joaquin_cachay/environment.py`
- `src/tau2/domains/restaurante_joaquin_cachay/utils.py`
- `src/tau2/domains/restaurante_joaquin_cachay/user_data_model.py`
- `src/tau2/domains/restaurante_joaquin_cachay/user_tools.py`

### Data files
- `data/tau2/domains/restaurante_joaquin_cachay/db.json`
- `data/tau2/domains/restaurante_joaquin_cachay/policy.md`
- `data/tau2/domains/restaurante_joaquin_cachay/tasks.json`
- `data/tau2/domains/restaurante_joaquin_cachay/split_tasks.json`

### Registry
- `src/tau2/registry.py`

### Tests
- `tests/domain_tests/restaurante_joaquin_cachay/test_restaurante_joaquin_cachay.py`

## Final Notes

Este dominio fue disenado para representar un escenario realista de atencion al cliente en restaurante, con suficiente estructura para evaluar agentes conversacionales de manera automatica. El foco principal esta en que el agente sea capaz de:

- leer el estado correcto del negocio
- no inventar datos
- pedir informacion minima necesaria
- confirmar acciones antes de modificar estado
- rechazar solicitudes invalidas o incompletas
- operar correctamente sobre reservas, ordenes y pagos
