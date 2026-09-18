from urllib.parse import quote

from django import template
from django.conf import settings

register = template.Library()


def _normalize_for_whatsapp(phone):
    """wa.me links need digits only (no '+', spaces, or dashes). Local
    numbers get the default country code prefixed first, same convention as
    notifications.services._normalize_phone uses for Twilio."""
    phone = (phone or "").strip().replace(" ", "").replace("-", "")
    if not phone:
        return ""
    if phone.startswith("00"):
        phone = "+" + phone[2:]
    if not phone.startswith("+"):
        default_cc = getattr(settings, "DEFAULT_PHONE_COUNTRY_CODE", "")
        phone = f"{default_cc}{phone}" if default_cc else phone
    return "".join(ch for ch in phone if ch.isdigit())


@register.simple_tag
def whatsapp_link(phone, message=""):
    """{% whatsapp_link phone message %} -> a wa.me link, or "" if there's no
    usable phone number (callers should check truthiness before rendering
    a button, so a missing number just quietly hides the button)."""
    digits = _normalize_for_whatsapp(phone)
    if not digits:
        return ""
    query = f"?text={quote(message)}" if message else ""
    return f"https://wa.me/{digits}{query}"
