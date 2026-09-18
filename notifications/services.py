import base64
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone


logger = logging.getLogger(__name__)


def _channels():
    return {
        channel.strip().lower()
        for channel in getattr(settings, "ORDER_NOTIFICATION_CHANNELS", "").split(",")
        if channel.strip()
    }


def _normalize_phone(phone):
    """WhatsApp/Twilio requires E.164 (e.g. +9779812345678). Most people just
    type a local 10-digit number at checkout or in their profile, so prefix
    the configured default country code when one isn't already present."""
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if not phone:
        return ""
    if phone.startswith("+"):
        return phone
    if phone.startswith("00"):
        return "+" + phone[2:]
    default_cc = getattr(settings, "DEFAULT_PHONE_COUNTRY_CODE", "")
    return f"{default_cc}{phone}" if default_cc else phone


def _twilio_from():
    """Twilio requires the sender number itself to be prefixed 'whatsapp:'
    (e.g. 'whatsapp:+14155238886'). It's an easy detail to miss when typing
    TWILIO_WHATSAPP_FROM into .env, so add it automatically if missing."""
    sender = getattr(settings, "TWILIO_WHATSAPP_FROM", "").strip()
    if sender and not sender.startswith("whatsapp:"):
        sender = f"whatsapp:{sender}"
    return sender


