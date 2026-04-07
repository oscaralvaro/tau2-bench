import datetime
from copy import deepcopy
from typing import Any, List, Optional

from tau2.domains.fishtrader_garbich.data_model import (
    Address,
    Claim,
    CompanyCustomer,
    ContactPerson,
    FishProduct,
    FishTraderDB,
    Incoterm,
    InventoryItem,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    Order,
    OrderLineItem,
    OrderStatus,
    PaymentMethodType,
    PaymentRecord,
    ProductStatus,
)
from tau2.environment.toolkit import ToolKitBase, ToolType, is_tool


class FishTraderTools(ToolKitBase):
    """Tools for the fish trader domain."""

    CURRENT_TIME = datetime.datetime(2026, 3, 29, 12, 0, 0)
    db: FishTraderDB

    def __init__(self, db: FishTraderDB) -> None:
        super().__init__(db)

    def _now(self) -> datetime.datetime:
        return self.CURRENT_TIME

    def _get_customer(self, customer_id: str) -> CompanyCustomer:
        if customer_id not in self.db.users:
            raise ValueError(f"Customer '{customer_id}' not found")
        return self.db.users[customer_id]

    def _get_product(self, product_id: str) -> FishProduct:
        if product_id not in self.db.products:
            raise ValueError(f"Product '{product_id}' not found")
        return self.db.products[product_id]

    def _get_order(self, order_id: str) -> Order:
        if order_id not in self.db.orders:
            raise ValueError(f"Order '{order_id}' not found")
        return self.db.orders[order_id]

    def _get_invoice(self, invoice_id: str) -> Invoice:
        if invoice_id not in self.db.invoices:
            raise ValueError(f"Invoice '{invoice_id}' not found")
        return self.db.invoices[invoice_id]

    def _get_inventory_records(self, product_id: str) -> list[InventoryItem]:
        return [
            inventory
            for inventory in self.db.inventory.values()
            if inventory.product_id == product_id
        ]

    def _generate_id(self, prefix: str, size: int) -> str:
        return f"{prefix}-{size + 1:03d}"

    def _parse_address(self, address: Address | dict) -> Address:
        if isinstance(address, dict):
            return Address(**address)
        return address

    def _parse_contacts(
        self, contact_persons: Optional[List[ContactPerson | dict]]
    ) -> list[ContactPerson]:
        if not contact_persons:
            return []
        return [
            ContactPerson(**contact) if isinstance(contact, dict) else contact
            for contact in contact_persons
        ]

    def _parse_order_items(
        self, items: List[OrderLineItem | dict]
    ) -> list[OrderLineItem]:
        parsed_items = []
        for item in items:
            parsed_items.append(OrderLineItem(**item) if isinstance(item, dict) else item)
        return parsed_items

    def _next_order_line_id(self, offset: int = 0) -> str:
        line_count = sum(len(order.items) for order in self.db.orders.values())
        return self._generate_id("LINE", line_count + offset)

    def _find_existing_order_line(
        self, order: Order, item_data: dict[str, Any]
    ) -> Optional[OrderLineItem]:
        line_id = item_data.get("line_id")
        if line_id is not None:
            for line in order.items:
                if line.line_id == line_id:
                    return line

        product_id = item_data.get("product_id")
        if product_id is None:
            return None

        matches = [line for line in order.items if line.product_id == product_id]
        if len(matches) == 1:
            return matches[0]
        return None

    def _is_full_order_item_payload(self, item: OrderLineItem | dict[str, Any]) -> bool:
        if isinstance(item, OrderLineItem):
            return True
        required_fields = {
            "line_id",
            "product_id",
            "product_name",
            "quantity",
            "unit_of_measure",
            "unit_price",
            "subtotal",
            "supplier_id",
        }
        return required_fields.issubset(item.keys())

    def _normalize_order_item(
        self,
        item: OrderLineItem | dict[str, Any],
        existing_line: Optional[OrderLineItem] = None,
        line_id_fallback: Optional[str] = None,
    ) -> OrderLineItem:
        item_data = item.model_dump() if isinstance(item, OrderLineItem) else dict(item)

        product_id = item_data.get("product_id")
        if product_id is None and existing_line is not None:
            product_id = existing_line.product_id
        if product_id is None:
            raise ValueError("Order item product_id is required")

        product = self._get_product(product_id)
        quantity = item_data.get("quantity")
        if quantity is None and existing_line is not None:
            quantity = existing_line.quantity
        if quantity is None:
            raise ValueError("Order item quantity is required")

        unit_price = item_data.get("unit_price")
        if unit_price is None and existing_line is not None:
            unit_price = existing_line.unit_price
        if unit_price is None:
            raise ValueError("Order item unit_price is required")

        line_id = (
            item_data.get("line_id")
            or (existing_line.line_id if existing_line is not None else None)
            or line_id_fallback
            or self._next_order_line_id()
        )
        product_name = item_data.get("product_name") or (
            existing_line.product_name if existing_line is not None else product.name
        )
        unit_of_measure = item_data.get("unit_of_measure") or (
            existing_line.unit_of_measure
            if existing_line is not None
            else product.unit_of_measure
        )
        supplier_id = item_data.get("supplier_id") or (
            existing_line.supplier_id if existing_line is not None else product.supplier_id
        )

        return OrderLineItem(
            line_id=line_id,
            product_id=product.product_id,
            product_name=product_name,
            quantity=quantity,
            unit_of_measure=unit_of_measure,
            unit_price=round(float(unit_price), 2),
            subtotal=round(float(quantity) * float(unit_price), 2),
            supplier_id=supplier_id,
        )

    def _validate_customer_can_order(self, customer: CompanyCustomer) -> None:
        if customer.status != "active":
            raise ValueError(
                f"Customer '{customer.customer_id}' is not allowed to place orders"
            )

    def _check_stock_available(self, product_id: str, quantity: float) -> None:
        records = self._get_inventory_records(product_id)
        total_available = sum(record.quantity_available for record in records)
        if total_available < quantity:
            raise ValueError(
                f"Insufficient stock for product '{product_id}'. Available: {total_available}, requested: {quantity}"
            )

    def _reserve_stock(self, product_id: str, quantity: float) -> None:
        self._check_stock_available(product_id, quantity)
        remaining = quantity
        for inventory in self._get_inventory_records(product_id):
            if remaining <= 0:
                break
            usable = min(inventory.quantity_available, remaining)
            inventory.quantity_available = round(inventory.quantity_available - usable, 2)
            inventory.quantity_reserved = round(inventory.quantity_reserved + usable, 2)
            inventory.last_updated_at = self._now()
            remaining = round(remaining - usable, 2)

    def _release_stock(self, product_id: str, quantity: float) -> None:
        remaining = quantity
        for inventory in self._get_inventory_records(product_id):
            if remaining <= 0:
                break
            releasable = min(inventory.quantity_reserved, remaining)
            inventory.quantity_reserved = round(inventory.quantity_reserved - releasable, 2)
            inventory.quantity_available = round(
                inventory.quantity_available + releasable, 2
            )
            inventory.last_updated_at = self._now()
            remaining = round(remaining - releasable, 2)
        if remaining > 0:
            raise ValueError(
                f"Unable to release reserved stock for product '{product_id}'"
            )

    def _release_order_stock(self, order: Order) -> None:
        for item in order.items:
            self._release_stock(item.product_id, item.quantity)

    def _build_order_items(
        self,
        items: List[OrderLineItem | dict],
        existing_order: Optional[Order] = None,
    ) -> list[OrderLineItem]:
        if existing_order is not None and not all(
            self._is_full_order_item_payload(item) for item in items
        ):
            normalized_items = [line.model_copy(deep=True) for line in existing_order.items]
            new_line_offset = 0
            for item in items:
                item_data = item.model_dump() if isinstance(item, OrderLineItem) else dict(item)
                existing_line = self._find_existing_order_line(existing_order, item_data)
                line_id_fallback = None
                if existing_line is None and "line_id" not in item_data:
                    line_id_fallback = self._next_order_line_id(new_line_offset)
                    new_line_offset += 1
                normalized_item = self._normalize_order_item(
                    item,
                    existing_line=existing_line,
                    line_id_fallback=line_id_fallback,
                )
                if existing_line is None:
                    normalized_items.append(normalized_item)
                    continue
                for idx, current_line in enumerate(normalized_items):
                    if current_line.line_id == existing_line.line_id:
                        normalized_items[idx] = normalized_item
                        break
        else:
            normalized_items = []
            next_line_offset = 0
            for item in items:
                item_data = item.model_dump() if isinstance(item, OrderLineItem) else dict(item)
                line_id_fallback = None
                if "line_id" not in item_data:
                    line_id_fallback = self._next_order_line_id(next_line_offset)
                    next_line_offset += 1
                existing_line = (
                    self._find_existing_order_line(existing_order, item_data)
                    if existing_order is not None
                    else None
                )
                normalized_items.append(
                    self._normalize_order_item(
                        item,
                        existing_line=existing_line,
                        line_id_fallback=line_id_fallback,
                    )
                )

        validated_items = []
        for item in normalized_items:
            product = self._get_product(item.product_id)
            if product.status != ProductStatus.ACTIVE:
                raise ValueError(f"Product '{product.product_id}' is not active")
            if item.quantity <= 0:
                raise ValueError("Order item quantity must be greater than zero")
            if item.unit_price < product.max_negotiable_price:
                raise ValueError(
                    f"Price for product '{product.product_id}' is below the maximum negotiable threshold"
                )
            self._check_stock_available(product.product_id, item.quantity)
            validated_items.append(
                OrderLineItem(
                    line_id=item.line_id,
                    product_id=product.product_id,
                    product_name=product.name,
                    quantity=item.quantity,
                    unit_of_measure=item.unit_of_measure or product.unit_of_measure,
                    unit_price=round(item.unit_price, 2),
                    subtotal=round(item.quantity * item.unit_price, 2),
                    supplier_id=product.supplier_id,
                )
            )
        return validated_items

    @is_tool(ToolType.WRITE)
    def register_customer(
        self,
        legal_name: str,
        ruc: str,
        address: Address | dict,
        incoterm: str,
        payment_method: str,
        payment_terms_days: int,
        shipping_lead_time_days: int,
        default_currency: str,
        shipping_address: Optional[Address | dict] = None,
        contact_persons: Optional[List[ContactPerson | dict]] = None,
        trade_name: Optional[str] = None,
        preferred_destination_port: Optional[str] = None,
        credit_limit: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> CompanyCustomer:
        """
        Register a new business customer.
        """
        if any(customer.ruc == ruc for customer in self.db.users.values()):
            raise ValueError(f"A customer with RUC '{ruc}' already exists")

        customer_id = self._generate_id("CUST", len(self.db.users))
        customer = CompanyCustomer(
            customer_id=customer_id,
            legal_name=legal_name,
            trade_name=trade_name,
            ruc=ruc,
            address=self._parse_address(address),
            shipping_address=(
                self._parse_address(shipping_address) if shipping_address else None
            ),
            incoterm=Incoterm(incoterm),
            payment_method=PaymentMethodType(payment_method),
            payment_terms_days=payment_terms_days,
            shipping_lead_time_days=shipping_lead_time_days,
            default_currency=default_currency,
            contact_persons=self._parse_contacts(contact_persons),
            preferred_destination_port=preferred_destination_port,
            credit_limit=credit_limit,
            notes=notes,
        )
        self.db.users[customer_id] = customer
        return customer

    @is_tool(ToolType.READ)
    def show_catalog(self) -> list[FishProduct]:
        """
        Show the active commercial catalog.
        """
        return [
            product
            for product in self.db.products.values()
            if product.status == ProductStatus.ACTIVE
        ]

    @is_tool(ToolType.READ)
    def get_customer_details(self, customer_id: str) -> CompanyCustomer:
        """
        Get the commercial profile of a customer company.
        """
        return self._get_customer(customer_id)

    @is_tool(ToolType.READ)
    def get_invoice_details(self, invoice_id: str) -> Invoice:
        """
        Get the financial details and status of an invoice.
        """
        return self._get_invoice(invoice_id)

    @is_tool(ToolType.READ)
    def check_stock(self, product_id: str) -> dict:
        """
        Get stock information for a product.
        """
        product = self._get_product(product_id)
        inventory_records = self._get_inventory_records(product_id)
        total_available = round(
            sum(record.quantity_available for record in inventory_records), 2
        )
        total_reserved = round(
            sum(record.quantity_reserved for record in inventory_records), 2
        )
        return {
            "product": product,
            "inventory_records": inventory_records,
            "total_available": total_available,
            "total_reserved": total_reserved,
        }

    @is_tool(ToolType.WRITE)
    def register_order(
        self,
        customer_id: str,
        items: List[OrderLineItem | dict],
        delivery_date: str,
        shipping_address: Optional[Address | dict] = None,
        incoterm: Optional[str] = None,
        payment_method: Optional[str] = None,
        currency: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Order:
        """
        Register a new sales order and reserve stock.
        """
        customer = self._get_customer(customer_id)
        self._validate_customer_can_order(customer)
        snapshot = deepcopy(self.db)
        try:
            normalized_items = self._build_order_items(items)
            for item in normalized_items:
                self._reserve_stock(item.product_id, item.quantity)
            order_id = self._generate_id("ORD", len(self.db.orders))
            order = Order(
                order_id=order_id,
                customer_id=customer_id,
                issue_date=self._now().date(),
                delivery_date=datetime.date.fromisoformat(delivery_date),
                incoterm=Incoterm(incoterm) if incoterm else customer.incoterm,
                payment_method=(
                    PaymentMethodType(payment_method)
                    if payment_method
                    else customer.payment_method
                ),
                currency=currency or customer.default_currency,
                shipping_address=(
                    self._parse_address(shipping_address)
                    if shipping_address
                    else customer.shipping_address or customer.address
                ),
                items=normalized_items,
                total_amount=round(sum(item.subtotal for item in normalized_items), 2),
                status=OrderStatus.CONFIRMED,
                notes=notes,
            )
            self.db.orders[order_id] = order
            customer.order_ids.append(order_id)
            return order
        except Exception:
            self.db = snapshot
            raise

    @is_tool(ToolType.WRITE)
    def modify_order(
        self,
        order_id: str,
        items: Optional[List[OrderLineItem | dict]] = None,
        delivery_date: Optional[str] = None,
        shipping_address: Optional[Address | dict] = None,
        incoterm: Optional[str] = None,
        payment_method: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Order:
        """
        Modify a confirmed order before shipment.
        """
        order = self._get_order(order_id)
        if order.status in {OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.CANCELLED}:
            raise ValueError("This order can no longer be modified")

        snapshot = deepcopy(self.db)
        try:
            if items is not None:
                self._release_order_stock(order)
                normalized_items = self._build_order_items(
                    items,
                    existing_order=order,
                )
                for item in normalized_items:
                    self._reserve_stock(item.product_id, item.quantity)
                order.items = normalized_items
                order.total_amount = round(
                    sum(item.subtotal for item in normalized_items), 2
                )
            if delivery_date is not None:
                order.delivery_date = datetime.date.fromisoformat(delivery_date)
            if shipping_address is not None:
                order.shipping_address = self._parse_address(shipping_address)
            if incoterm is not None:
                order.incoterm = Incoterm(incoterm)
            if payment_method is not None:
                order.payment_method = PaymentMethodType(payment_method)
            if notes is not None:
                order.notes = notes
            return order
        except Exception:
            self.db = snapshot
            raise

    @is_tool(ToolType.WRITE)
    def cancel_order(self, order_id: str, reason: str) -> Order:
        """
        Cancel an order and release reserved stock.
        """
        order = self._get_order(order_id)
        if order.status in {OrderStatus.SHIPPED, OrderStatus.DELIVERED}:
            raise ValueError("Shipped or delivered orders cannot be cancelled")
        if order.status == OrderStatus.CANCELLED:
            raise ValueError("Order is already cancelled")
        self._release_order_stock(order)
        order.status = OrderStatus.CANCELLED
        order.notes = reason if order.notes is None else f"{order.notes}\n{reason}"
        return order

    @is_tool(ToolType.READ)
    def get_order_status(self, order_id: str) -> dict:
        """
        Get the commercial and logistics status of an order.
        """
        order = self._get_order(order_id)
        shipments = [
            self.db.shipments[shipment_id]
            for shipment_id in order.shipment_ids
            if shipment_id in self.db.shipments
        ]
        invoices = [
            self.db.invoices[invoice_id]
            for invoice_id in order.invoice_ids
            if invoice_id in self.db.invoices
        ]
        return {
            "order": order,
            "shipments": shipments,
            "invoices": invoices,
            "shipment_statuses": [shipment.status for shipment in shipments],
            "invoice_statuses": [invoice.status for invoice in invoices],
        }

    @is_tool(ToolType.WRITE)
    def register_claim(
        self,
        customer_id: str,
        subject: str,
        description: str,
        order_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
    ) -> Claim:
        """
        Register a claim related to an order, invoice, or general service issue.
        """
        self._get_customer(customer_id)
        if order_id is not None:
            self._get_order(order_id)
        if invoice_id is not None:
            self._get_invoice(invoice_id)

        claim_id = self._generate_id("CLM", len(self.db.claims))
        claim = Claim(
            claim_id=claim_id,
            customer_id=customer_id,
            order_id=order_id,
            invoice_id=invoice_id,
            subject=subject,
            description=description,
            created_at=self._now(),
        )
        self.db.claims[claim_id] = claim
        return claim

    @is_tool(ToolType.WRITE)
    def issue_invoice(self, order_id: str, tax_rate: float = 0.18) -> Invoice:
        """
        Issue an invoice for an order.
        """
        order = self._get_order(order_id)
        if order.status == OrderStatus.CANCELLED:
            raise ValueError("Cancelled orders cannot be invoiced")
        if order.invoice_ids:
            raise ValueError("This order already has an invoice")

        customer = self._get_customer(order.customer_id)
        subtotal = round(sum(item.subtotal for item in order.items), 2)
        tax_amount = round(subtotal * tax_rate, 2)
        total_amount = round(subtotal + tax_amount, 2)
        invoice_id = self._generate_id("INV", len(self.db.invoices))
        issue_date = self._now().date()
        due_date = issue_date + datetime.timedelta(days=customer.payment_terms_days)
        line_items = [
            InvoiceLineItem(
                line_id=f"INVLINE-{index + 1:03d}",
                product_id=item.product_id,
                description=item.product_name,
                quantity=item.quantity,
                unit_of_measure=item.unit_of_measure,
                unit_price=item.unit_price,
                subtotal=item.subtotal,
            )
            for index, item in enumerate(order.items)
        ]
        invoice = Invoice(
            invoice_id=invoice_id,
            invoice_number=f"F001-{len(self.db.invoices) + 1:06d}",
            order_id=order_id,
            customer_id=customer.customer_id,
            customer_legal_name=customer.legal_name,
            customer_ruc=customer.ruc,
            billing_address=customer.address,
            issue_date=issue_date,
            due_date=due_date,
            currency=order.currency,
            payment_method=order.payment_method,
            payment_terms_days=customer.payment_terms_days,
            line_items=line_items,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            paid_amount=0.0,
            status=InvoiceStatus.ISSUED,
            issued_at=self._now(),
        )
        self.db.invoices[invoice_id] = invoice
        order.invoice_ids.append(invoice_id)
        customer.invoice_ids.append(invoice_id)
        return invoice

    @is_tool(ToolType.WRITE)
    def make_payment(
        self,
        invoice_id: str,
        amount: float,
        payment_method: str,
        reference: Optional[str] = None,
    ) -> Invoice:
        """
        Register a payment against an invoice.
        """
        invoice = self._get_invoice(invoice_id)
        if invoice.status == InvoiceStatus.CANCELLED:
            raise ValueError("Cancelled invoices cannot receive payments")
        if invoice.status == InvoiceStatus.PAID:
            raise ValueError("This invoice is already fully paid")
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")

        outstanding = round(invoice.total_amount - invoice.paid_amount, 2)
        if amount > outstanding:
            raise ValueError(
                f"Payment exceeds outstanding amount. Outstanding: {outstanding}"
            )

        payment_id = self._generate_id("PAY", len(invoice.payment_records))
        payment = PaymentRecord(
            payment_id=payment_id,
            invoice_id=invoice_id,
            amount=round(amount, 2),
            payment_method=PaymentMethodType(payment_method),
            payment_date=self._now(),
            reference=reference,
        )
        invoice.payment_records.append(payment)
        invoice.paid_amount = round(invoice.paid_amount + amount, 2)
        if invoice.paid_amount == invoice.total_amount:
            invoice.status = InvoiceStatus.PAID
            invoice.paid_at = self._now()
        else:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
        return invoice
