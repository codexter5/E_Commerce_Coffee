from django.conf import settings
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
    "PREPARING": {"READY_FOR_DELIVERY": "SELLER", "ASSIGNED": "SELLER", "CANCELLED": "SELLER"},
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
# involved with the order. Email/WhatsApp is more precisely targeted, but on
# the "give people proof things went right" principle, it now covers the
# whole journey for buyer, seller, and delivery rider -- not just the one
# stage each of them happens to trigger themselves:
#   - the buyer cares about every step of their own order
#   - the seller gets pinged for a new sale and every stage after they've
#     handed it off to delivery, so they can see it through to completion
#   - the specific assigned delivery rider gets the closing "buyer confirmed
#     receipt" message, so they know their part of the job is fully done
#   - the delivery *pool* (everyone with that role, not just whoever's
#     assigned) only gets pinged when a fresh job becomes available to claim
#   - admins: see ADMIN_NOTIFY_ALL_ORDER_EVENTS below -- by default they're
#     added to every stage too. CANCELLED always escalates to admins
#     regardless of that setting, since it's worth knowing about either way.
# On top of all this, whoever actually performed an action (seller accepting,
# rider marking delivered, buyer confirming receipt...) gets their own separate
# confirmation message -- see send_actor_confirmation() below -- so there's a
# written/WhatsApp record that their action actually went through.
EXTERNAL_NOTIFY_ON = {
    "ACCEPTED": {"buyer"},
    "PREPARING": {"buyer"},
    "READY_FOR_DELIVERY": {"buyer", "seller", "delivery_pool"},
    "ASSIGNED": {"buyer", "seller"},
    "PICKED_UP": {"buyer", "seller"},
    "OUT_FOR_DELIVERY": {"buyer", "seller"},
    "DELIVERED": {"buyer", "seller"},
    "COMPLETED": {"buyer", "seller", "delivery_person"},
    "CANCELLED": {"buyer", "seller", "admin"},
}

