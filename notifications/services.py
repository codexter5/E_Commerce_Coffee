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


def _send_channels(order, subject, body):
    channels = _channels()

    if "email" in channels and order.email:
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [order.email], fail_silently=False)
        except Exception:
            logger.exception("Email notification failed for order %s", order.order_number)

    if "whatsapp" in channels:
        _send_whatsapp(order.phone, body)


def send_order_status_notification(order, status, message):
    _send_channels(order, f"Order {order.order_number}: {status.title()}", message)


def send_order_confirmation_notification(order):
    body = (
        f"Your order {order.order_number} has been confirmed. "
        f"Total: {order.total_amount}. We will update you when its status changes."
    )
    _send_channels(order, f"Order confirmation: {order.order_number}", body)