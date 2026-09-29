from django.conf import settings


def site_settings(request):
    """Makes a few optional site-wide settings available to every template:
    GOOGLE_ANALYTICS_ID and FACEBOOK_PIXEL_ID (their tracking snippets only
    render once a real ID is configured), GOOGLE_ADSENSE_CLIENT_ID (AdSense
    script/ad slots only render once configured), and STORE_WHATSAPP_NUMBER
    (the floating "Chat with us" button only renders once a real number is
    configured)."""
    return {
        "GOOGLE_ANALYTICS_ID": getattr(settings, "GOOGLE_ANALYTICS_ID", ""),
        "FACEBOOK_PIXEL_ID": getattr(settings, "FACEBOOK_PIXEL_ID", ""),
        "GOOGLE_ADSENSE_CLIENT_ID": getattr(settings, "GOOGLE_ADSENSE_CLIENT_ID", ""),
        "STORE_WHATSAPP_NUMBER": getattr(settings, "STORE_WHATSAPP_NUMBER", ""),
    }


def pending_ecommerce_event(request):
    """Some conversion events (add-to-cart today) happen on a plain
    POST-redirect-GET flow rather than an AJAX call, so there's no single
    page load where "the click just happened" in JS. To still fire a GA4/
    Meta Pixel event for those, the view that handles the POST stashes a
    small JSON-able dict describing the event in the session; this pops it
    (so it only ever fires once) and hands it to base.html, which renders it
    via json_script for static/js/analytics.js to pick up and send."""
    event = None
    if hasattr(request, "session"):
        event = request.session.pop("ecommerce_event", None)
    return {"ecommerce_event": event}
