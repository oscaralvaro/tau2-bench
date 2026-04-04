# FishTrader Domain

Author: Joaquin Matias Garbich Rabinovich

## Domain Summary

The `fishtrader_garbich` domain simulates a B2B customer service agent for a seafood trading company. The agent supports commercial and operational workflows for business customers, including customer onboarding, catalog consultation, stock checks, order creation and modification, order cancellation, invoice issuance, payment registration, and claims intake.

This is not a retail domain. Customers are companies with commercial profiles, negotiated terms, shipping preferences, and invoice/order histories. The domain is designed to test whether an agent can follow realistic commercial rules while interacting safely with inventory, order, and billing data.

## High-Level Scope

The domain evaluates whether an agent can:

- handle read-only requests such as catalog, stock, customer, invoice, and order status queries
- perform write actions only after explicit user confirmation
- apply commercial constraints such as customer status, stock availability, minimum acceptable price, invoice uniqueness, and payment balance limits
- refuse or escalate requests that violate policy

## Core Entities

### Customer

A customer is a company account with legal/trade name, RUC, billing/shipping addresses, incoterm, payment terms, default currency, contacts, destination port, credit limit, status, notes, and related order/invoice IDs.

Customer status directly affects commercial actions:

- `active`: may place new orders
- `credit_hold`: not allowed to place new credit-based orders
- `inactive`: not allowed to place new orders

### Supplier

A supplier stores legal/tax identity, address, contacts, country of origin, payment method, lead time, and status. Supplier data is internal support information and should not be exposed beyond what is needed for valid tool-driven actions.

### Product

A fish product includes product ID, name, description, species, presentation, unit, selling price, maximum negotiable price threshold, currency, supplier, origin country, and status.

The agent must not register or modify an order line below the product's `max_negotiable_price`.

### Inventory

Inventory records track available and reserved quantity per product, location, unit, timestamp, and inventory status. Only available stock can be committed to new orders.

### Order

Orders include customer, issue date, delivery date, incoterm, payment method, shipping address, line items, total amount, order status, notes, shipment IDs, and invoice IDs.

Important statuses:

- `confirmed`
- `shipped`
- `delivered`
- `cancelled`

### Shipment

Shipments include carrier, container/tracking information, ports, ETA/ATA dates, incoterm, status, and notes.

### Invoice

Invoices include invoice/order/customer linkage, billing data, line items, tax, total amount, paid amount, payment records, due date, and status.

Important statuses:

- `issued`
- `partially_paid`
- `paid`
- `cancelled`

### Claim

Claims capture customer complaints or incidents tied to an order, invoice, or general service issue, with subject, description, timestamp, and claim status.

## Tools

### Read Tools

- `show_catalog()`: returns active commercial products only
- `get_customer_details(customer_id)`: returns the business profile of a customer
- `get_invoice_details(invoice_id)`: returns invoice details and payment status
- `check_stock(product_id)`: returns product info, inventory records, total available, and total reserved stock
- `get_order_status(order_id)`: returns order, related shipments, related invoices, and summarized shipment/invoice statuses

### Write Tools

- `register_customer(...)`: creates a new business customer if the RUC is not duplicated
- `register_order(...)`: creates an order for an eligible customer and reserves stock
- `modify_order(...)`: updates an existing order before shipment
- `cancel_order(order_id, reason)`: cancels an eligible order and releases reserved stock
- `issue_invoice(order_id, tax_rate=0.18)`: issues one invoice for an eligible order
- `make_payment(invoice_id, amount, payment_method, reference=None)`: records a payment against an invoice
- `register_claim(...)`: logs a customer claim

## Policy Summary

The full policy is in [policy.md](/Users/joaquingarbich/tau2-bench/data/tau2/domains/fishtrader_garbich/policy.md). Key rules:

- The agent serves only business customers, not retail consumers.
- The agent must not invent procedures, promises, or data that are not supported by tools, the DB, or the policy.
- The agent must make only one tool call at a time.
- Any write action requires an explicit confirmation after summarizing the intended action.
- Write actions requiring confirmation:
  - customer registration
  - order registration
  - order modification
  - order cancellation
  - invoice issuance
  - payment registration
  - claim registration
- Orders are allowed only for eligible customers and valid products with sufficient stock.
- Prices below the product's minimum acceptable threshold must be rejected.
- Cancelled, shipped, or delivered orders cannot be handled the same way:
  - shipped/delivered orders cannot be cancelled by the agent
  - already cancelled orders cannot be cancelled again
- Duplicate invoices for the same order are not allowed.
- Payments must be positive and cannot exceed the outstanding balance.
- Claims can be logged, but the agent must not promise compensation unless the tools/policy support it.
- If a case cannot be safely handled through the available tools and policy, the agent should transfer or clearly indicate human review is required.

## Task Coverage

The domain currently includes 15 tasks total:

- `base`: 15 tasks
- `train`: 10 tasks
- `test`: 5 tasks

Representative scenarios:

- `fishtrader_01_register_customer`: successful registration of a new business customer
- `fishtrader_03_check_stock_out_of_stock`: stock check where the requested product is unavailable
- `fishtrader_04_register_order_success`: successful order registration with stock reservation
- `fishtrader_05_modify_order_success`: valid order modification before shipment
- `fishtrader_07_cancel_order_too_old_denied`: refusal to cancel an order older than the allowed window
- `fishtrader_08_cancel_shipped_order_denied`: refusal to cancel an already shipped order
- `fishtrader_10_issue_invoice_success`: valid invoice issuance for an order without an existing invoice
- `fishtrader_11_issue_duplicate_invoice_denied`: refusal to issue a duplicate invoice
- `fishtrader_12_make_payment_success`: successful payment registration
- `fishtrader_13_overpayment_denied`: refusal to overpay an invoice
- `fishtrader_14_register_claim_success`: successful claim registration tied to a commercial/logistics issue
- `fishtrader_15_inactive_customer_order_denied`: refusal to place an order for an inactive customer

As in the other tau2 domains, tasks combine expected tool behavior, resulting environment state, and natural-language behavioral assertions.

## Suggested PR Notes

For the PR description, include at least:

- your full name: Joaquin Matias Garbich Rabinovich
- a short domain summary
- key entities
- tool inventory
- policy highlights
- number of tasks and the train/test/base split

## Execution Evidence

Before submitting or updating the PR, add evidence that the domain was executed at least once with a valid API key.

Suggested command:

```bash
source .venv/bin/activate
tau2 run \
  --domain fishtrader_garbich \
  --agent-llm gemini/gemma-3-27b-it \
  --user-llm gemini/gemma-3-27b-it \
  --num-tasks 1 \
  --max-concurrency 1
```

Then attach one screenshot that shows:

- the number of executed tasks
- the resulting metrics summary

You can use either the summary printed at the end of `tau2 run` or the output of `tau2 view`.

## Notes

- The project reads `GOOGLE_API_KEY` from the repo-level `.env`.
- If using a free Gemini tier, `--max-concurrency 1` is recommended to avoid rate limit issues.