# Sent back to whoever just performed the action -- a receipt confirming it
# actually went through, distinct from the "FYI" message everyone else gets.
ACTOR_CONFIRMATION_MESSAGES = {
    "ACCEPTED": "You accepted this order.",
    "PREPARING": "You marked this order as being prepared.",
    "READY_FOR_DELIVERY": "You marked this order ready for delivery.",
    "ASSIGNED": "You claimed this delivery.",
    "PICKED_UP": "You marked this order picked up.",
    "OUT_FOR_DELIVERY": "You marked this order out for delivery.",
    "DELIVERED": "You marked this order delivered.",
    "COMPLETED": "You confirmed receipt of this order.",
    "CANCELLED": "You cancelled this order.",
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


def _admin_notify_enabled():
    return getattr(settings, "ADMIN_NOTIFY_ALL_ORDER_EVENTS", True)


def _admin_users(exclude_id=None):
    qs = User.objects.filter(profile__role=Profile.Role.ADMIN).select_related("profile")
    if exclude_id:
        qs = qs.exclude(pk=exclude_id)
    return list(qs)


def _external_recipients_for(order, new_status, actor):
    """Resolve EXTERNAL_NOTIFY_ON's role labels into actual User objects for
    this specific order, excluding whoever just performed the action (they
    get send_actor_confirmation() instead of this "FYI" message)."""
    targets = set(EXTERNAL_NOTIFY_ON.get(new_status, set()))
    if _admin_notify_enabled():
        targets.add("admin")
    recipients = []
    if "buyer" in targets and order.user_id and order.user_id != actor.id:
        recipients.append(order.user)
    if "seller" in targets and order.seller_id and order.seller_id != actor.id:
        recipients.append(order.seller)
    if "delivery_person" in targets and order.delivery_person_id and order.delivery_person_id != actor.id:
        recipients.append(order.delivery_person)
    if "delivery_pool" in targets:
        recipients.extend(
            User.objects.filter(profile__role=Profile.Role.DELIVERY).exclude(pk=actor.id).select_related("profile")
        )
    if "admin" in targets:
        recipients.extend(_admin_users(exclude_id=actor.id))
    return recipients


def send_status_update_notifications(order, new_status, message, actor):
    """Queue email/WhatsApp for every recipient EXTERNAL_NOTIFY_ON (plus the
    admin toggle) says should hear about this status as an FYI."""
    for recipient in _external_recipients_for(order, new_status, actor):
        transaction.on_commit(
            lambda recipient=recipient: send_status_update_to_recipient(recipient, order, new_status, message)
        )


def send_actor_confirmation(order, new_status, actor, message=None):
    """A short receipt-style confirmation sent back to whoever just performed
    the action (seller accepting, rider marking delivered, buyer confirming
    receipt, or an admin override), so they have written/WhatsApp proof the
    update actually went through -- not just a success banner that
    disappears the moment they navigate away. Pass `message` to override the
    default wording (used when a seller directly hands an order to a chosen
    rider, since "You claimed this delivery" would be the wrong phrasing for
    them)."""
    message = message or ACTOR_CONFIRMATION_MESSAGES.get(
        new_status, f"You updated this order to {new_status.replace('_', ' ').title()}."
    )
    transaction.on_commit(
        lambda: send_status_update_to_recipient(actor, order, new_status, message)
    )


@transaction.atomic
def transition_order(order, actor, new_status, assignee=None):
    """Advance an order one step. `assignee` is only meaningful for the
    PREPARING -> ASSIGNED jump: it lets a seller hand the order directly to a
    specific delivery rider of their choosing, instead of the normal
    READY_FOR_DELIVERY -> ASSIGNED path where any rider in the pool claims it
    themselves. Everything else about the state machine is unchanged."""
    required_role = TRANSITIONS.get(order.status, {}).get(new_status)
    if not required_role or _role(actor) != required_role:
        raise ValueError("You are not allowed to make that order transition.")
    if required_role == "SELLER" and order.seller_id != actor.id:
        raise ValueError("Only the assigned seller can update this order.")
    if required_role == "BUYER" and order.user_id != actor.id:
        raise ValueError("Only the buyer can confirm this order.")
    if required_role == "DELIVERY" and new_status != "ASSIGNED" and order.delivery_person_id != actor.id:
        raise ValueError("Only the assigned delivery person can update this order.")

    if assignee is not None and (new_status != "ASSIGNED" or required_role != "SELLER"):
        raise ValueError("A delivery person can only be chosen when marking an order ready for delivery.")

    if new_status == "ASSIGNED":
        if order.delivery_person_id and order.delivery_person_id != actor.id:
            raise ValueError("This delivery is already assigned.")
        if assignee is not None:
            if _role(assignee) != "DELIVERY":
                raise ValueError("That account isn't a delivery rider.")
            order.delivery_person = assignee
        else:
            order.delivery_person = actor

    was_direct_assignment = new_status == "ASSIGNED" and order.status == "PREPARING"
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
    if was_direct_assignment and "ready_at" not in update_fields:
        # it skipped the open READY_FOR_DELIVERY stage entirely, but it became
        # ready and assigned in the same moment, so still record when that was
        order.ready_at = timezone.now()
        update_fields.append("ready_at")
    order.save(update_fields=update_fields)

    notification_type, message = NOTIFICATION_DETAILS[new_status]
    assignee_message = (
        "The seller assigned this delivery to you directly. Please prepare to pick it up."
        if assignee is not None else None
    )
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
        recipient_message = assignee_message if (assignee is not None and recipient.id == assignee.id) else message
        _notify(recipient, order, notification_type, recipient_message)
    send_status_update_notifications(order, new_status, message, actor)
    if assignee is not None:
        transaction.on_commit(
            lambda: send_status_update_to_recipient(assignee, order, new_status, assignee_message)
        )
        send_actor_confirmation(order, new_status, actor, message=f"You assigned this delivery to {assignee.username}.")
    else:
        send_actor_confirmation(order, new_status, actor)
    return order


def notify_order_placed(order):
    """The very first notification of an order's life: fired the moment
    checkout completes ("the product has been checked out"). The buyer gets
    an in-app + email/WhatsApp confirmation (their receipt); the seller gets
    an in-app + email/WhatsApp alert that a sale is waiting for them; and --
    if ADMIN_NOTIFY_ALL_ORDER_EVENTS is on (the default) -- every admin gets
    the same, so the owner can track it start to finish."""
    if order.seller:
        _notify(order.seller, order, Notification.Type.ORDER_PLACED, "A new order is waiting for your review.")
    admins = _admin_users(exclude_id=order.user_id) if _admin_notify_enabled() else []
    for admin_user in admins:
        _notify(admin_user, order, Notification.Type.ORDER_PLACED, f"New order {order.order_number} was placed.")
    transaction.on_commit(lambda: send_order_confirmation_notification(order))
    if order.seller_id:
        transaction.on_commit(lambda: send_seller_new_order_notification(order))
    for admin_user in admins:
        transaction.on_commit(
            lambda admin_user=admin_user: send_status_update_to_recipient(admin_user, order, "PLACED", "New order placed.")
        )