def _send_whatsapp_via_twilio(phone, message):
    """Does the actual Twilio call and returns (success, detail)."""
    sid = getattr(settings, "TWILIO_ACCOUNT_SID", "").strip()
    token = getattr(settings, "TWILIO_AUTH_TOKEN", "").strip()
    sender = _twilio_from()
    normalized = _normalize_phone(phone)

    if not sid or not token:
        return False, "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN are not set in .env."
    if not sender:
        return False, "TWILIO_WHATSAPP_FROM is not set in .env."
    if not normalized:
        return False, "No phone number was given."

    data = urlencode({"From": sender, "To": f"whatsapp:{normalized}", "Body": message}).encode()
    credentials = base64.b64encode(f"{sid}:{token}".encode()).decode()
    request = Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        data=data,
        headers={"Authorization": f"Basic {credentials}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return True, f"Sent to {normalized} (Twilio HTTP {response.status})."
    except HTTPError as error:
        detail = error.read().decode(errors="replace")[:400]
        return False, f"Twilio rejected the request (HTTP {error.code}): {detail}"
    except (URLError, TimeoutError) as error:
        return False, f"Could not reach Twilio: {error}"


def _meta_api_url():
    version = (getattr(settings, "META_WHATSAPP_API_VERSION", "") or "v20.0").strip()
    phone_number_id = getattr(settings, "META_WHATSAPP_PHONE_NUMBER_ID", "").strip()
    return f"https://graph.facebook.com/{version}/{phone_number_id}/messages"


def _send_whatsapp_via_meta(phone, message):
    """Sends via Meta's own WhatsApp Cloud API directly -- no Twilio, no
    third-party middleman, and no per-message cost on the free tier. Returns
    (success, detail) the same way the Twilio path does."""
    token = getattr(settings, "META_WHATSAPP_TOKEN", "").strip()
    phone_number_id = getattr(settings, "META_WHATSAPP_PHONE_NUMBER_ID", "").strip()
    normalized = _normalize_phone(phone)

    if not token:
        return False, "META_WHATSAPP_TOKEN is not set in .env."
    if not phone_number_id:
        return False, "META_WHATSAPP_PHONE_NUMBER_ID is not set in .env."
    if not normalized:
        return False, "No phone number was given."

    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": normalized.lstrip("+"),
        "type": "text",
        "text": {"body": message},
    }).encode()
    request = Request(
        _meta_api_url(),
        data=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return True, f"Sent to {normalized} (Meta HTTP {response.status})."
    except HTTPError as error:
        detail = error.read().decode(errors="replace")[:400]
        return False, f"Meta rejected the request (HTTP {error.code}): {detail}"
    except (URLError, TimeoutError) as error:
        return False, f"Could not reach Meta: {error}"


def _send_whatsapp_verbose(phone, message):
    """Routes to whichever provider WHATSAPP_PROVIDER selects ("twilio" or
    "meta"), returning (success, detail) either way -- used by the
    notification test tool so a real person can see exactly why a message
    did or didn't go through, without needing server log access."""
    provider = getattr(settings, "WHATSAPP_PROVIDER", "twilio").strip().lower()
    if provider == "meta":
        return _send_whatsapp_via_meta(phone, message)
    return _send_whatsapp_via_twilio(phone, message)


def _send_whatsapp(phone, message):
    success, detail = _send_whatsapp_verbose(phone, message)
    if not success:
        logger.warning("WhatsApp notification failed: %s", detail)


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


def _order_summary(order):
    """A few extra lines of receipt-style detail appended to every message so
    whoever reads it (buyer, seller, delivery rider, admin) has the full
    picture in writing -- proof of exactly what the order was and where it
    stands, without needing to open the dashboard to check.

    Order ID and timestamp go in the body (not just the email subject) since
    WhatsApp messages have no subject line at all -- without this, a WhatsApp
    notification would never actually say which order it's about. Place
    (the delivery address) matters most for delivery riders deciding whether
    a job is even feasible for them before they claim it, but it's included
    for everyone for the same "proof in writing" reason as the rest.
    """
    lines = [
        f"Order: {order.order_number}",
        f"When: {timezone.now().strftime('%b %d, %Y %I:%M %p')}",
        f"Buyer: {order.full_name} ({order.email}, {order.phone})",
        f"Place: {order.shipping_address}, {order.city} {order.postal_code}",
        f"Total: Rs. {order.total_amount} -- {order.get_payment_method_display()}"
        f"{' (paid)' if order.is_paid else ' (due on delivery)'}",
    ]
    if order.seller_id:
        lines.append(f"Seller: {order.seller.username}")
    if order.delivery_person_id:
        lines.append(f"Delivery: {order.delivery_person.username}")
    items = list(order.items.all()[:10])
    if items:
        lines.append("Items: " + ", ".join(f"{item.product_name} x{item.quantity}" for item in items))
    return "\n".join(lines)


def send_order_confirmation_notification(order):
    """Buyer-facing: sent the moment checkout completes. Doubles as their
    receipt -- exact items, total, and payment method in writing."""
    body = (
        f"Your order {order.order_number} has been confirmed. "
        f"We'll message you again as its status changes.\n\n{_order_summary(order)}"
    )
    notify_recipient(order.user, order, f"Order confirmation: {order.order_number}", body)


def send_seller_new_order_notification(order):
    """Seller-facing: sent the moment a buyer checks out with one of their products."""
    if not order.seller_id:
        return
    body = (
        f"New order {order.order_number} is waiting for your review. "
        f"Log in to your seller dashboard to accept it.\n\n{_order_summary(order)}"
    )
    notify_recipient(order.seller, order, f"New order received: {order.order_number}", body)


def send_status_update_to_recipient(recipient, order, new_status, message):
    """Used for every order-lifecycle step (accepted, preparing, ready,
    assigned, picked up, out for delivery, delivered, completed, cancelled).
    Every recipient -- buyer, seller, delivery rider, or admin -- gets the
    same receipt-style detail, not just a one-line status word, so the
    message itself is proof of what happened and to which order."""
    subject = f"Order {order.order_number}: {new_status.replace('_', ' ').title()}"
    body = f"{message}\n\n{_order_summary(order)}"
    notify_recipient(recipient, order, subject, body)


def notification_config_status():
    """A plain-language readout of the current notification configuration,
    for the admin dashboard's Notifications page -- so you can see at a
    glance what's actually turned on, without digging through .env or
    server logs. Never returns secret values, only whether they're set."""
    channels = _channels()
    email_backend = getattr(settings, "EMAIL_BACKEND", "")
    is_console_backend = email_backend.endswith("console.EmailBackend")
    provider = getattr(settings, "WHATSAPP_PROVIDER", "twilio").strip().lower()
    return {
        "channels": sorted(channels) or None,
        "email": {
            "enabled": "email" in channels,
            "backend": email_backend,
            "is_console_backend": is_console_backend,
            "host": getattr(settings, "EMAIL_HOST", ""),
            "from_address": getattr(settings, "DEFAULT_FROM_EMAIL", ""),
            "host_user_set": bool(getattr(settings, "EMAIL_HOST_USER", "")),
            "host_password_set": bool(getattr(settings, "EMAIL_HOST_PASSWORD", "")),
        },
        "whatsapp": {
            "enabled": "whatsapp" in channels,
            "provider": provider,
            # Twilio
            "sid_set": bool(getattr(settings, "TWILIO_ACCOUNT_SID", "")),
            "token_set": bool(getattr(settings, "TWILIO_AUTH_TOKEN", "")),
            "from_set": bool(getattr(settings, "TWILIO_WHATSAPP_FROM", "")),
            "from_number": _twilio_from(),
            # Meta
            "meta_token_set": bool(getattr(settings, "META_WHATSAPP_TOKEN", "")),
            "meta_phone_number_id_set": bool(getattr(settings, "META_WHATSAPP_PHONE_NUMBER_ID", "")),
            "meta_api_version": getattr(settings, "META_WHATSAPP_API_VERSION", ""),
            "default_country_code": getattr(settings, "DEFAULT_PHONE_COUNTRY_CODE", ""),
        },
        "admin_notify_all_stages": getattr(settings, "ADMIN_NOTIFY_ALL_ORDER_EVENTS", True),
    }


def send_test_notification(email=None, phone=None, message=None):
    """Sends a real test message right now and reports exactly what happened
    per channel, instead of silently logging it -- this is what the admin
    dashboard's 'Send test notification' button calls. Returns a dict like
    {"email": "sent to ...", "whatsapp": "FAILED: ..."} so the person testing
    it can see the actual reason without needing server log access."""
    message = message or "This is a test notification from your BrewMart store."
    channels = _channels()
    results = {}

    if not channels:
        results["error"] = (
            "No channels are enabled. Set ORDER_NOTIFICATION_CHANNELS=email,whatsapp "
            "(or just one of them) in .env and restart the server."
        )
        return results

    if "email" in channels:
        if not email:
            results["email"] = "Skipped -- no email address given."
        else:
            try:
                send_mail(
                    "BrewMart test notification", message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False,
                )
                results["email"] = f"Sent to {email}."
            except Exception as error:
                results["email"] = f"FAILED: {error}"

    if "whatsapp" in channels:
        if not phone:
            results["whatsapp"] = "Skipped -- no phone number given."
        else:
            success, detail = _send_whatsapp_verbose(phone, message)
            results["whatsapp"] = detail if success else f"FAILED: {detail}"

    return results

