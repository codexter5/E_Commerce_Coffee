from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from notifications.models import Notification


TRANSITIONS = {
    "PLACED": {"ACCEPTED": "SELLER"},
    "ACCEPTED": {"PREPARING": "SELLER"},
    "PREPARING": {"READY_FOR_DELIVERY": "SELLER"},
    "READY_FOR_DELIVERY": {"ASSIGNED": "DELIVERY"},
    "ASSIGNED": {"PICKED_UP": "DELIVERY"},
    "PICKED_UP": {"OUT_FOR_DELIVERY": "DELIVERY"},
    "OUT_FOR_DELIVERY": {"DELIVERED": "DELIVERY"},
    "DELIVERED": {"COMPLETED": "BUYER"},
}

NOTIFICATION_DETAILS = {
    "ACCEPTED": (Notification.Type.ORDER_ACCEPTED, "The seller accepted your order."),
    "PREPARING": (Notification.Type.ORDER_PREPARING, "The seller is preparing your order."),
    "READY_FOR_DELIVERY": (Notification.Type.ORDER_READY, "Your order is ready for delivery."),
    "ASSIGNED": (Notification.Type.DELIVERY_ASSIGNED, "A delivery person accepted your order."),
    "PICKED_UP": (Notification.Type.ORDER_PICKED_UP, "Your order has been picked up."),
    "OUT_FOR_DELIVERY": (Notification.Type.ORDER_OUT_FOR_DELIVERY, "Your order is out for delivery."),
    "DELIVERED": (Notification.Type.ORDER_DELIVERED, "Your order was marked delivered."),
    "COMPLETED": (Notification.Type.ORDER_COMPLETED, "The buyer confirmed receipt of the order."),
}


def _role(user):
    return getattr(getattr(user, "profile", None), "role", None)


def _notify(recipient, order, notification_type, message):
    if recipient:
        Notification.objects.create(
            recipient=recipient,
            order=order,
            notification_type=notification_type,
            message=f"Order {order.order_number}: {message}",
        )


@transaction.atomic
def transition_order(order, actor, new_status):
    required_role = TRANSITIONS.get(order.status, {}).get(new_status)
    if not required_role or _role(actor) != required_role:
        raise ValueError("You are not allowed to make that order transition.")
    if required_role == "SELLER" and order.seller_id != actor.id:
        raise ValueError("Only the assigned seller can update this order.")
    if required_role == "BUYER" and order.user_id != actor.id:
        raise ValueError("Only the buyer can confirm this order.")
    if required_role == "DELIVERY" and new_status != "ASSIGNED" and order.delivery_person_id != actor.id:
        raise ValueError("Only the assigned delivery person can update this order.")
    if new_status == "ASSIGNED":
        if order.delivery_person_id and order.delivery_person_id != actor.id:
            raise ValueError("This delivery is already assigned.")
        order.delivery_person = actor
    order.status = new_status
    timestamp_field = {
        "ACCEPTED": "accepted_at", "READY_FOR_DELIVERY": "ready_at",
        "PICKED_UP": "picked_up_at", "OUT_FOR_DELIVERY": "picked_up_at",
        "DELIVERED": "delivered_at", "COMPLETED": "completed_at",
    }.get(new_status)
    update_fields = ["status", "delivery_person"] if new_status == "ASSIGNED" else ["status"]
    if timestamp_field:
        setattr(order, timestamp_field, timezone.now())
        update_fields.append(timestamp_field)
    order.save(update_fields=update_fields)
    notification_type, message = NOTIFICATION_DETAILS[new_status]
    recipients = {order.user_id: order.user}
    if order.seller_id:
        recipients[order.seller_id] = order.seller
    if order.delivery_person_id:
        recipients[order.delivery_person_id] = order.delivery_person
    if new_status == "READY_FOR_DELIVERY":
        delivery_users = Profile.objects.filter(role=Profile.Role.DELIVERY).select_related("user")
        recipients.update({profile.user_id: profile.user for profile in delivery_users})
    recipients.pop(actor.id, None)
    for recipient in recipients.values():
        _notify(recipient, order, notification_type, message)
    return order


def notify_order_placed(order):
    if order.seller:
        _notify(order.seller, order, Notification.Type.ORDER_PLACED, "A new order is waiting for your review.")
