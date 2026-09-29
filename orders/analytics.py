def purchase_event_payload(order):
    """Builds the one-time flash event fired right after an order is created
    (see core.context_processors.pending_ecommerce_event). This is rendered
    exactly once, on the "payment authorized" page immediately after
    checkout -- not on the reusable orders:success page, which the buyer can
    revisit any number of times and would otherwise double-count the
    conversion."""
    items = list(order.items.select_related("product"))
    return {
        "event": "purchase",
        "fb_event": "Purchase",
        "transaction_id": order.order_number,
        "currency": "NPR",
        "value": float(order.total_amount),
        "items": [
            {
                "item_id": item.product.sku,
                "item_name": item.product_name,
                "price": float(item.price),
                "quantity": item.quantity,
            }
            for item in items
        ],
    }
