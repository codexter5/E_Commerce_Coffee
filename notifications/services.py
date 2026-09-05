import base64
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import send_mail


logger = logging.getLogger(__name__)


def _channels():
    return {
        channel.strip().lower()
        for channel in getattr(settings, "ORDER_NOTIFICATION_CHANNELS", "").split(",")
        if channel.strip()
    }


def _send_whatsapp(phone, message):
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "")
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "")
    sender = getattr(settings, "TWILIO_WHATSAPP_FROM", "")
    if not all((sid, token, sender, phone)):
        logger.warning("WhatsApp notification skipped: Twilio settings or recipient phone is missing.")
        return

    data = urlencode({"From": sender, "To": f"whatsapp:{phone}", "Body": message}).encode()
    credentials = base64.b64encode(f"{sid}:{token}".encode()).decode()
    request = Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=data,
        headers={"Authorization": f"Basic {credentials}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10):
            return
    except (HTTPError, URLError, TimeoutError) as error:
        logger.exception("WhatsApp notification failed: %s", error)


def _contact_for(recipient, order):
    """Work out which email/phone to use for a given recipient.

    For the buyer, we prefer the contact details they typed into the checkout
    form for *this specific order* (order.email / order.phone) over their
    account email, since that's the number/address they told us to reach them
    on for this delivery. For every other recipient (seller, delivery rider,
    admin) there's no per-order override, so we use their account email and
    the phone number on their profile.
    """
    if order and order.user_id and recipient.id == order.user_id:
        return order.email or recipient.email, order.phone
    phone = getattr(getattr(recipient, "profile", None), "phone", "")
    return recipient.email, phone


def notify_recipient(recipient, order, subject, body):
    """Send subject/body to one recipient over every enabled channel
    (email and/or WhatsApp, per ORDER_NOTIFICATION_CHANNELS), using
    whichever contact details are appropriate for that recipient/order pair.
    Safe to call even if the recipient has no email or no phone on file --
    each channel is skipped individually rather than raising.
    """
    channels = _channels()
    if not channels or recipient is None:
        return
    email, phone = _contact_for(recipient, order)

    if "email" in channels and email:
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
        except Exception:
            logger.exception(
                "Email notification failed for order %s -> %s",
                order.order_number if order else "-", recipient,
            )

    if "whatsapp" in channels and phone:
        _send_whatsapp(phone, body)


def send_order_confirmation_notification(order):
    """Buyer-facing: sent the moment checkout completes."""
    body = (
        f"Your order {order.order_number} has been confirmed. "
        f"Total: Rs. {order.total_amount}. We'll message you again as its status changes."
    )
    notify_recipient(order.user, order, f"Order confirmation: {order.order_number}", body)


def send_seller_new_order_notification(order):
    """Seller-facing: sent the moment a buyer checks out with one of their products."""
    if not order.seller_id:
        return
    body = (
        f"New order {order.order_number} for Rs. {order.total_amount} is waiting for your review. "
        f"Log in to your seller dashboard to accept it."
    )
    notify_recipient(order.seller, order, f"New order received: {order.order_number}", body)


def send_status_update_to_recipient(recipient, order, new_status, message):
    """Used for every order-lifecycle step (accepted, preparing, ready,
    assigned, picked up, out for delivery, delivered, completed, cancelled) --
    whoever needs to know gets routed here individually."""
    subject = f"Order {order.order_number}: {new_status.replace('_', ' ').title()}"
    notify_recipient(recipient, order, subject, message)
