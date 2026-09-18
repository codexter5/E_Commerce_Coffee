from django.conf import settings


def site_settings(request):
    """Makes a few optional site-wide settings available to every template:
    GOOGLE_ANALYTICS_ID (gtag.js only renders once a real measurement ID is
    configured) and STORE_WHATSAPP_NUMBER (the floating "Chat with us" button
    only renders once a real number is configured)."""
    return {
        "GOOGLE_ANALYTICS_ID": getattr(settings, "GOOGLE_ANALYTICS_ID", ""),
        "STORE_WHATSAPP_NUMBER": getattr(settings, "STORE_WHATSAPP_NUMBER", ""),
    }
