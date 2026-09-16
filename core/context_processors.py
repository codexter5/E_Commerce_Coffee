from django.conf import settings


def analytics(request):
    """Makes GOOGLE_ANALYTICS_ID available to base.html so the gtag.js snippet
    only renders when a real measurement ID has been configured -- nothing
    fires (and no broken/fake tracking code ships) until it's set."""
    return {"GOOGLE_ANALYTICS_ID": getattr(settings, "GOOGLE_ANALYTICS_ID", "")}
