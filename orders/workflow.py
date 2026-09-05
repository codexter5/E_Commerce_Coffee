from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from accounts.models import Profile
from notifications.models import Notification
from notifications.services import (
    send_order_confirmation_notification,
    send_seller_new_order_notification,
    send_status_update_to_recipient,
)


TRANSITIONS = {
    "PLACED": {"ACCEPTED": "SELLER", "CANCELLED": "SELLER"},
    "ACCEPTED": {"PREPARING": "SELLER", "CANCELLED": "SELLER"},
    "PREPARING": {"READY_FOR_DELIVERY": "SELLER", "CANCELLED": "SELLER"},
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
    "CANCELLED": (Notification.Type.ORDER_CANCELLED, "Your order was cancelled."),
}

# Every status change always gets an in-app (bell) notification for everyone
# involved with the order. Email/WhatsApp is more precisely targeted so people
# aren't messaged about things they don't need to act on:
#   - the buyer cares about every step of their own order, so they're always included
#   - the seller only needs pinging for events that need their attention or
#     confirm a sale (a new order, a cancellation, a completed sale)
#   - delivery riders (as a pool, not just whoever's assigned) only need
#     pinging when a fresh job becomes available to claim
#   - admins only get externally notified for the one event worth escalating: a cancellation
EXTERNAL_NOTIFY_ON = {
    "ACCEPTED": {"buyer"},
    "PREPARING": {"buyer"},
    "READY_FOR_DELIVERY": {"buyer", "delivery_pool"},
    "ASSIGNED": {"buyer"},
    "PICKED_UP": {"buyer"},
    "OUT_FOR_DELIVERY": {"buyer"},
    "DELIVERED": {"buyer", "seller"},
    "COMPLETED": {"buyer", "seller"},
    "CANCELLED": {"buyer", "seller", "admin"},
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


def _external_recipients_for(order, new_status, actor):
    """Resolve EXTERNAL_NOTIFY_ON's role labels into actual User objects for
    this specific order, excluding whoever just performed the action (no
    point emailing/WhatsApp-ing someone about their own click)."""
    targets = EXTERNAL_NOTIFY_ON.get(new_status, set())
    recipients = []
    if "buyer" in targets and order.user_id and order.user_id != actor.id:
        recipients.append(order.user)
    if "seller" in targets and order.seller_id and order.seller_id != actor.id:
        recipients.append(order.seller)
    if "delivery_pool" in targets:
        recipients.extend(
            User.objects.filter(profile__role=Profile.Role.DELIVERY).exclude(pk=actor.id).select_related("profile")
        )
    if "admin" in targets:
        recipients.extend(
            User.objects.filter(profile__role=Profile.Role.ADMIN).exclude(pk=actor.id).select_related("profile")
        )
    return recipients


def send_status_update_notifications(order, new_status, message, actor):
    """Queue email/WhatsApp for every recipient EXTERNAL_NOTIFY_ON says should
    hear about this status externally (not just via the in-app bell)."""
    for recipient in _external_recipients_for(order, new_status, actor):
        transaction.on_commit(
            lambda recipient=recipient: send_status_update_to_recipient(recipient, order, new_status, message)
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
    send_status_update_notifications(order, new_status, message, actor)
    return order


def notify_order_placed(order):
    """The very first notification of an order's life: fired the moment
    checkout completes ("the product has been checked out"). The buyer gets
    an in-app + email/WhatsApp confirmation; the seller gets an in-app +
    email/WhatsApp alert that a sale is waiting for them."""
    if order.seller:
        _notify(order.seller, order, Notification.Type.ORDER_PLACED, "A new order is waiting for your review.")
    transaction.on_commit(lambda: send_order_confirmation_notification(order))
    if order.seller_id:
        transaction.on_commit(lambda: send_seller_new_order_notification(order))
