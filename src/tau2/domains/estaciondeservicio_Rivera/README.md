# Estacion de Servicio Rivera Domain

**Author:** Diego Eduardo Rivera Rodriguez

## Domain Summary

The `estaciondeservicio_Rivera` domain simulates a customer service agent for a fuel station that serves corporate delivery orders in Sullana, Piura. The agent helps customers register their company, explore the catalog, check stock, create and manage orders, register payments, submit complaints, and request virtual invoices.

The domain is centered on realistic operational constraints for fuel delivery:

- fuel orders require a minimum of 250 gallons
- orders must be scheduled in advance
- cancellations and rescheduling are restricted by time windows
- lubricants can only be requested with an eligible fuel order
- each order uses one payment method and is paid in a single transaction

## Main Entities

- `Item`: Product catalog entry with product name, product type, unit of measure, unit price, and available stock.
- `Customer`: Registered company customer with contact data, RUC, billing email, fiscal address, and authorized delivery addresses.
- `Order`: Delivery order linked to a customer and an item, with quantity, delivery scheduling, payment method, invoice data, and operational status.
- `PaymentMethod`: Registered payment method. Supported types are `credit`, `bank_transfer`, and `cash`.
- `Payment`: Recorded payment for an order.
- `Claim`: Complaint registered by a customer, optionally linked to an order.
- `VirtualInvoice`: Invoice delivery data associated with an order.
- `FuelStationDB`: Domain database containing customers, items, payment methods, payments, claims, and orders.

## Tools

### Read Tools

- `get_client_details`: Returns full customer details.
- `get_order_details`: Returns full order details.
- `search_client_by_ruc`: Finds a customer by RUC.
- `get_orders_by_client`: Lists all orders of a customer.
- `show_catalog`: Returns the full product catalog.
- `search_items_by_name_or_type`: Searches products by name or product type.
- `consult_stock`: Returns stock information for a specific item.
- `list_available_payment_methods`: Lists registered payment methods.
- `get_payment_method_details`: Returns details of a specific payment method.
- `get_order_status`: Returns an operational summary of an order.
- `get_payment_status`: Returns payment summary for an order.
- `get_claim_details`: Returns details of a complaint.
- `get_claims_by_client`: Lists complaints registered by a customer.

### Write Tools

- `register_client`: Registers a new corporate customer.
- `update_client`: Updates customer information.
- `add_delivery_address_to_client`: Adds an authorized delivery address.
- `remove_delivery_address_from_client`: Removes an authorized delivery address.
- `register_payment_method`: Registers a payment method.
- `update_order_payment_method`: Changes the selected payment method before payment.
- `register_order`: Creates a new order.
- `update_order`: Updates a pending unpaid order.
- `reschedule_order`: Reschedules a pending order within allowed time limits.
- `cancel_order`: Cancels a pending order and restores reserved stock.
- `register_claim`: Registers a complaint.
- `update_claim_status`: Updates complaint status.
- `emit_virtual_invoice`: Issues or updates the virtual invoice for an order.
- `mark_order_delivered`: Marks a pending order as delivered with proof.
- `make_payment`: Registers the single full payment of an order.

### Generic Tool

- `transfer_to_human_agents`: Escalates the case when the request is out of scope or when the user asks for a human advisor.

## Policy Summary

The full policy is defined in [policy.md](/c:/Users/diego/tau2-bench/data/tau2/domains/estaciondeservicio_Rivera/policy.md). The key business rules are:

- Unknown customers must be registered before placing any order.
- The agent must handle only one customer per conversation.
- Any write action requires a clear summary and explicit user confirmation.
- Only `pending` orders can be modified, rescheduled, cancelled, or marked as delivered.
- If an order already has payments, its contents cannot be modified.
- Fuel products must use `galones` and require at least 250 gallons.
- Lubricants are normalized to `unidad`.
- Partial deliveries are not allowed.
- Orders must be scheduled at least 24 hours in advance.
- Cancellations are allowed only up to 12 hours before scheduled delivery.
- Rescheduling is allowed only up to 12 hours before scheduled delivery, and the new time must also keep at least 12 hours of notice.
- Lubricants may only be requested with an associated fuel order of at least 250 gallons.
- If the delivery address is not registered, it must be added before creating the order.
- Each order uses a single payment method.
- The selected payment method may be changed only before any payment is registered.
- Each order must be paid in a single full transaction.
- Delivery has no additional charge.
- A proof of delivery is required to mark an order as delivered.
- Requests outside tool scope must be transferred to a human agent.

## Tasks

The task set currently contains 20 tasks covering successful flows, policy rejections, state changes, incomplete-information cases, and human handoff scenarios.

Representative examples:

- `0`: Customer requests the catalog and stock information.
- `1`: Register a new customer, register a payment method, and create a valid fuel order.
- `4`: Register a lubricant order linked to a valid fuel order.
- `5`: Cancel a pending order within the allowed time window.
- `6`: Change the payment method before payment and then complete the full payment.
- `7`: Reject a fuel order below the 250-gallon minimum.
- `8`: Reject a partial payment attempt.
- `10`: Transfer the conversation to a human agent for an exception request.
- `14`: Check stock for a specific item.
- `17`: Issue a virtual invoice.
- `18`: Register a complaint.
- `19`: Reject payment using a different method from the one selected on the order.

## File Structure

Relevant files for this domain:

- [data_model.py](/c:/Users/diego/tau2-bench/src/tau2/domains/estaciondeservicio_Rivera/data_model.py)
- [tools.py](/c:/Users/diego/tau2-bench/src/tau2/domains/estaciondeservicio_Rivera/tools.py)
- [environment.py](/c:/Users/diego/tau2-bench/src/tau2/domains/estaciondeservicio_Rivera/environment.py)
- [utils.py](/c:/Users/diego/tau2-bench/src/tau2/domains/estaciondeservicio_Rivera/utils.py)
- [policy.md](/c:/Users/diego/tau2-bench/data/tau2/domains/estaciondeservicio_Rivera/policy.md)
- [db.json](/c:/Users/diego/tau2-bench/data/tau2/domains/estaciondeservicio_Rivera/db.json)
- [tasks.json](/c:/Users/diego/tau2-bench/data/tau2/domains/estaciondeservicio_Rivera/tasks.json)
- [split_tasks.json](/c:/Users/diego/tau2-bench/data/tau2/domains/estaciondeservicio_Rivera/split_tasks.json)

## Notes

- The catalog includes fuels, lubricants, additives, filters, and related products.
- Lubricants are normalized to `unidad`, while fuel products are normalized to `galones`.
