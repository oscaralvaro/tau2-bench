

Proyecto: Dominio de Filtros para Maquinaria Pesada
Estudiante: Francesco Gastelo
Curso: Introducción a las Redes Neuronales

Resumen del dominio
El dominio filtro_gastelo simula un agente de servicio al cliente para una tienda especializada en filtros de maquinaria pesada (Caterpillar, John Deere, Komatsu, etc.). El agente asiste en la consulta de inventario, precios en soles y la gestión de pedidos especiales a proveedores, asegurando el cumplimiento de políticas de compatibilidad y descuentos por fidelidad.

Entidades
Filter (Item): Componente con ID, marca, nombre, tipo (Aceite, Aire, Hidráulico), precio (S/.) y stock. Incluye compatibilidad mediante equivalent_id.

Customer: Usuario registrado con ID, nombre, celular y registro de compras previas para descuentos.

Pedido a Proveedor: Registro de solicitud para productos sin stock (entrega de 3 a 5 días hábiles).

Tools
get_filter_status(item_id): Verifica stock, precio y disponibilidad inmediata.

search_filter_catalog(brand, filter_type): Filtra el catálogo por marca o tipo de repuesto.

get_equivalent_filter(item_id): Busca repuestos 100% compatibles si el original está agotado.

register_provider_order(customer_name, customer_phone, item_id, quantity): Registra pedidos a proveedores.

get_customer_details(customer_id): Recupera información del cliente y sus beneficios.

escalate_to_human(reason): Transfiere a un especialista en casos de quejas o repuestos técnicos de motor.

Policy Summary
Disponibilidad: Si hay stock, se confirma "Entrega Inmediata". Si no, se busca un equivalente antes de ofrecer pedido a proveedor.

Pedidos: Requieren nombre y celular obligatoriamente. Tiempo de espera de 3-5 días.

Descuentos: 10% para clientes con 10+ compras, 5% para 5+ compras. Clientes nuevos no tienen descuento.

Restricciones: Prohibida la venta de filtros para autos. Solo maquinaria pesada.

Escalamiento: Casos de descuentos no autorizados o repuestos internos de motor (pistones, etc.) se derivan a un humano.

Tasks (15 totales)
El dominio incluye un set de 15 tareas que validan el comportamiento del agente:

Task 0: Caso exitoso: Consulta de stock y precio disponible (JD-101).

Task 1: Consulta de catálogo: Listar todos los filtros de marca Caterpillar.

Task 2: Consulta por categoría: Buscar filtros de tipo "Hidráulico".

Task 3: Flujo de Pedido: Sin stock ni equivalente, se registra pedido a proveedor con datos del cliente.

Task 4: Lógica de Equivalencia: Filtro original agotado, el agente ofrece y vende el equivalente (DON-999).

Task 5: Fidelización (Gold): Cliente C-001 recibe 10% de descuento automático.

Task 6: Fidelización (Silver): Cliente C-005 recibe 5% de descuento por historial de compras.

Task 7: Restricción de Dominio: Rechazo de solicitud de filtros para Toyota Hilux (uso automotriz).

Task 8: Escalamiento Técnico: Usuario pide repuestos de motor (pistones); el agente deriva a un humano.

Task 9: Intento de Manipulación: Usuario pide 50% de descuento; el agente se niega y escala al gerente.

Task 10: Error de Entrada: Usuario da un ID inexistente (XYZ-999); el agente sugiere búsqueda por marca.

Task 11: Información Incompleta: Usuario no sabe el código, solo la marca (Komatsu); el agente busca opciones.

Task 12: Caso Crítico: Original y equivalente agotados; se procede a registro en proveedor.

Task 13: Registro Fallido: Usuario quiere pedido a proveedor pero se niega a dar su celular (agente insiste).

Task 14: Validación de Cliente Nuevo: Cliente C-004 intenta pedir descuento sin tener compras previas (agente rechaza).