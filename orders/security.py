import hashlib
import hmac
import json

from django.conf import settings


def transaction_payload(order, payment_reference):
    items = [
        {
            "product_name": item.product_name,
            "price": str(item.price),
            "quantity": item.quantity,
        }
        for item in order.items.order_by("id")
    ]
    return {
        "order_number": order.order_number,
        "user_id": order.user_id,
        "total_amount": str(order.total_amount),
        "payment_reference": payment_reference,
        "items": items,
    }


def canonical_transaction_data(order, payment_reference):
    return json.dumps(
        transaction_payload(order, payment_reference),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def transaction_hash(order, payment_reference):
    return hashlib.sha256(
        canonical_transaction_data(order, payment_reference)
    ).hexdigest()


def transaction_signature(order, payment_reference):
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        canonical_transaction_data(order, payment_reference),
        hashlib.sha256,
    ).hexdigest()


def verify_transaction_signature(order):
    if not order.payment_reference or not order.transaction_signature:
        return False
    expected_hash = transaction_hash(order, order.payment_reference)
    expected_signature = transaction_signature(order, order.payment_reference)
    return hmac.compare_digest(order.transaction_hash or "", expected_hash) and hmac.compare_digest(
        order.transaction_signature, expected_signature
    )